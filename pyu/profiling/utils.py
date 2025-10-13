"""
Profiling utility functions.

@author: Jakub Walczak
@organization: HappyRavenLabs
"""

from __future__ import annotations

import csv
import inspect
import io
import linecache
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

from rich.console import Console
from rich.table import Table


def compute_statistics(data: List[float]) -> Dict[str, float]:
    """Compute basic statistics for a list of numbers.

    Returns a dictionary with mean, median, stdev, iqr,
    min, max, count, and sum.
    """
    sorted_data = sorted(data)
    if not data:
        return {}
    mean = sum(data) / len(data)
    return {
        "mean": mean,
        "median": sorted_data[len(sorted_data) // 2],
        "stdev": (
            (
                sum((x - mean) ** 2 for x in sorted_data)
                / (len(sorted_data) - 1)
            )
            ** 0.5
            if len(data) > 1
            else 0.0
        ),
        "iqr": sorted_data[int(0.75 * len(sorted_data))]
        - sorted_data[int(0.25 * len(sorted_data))],
        "min": min(data),
        "max": max(data),
        "count": len(data),
        "sum": sum(data),
    }


def _select_output(out: Any) -> Any:
    if out is None:
        out = sys.stderr
    elif isinstance(out, (str, Path)):
        path = Path(out)
        if path.exists():
            raise UserWarning(
                f"Output file {out} already exists. It will be overwritten."
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        out = open(out, "w")
    return out


def get_named_arguments(
    func: Callable,
    arguments: Optional[Tuple] = None,
    kwargs: Optional[Dict] = None,
) -> Dict:
    if arguments is None:
        arguments = ()
    if kwargs is None:
        kwargs = {}
    sig = inspect.signature(func)
    bound = sig.bind(*arguments, **kwargs)
    bound.apply_defaults()
    return dict(bound.arguments)


def _is_csv_output(output: Any) -> bool:
    """Check if output is a CSV file path."""
    if isinstance(output, (str, Path, os.PathLike)):
        path = Path(output)
        return path.suffix.lower() == ".csv"
    return False


class Format(Enum):
    CSV = "csv"
    STDIO = "stdio"
    TXT = "txt"

    @classmethod
    def _missing_(cls, key):
        return cls.TXT


class TimeWriter:
    _format: Format
    _target: Union[io.TextIOWrapper, Path]
    _func: Optional[Callable] = None
    _bind_args: Optional[dict] = None

    def __init__(
        self,
        out: Optional[Union[io.TextIOWrapper, str, Path, os.PathLike]] = None,
    ):
        if out is None:
            out = sys.stderr
        if isinstance(out, io.TextIOWrapper):
            self._format = Format.STDIO
        elif isinstance(out, (str, Path, os.PathLike)):
            out = Path(out)
            out.parent.mkdir(exist_ok=True, parents=True)
            if "csv" in out.suffix.lower():
                self._format = Format.CSV
            else:
                self._format = Format.TXT
                out = open(out, "w")
        else:
            raise TypeError(
                "`out` argument is expected to be one of "
                "[io.TextIOWrapper, str, Path, os.PathLike] "
                f"but found: {type(out)}"
            )
        self._target = out

    def with_func(
        self, func: Callable, *arguments, **kwarguments
    ) -> "TimeWriter":
        self._func = func
        self._bind_args = get_named_arguments(func, arguments, kwarguments)
        return self

    @property
    def _title(self) -> str:
        title = "Timing report"
        if self._func:
            kwargs = [
                f"{key}={value}" for key, value in self._bind_args.items()
            ]
            title += f" for function {self._func.__name__}({','.join(kwargs)})"

        return title

    def write(
        self,
        values: Union[List[float], Dict[int, List[float]]],
        *,
        root_file: Optional[Union[str, os.PathLike, Path]] = None,
    ):
        if isinstance(values, dict):
            if root_file is None:
                raise ValueError(
                    "For line-based report, `root_file` argument must ba "
                    "passed"
                )
            if self._format is Format.CSV:
                self._write_lines_to_csv(values, root_file)
            elif self._format is Format.STDIO:
                self._write_lines_to_stdio(values, root_file)
            else:
                self._write_lines_to_txt(values, root_file)
        elif isinstance(values, Iterable):
            if self._format is Format.CSV:
                self._write_to_csv(values)
            elif self._format is Format.STDIO:
                self._write_to_stdio(values)
            else:
                self._write_to_txt(values)

    def _write_to_csv(self, times: List[float]):
        headers = ["Metric", "Value"]
        stats = compute_statistics(times)
        with open(self._target, "w", encoding="utf-8") as file:
            file.write(f"{self._title}\n\n")
            _writer = csv.DictWriter(file, fieldnames=headers)
            _writer.writeheader()
            _writer.writerows(
                [
                    {"Metric": "Total elapsed time", "Value": sum(times)},
                    {"Metric": "Number of runs", "Value": len(times)},
                    {"Metric": "Average time", "Value": stats["mean"]},
                    {"Metric": "Standard deviation", "Value": stats["stdev"]},
                    {"Metric": "Median time", "Value": stats["median"]},
                    {
                        "Metric": "Interquartile range (IQR)",
                        "Value": stats["iqr"],
                    },
                    {"Metric": "Minimum time", "Value": stats["min"]},
                    {"Metric": "Maximum time", "Value": stats["max"]},
                ]
            )

    def _write_to_stdio(self, times: List[float]):
        console = Console(file=self._target)
        if not times or len(times) == 0:
            console.log("[bold yellow]No timing data available.[/bold yellow]")
        elif len(times) == 1:
            console.log(
                "[bold green]Elapsed time:[/bold green] "
                f"{sum(times):.6f} seconds"
            )
        else:
            stats = compute_statistics(times)
            table = Table(title=self._title)
            table.add_column("Metric", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            table.add_row(
                "Total elapsed time",
                f"{sum(times):.6f} seconds over {stats['count']} runs",
            )
            table.add_row(
                "Average time per run", f"{stats['mean']:.6f} seconds"
            )
            table.add_row(
                "Standard deviation", f"{stats['stdev']:.6f} seconds"
            )
            table.add_row("Median time", f"{stats['median']:.6f} seconds")
            table.add_row(
                "Interquartile range (IQR)", f"{stats['iqr']:.6f} seconds"
            )
            table.add_row("Minimum time", f"{stats['min']:.6f} seconds")
            table.add_row("Maximum time", f"{stats['max']:.6f} seconds")
            console.log(table)

    _write_to_txt = _write_to_stdio

    def _write_lines_to_stdio(
        self,
        values: Dict[int, List[float]],
        root_file: Union[str, os.PathLike, Path],
    ):
        console = Console(file=self._target)
        table = Table(title=self._title + f" for code in file '{root_file}'")
        table.add_column("Line No.", style="cyan", no_wrap=True)
        table.add_column("Code", style="green")
        table.add_column("Total Time (s)", style="magenta")
        table.add_column("Avg Time (s)", style="magenta")
        table.add_column("Count", style="yellow")

        _leading_chars_trim: int = 0
        for (filename, line_no), times in sorted(values.items()):
            code_line = linecache.getline(filename, line_no)
            if _leading_chars_trim == 0:
                _leading_chars_trim = len(code_line) - len(code_line.lstrip())
            code_line = code_line.rstrip()[_leading_chars_trim:]
            stats = compute_statistics(times)
            table.add_row(
                str(line_no),
                code_line,
                f"{stats['sum']:.6f}",
                f"{stats['mean']:.6f}",
                str(stats["count"]),
            )

        console.log(table)

    _write_lines_to_txt = _write_lines_to_stdio

    def _write_lines_to_csv(
        self,
        values: Dict[int, List[float]],
        root_file: Union[str, os.PathLike, Path],
    ):
        headers = [
            "Line No.",
            "Code",
            "Total Time (s)",
            "Avg Time (s)",
            "Count",
        ]
        with open(self._target, "w", encoding="utf-8") as file:
            file.write(f"{self._title} for code in file '{root_file}'\n\n")
            _writer = csv.DictWriter(file, fieldnames=headers)
            _writer.writeheader()

            _leading_chars_trim: int = 0
            for (filename, line_no), times in sorted(values.items()):
                stats = compute_statistics(times)
                code_line = linecache.getline(filename, line_no)
                if _leading_chars_trim == 0:
                    _leading_chars_trim = len(code_line) - len(
                        code_line.lstrip()
                    )
                code_line = code_line.rstrip()[_leading_chars_trim:]
                _writer.writerow(
                    {
                        "Line No.": line_no,
                        "Code": code_line,
                        "Total Time (s)": stats["sum"],
                        "Avg Time (s)": stats["mean"],
                        "Count": stats["count"],
                    }
                )


class MemoryWriter:
    _format: Format
    _target: Union[io.TextIOWrapper, Path]
    _func: Optional[Callable] = None
    _bind_args: Optional[dict] = None

    def __init__(
        self,
        out: Optional[Union[io.TextIOWrapper, str, Path, os.PathLike]] = None,
    ):
        if out is None:
            out = sys.stderr
        if isinstance(out, io.TextIOWrapper):
            self._format = Format.STDIO
        elif isinstance(out, (str, Path, os.PathLike)):
            out = Path(out)
            out.parent.mkdir(exist_ok=True, parents=True)
            if "csv" in out.suffix.lower():
                self._format = Format.CSV
            else:
                self._format = Format.TXT
                out = open(out, "w")
        else:
            raise TypeError(
                "`out` argument is expected to be one of "
                "[io.TextIOWrapper, str, Path, os.PathLike] "
                f"but found: {type(out)}"
            )
        self._target = out

    def with_func(
        self, func: Callable, *arguments, **kwarguments
    ) -> "MemoryWriter":
        self._func = func
        self._bind_args = get_named_arguments(func, arguments, kwarguments)
        return self

    @property
    def _title(self) -> str:
        title = "Memory Usage Report"
        if self._func:
            kwargs = [
                f"{key}={value}" for key, value in self._bind_args.items()
            ]
            title += f" for function {self._func.__name__}({','.join(kwargs)})"

        return title

    def write(
        self,
        values: Union[List[float], Dict[int, List[float]]],
        *,
        root_file: Optional[Union[str, os.PathLike, Path]] = None,
    ):
        if isinstance(values, dict):
            if root_file is None:
                raise ValueError(
                    "For line-based report, `root_file` argument must be "
                    "passed"
                )
            if self._format is Format.CSV:
                self._write_lines_to_csv(values, root_file)
            elif self._format is Format.STDIO:
                self._write_lines_to_stdio(values, root_file)
            else:
                self._write_lines_to_txt(values, root_file)
        elif isinstance(values, Iterable):
            if self._format is Format.CSV:
                self._write_to_csv(values)
            elif self._format is Format.STDIO:
                self._write_to_stdio(values)
            else:
                self._write_to_txt(values)

    def _write_to_csv(self, mem_usage: List[float]):
        headers = ["Metric", "Memory Usage (bytes)"]
        stats = compute_statistics(mem_usage)
        with open(self._target, "w", encoding="utf-8") as file:
            file.write(f"{self._title}\n\n")
            _writer = csv.DictWriter(file, fieldnames=headers)
            _writer.writeheader()
            _writer.writerows(
                [
                    {
                        "Metric": "Number of runs",
                        "Memory Usage (bytes)": len(mem_usage),
                    },
                    {
                        "Metric": "Average memory",
                        "Memory Usage (bytes)": stats["mean"],
                    },
                    {
                        "Metric": "Standard deviation",
                        "Memory Usage (bytes)": stats["stdev"],
                    },
                    {
                        "Metric": "Median memory",
                        "Memory Usage (bytes)": stats["median"],
                    },
                    {
                        "Metric": "Interquartile range (IQR)",
                        "Memory Usage (bytes)": stats["iqr"],
                    },
                    {
                        "Metric": "Minimum memory",
                        "Memory Usage (bytes)": stats["min"],
                    },
                    {
                        "Metric": "Maximum memory",
                        "Memory Usage (bytes)": stats["max"],
                    },
                ]
            )

    def _write_to_stdio(self, mem_usage: List[float]):
        console = Console(file=self._target)
        if not mem_usage or len(mem_usage) == 0:
            console.log(
                "[bold yellow]No memory usage data available.[/bold yellow]"
            )
        elif len(mem_usage) == 1:
            console.log(
                "[bold green]Total Memory Used:[/bold green] "
                f" {get_mem_unit(mem_usage[0])}"
            )
        else:
            stats = compute_statistics(mem_usage)
            table = Table(title=self._title)
            table.add_column("Metric", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            table.add_row(
                "Total memory used",
                f"{get_mem_unit(sum(mem_usage))} over {stats['count']} runs",
            )
            table.add_row(
                "Average memory per run", f"{get_mem_unit(stats['mean'])}"
            )
            table.add_row(
                "Standard deviation", f"{get_mem_unit(stats['stdev'])}"
            )
            table.add_row("Median memory", f"{get_mem_unit(stats['median'])}")
            table.add_row(
                "Interquartile range (IQR)", f"{get_mem_unit(stats['iqr'])}"
            )
            table.add_row("Minimum memory", f"{get_mem_unit(stats['min'])}")
            table.add_row("Maximum memory", f"{get_mem_unit(stats['max'])}")
            console.log(table)

    _write_to_txt = _write_to_stdio

    def _write_lines_to_stdio(
        self,
        values: Dict[int, List[float]],
        root_file: Union[str, os.PathLike, Path],
    ):
        console = Console(file=self._target)
        table = Table(title=self._title + f" for code in file '{root_file}'")
        table.add_column("Line No.", style="cyan", no_wrap=True)
        table.add_column("Code", style="green")
        table.add_column("Total Memory", style="magenta")
        table.add_column("Avg Memory", style="magenta")
        table.add_column("Count", style="yellow")

        _leading_chars_trim: int = 0
        for (filename, line_no), mem_usage in sorted(values.items()):
            code_line = linecache.getline(filename, line_no)
            if _leading_chars_trim == 0:
                _leading_chars_trim = len(code_line) - len(code_line.lstrip())
            code_line = code_line.rstrip()[_leading_chars_trim:]
            stats = compute_statistics(mem_usage)
            table.add_row(
                str(line_no),
                code_line,
                get_mem_unit(stats["sum"]),
                get_mem_unit(stats["mean"]),
                str(stats["count"]),
            )

        console.log(table)

    _write_lines_to_txt = _write_lines_to_stdio

    def _write_lines_to_csv(
        self,
        values: Dict[int, List[float]],
        root_file: Union[str, os.PathLike, Path],
    ):
        headers = [
            "Line No.",
            "Code",
            "Total memory (bytes)",
            "Avg Memory (bytes)",
            "Count",
        ]
        with open(self._target, "w", encoding="utf-8") as file:
            file.write(f"{self._title} for code in file '{root_file}'\n\n")
            _writer = csv.DictWriter(file, fieldnames=headers)
            _writer.writeheader()

            _leading_chars_trim: int = 0
            for (filename, line_no), times in sorted(values.items()):
                stats = compute_statistics(times)
                code_line = linecache.getline(filename, line_no)
                if _leading_chars_trim == 0:
                    _leading_chars_trim = len(code_line) - len(
                        code_line.lstrip()
                    )
                code_line = code_line.rstrip()[_leading_chars_trim:]
                _writer.writerow(
                    {
                        "Line No.": line_no,
                        "Code": code_line,
                        "Total Memory (bytes)": stats["sum"],
                        "Avg Memory (bytes)": stats["mean"],
                        "Count": stats["count"],
                    }
                )


def get_mem_unit(mem_bytes: float) -> float:
    unit = "bytes"
    conv = mem_bytes
    if conv > 2048:
        conv = mem_bytes / 1024
        unit = "kB"
    if conv > 2048:
        conv = conv / 1024
        unit = "MB"
    if conv > 2048:
        conv = conv / 1024
        unit = "GB"
    return f"{conv:.2f} {unit}"
