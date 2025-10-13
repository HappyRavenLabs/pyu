"""
This module provides a robust, extensible system for writing profiling data
to various output formats (console, CSV, text files) with proper error handling
and resource management.

@author: Jakub Walczak
@organization: HappyRavenLabs
"""

from __future__ import annotations

import csv
import inspect
import io
import linecache
import sys
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Tuple,
    Type,
    Union,
)

from rich.console import Console
from rich.table import Table

from .exceptions import DataValidationError, InvalidOutputError

# #######################
# Configuration and Enums
# #######################


class OutputFormat(Enum):
    """Supported output formats"""

    CONSOLE = "console"
    CSV = "csv"
    TXT = "txt"


@dataclass
class ReportConfig:
    """Configuration for report generation"""

    precision: int = 6
    show_statistics: List[str] = field(
        default_factory=lambda: [
            "mean",
            "median",
            "stdev",
            "min",
            "max",
            "count",
            "sum",
        ]
    )
    memory_units: str = "auto"  # 'bytes', 'kb', 'mb', 'gb', 'auto'
    time_units: str = "seconds"  # 'seconds', 'milliseconds', 'microseconds'


# ########################
# Protocols and Utilities
# ########################


class MetricData(Protocol):
    """Protocol for different types of measurement data"""

    def get_values(self) -> Union[List[float], Dict[Any, List[float]]]:
        """Get the measurement values"""
        ...

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the measurements"""
        ...


def validate_measurement_data(
    data: Union[List[float], Dict[Any, List[float]]],
) -> None:
    """Validate measurement data before processing"""
    if isinstance(data, list):
        if not data:
            return
        if not all(isinstance(x, (int, float)) and x >= 0 for x in data):
            raise DataValidationError(
                "All measurements must be non-negative numbers"
            )
    elif isinstance(data, dict):
        for key, values in data.items():
            if not isinstance(values, list):
                raise DataValidationError(
                    f"Invalid measurement data type for key {key}"
                )
            if values:
                validate_measurement_data(values)
    else:
        raise DataValidationError(
            "Data must be either List[float] or "
            f"Dict[Any, List[float]], but found {type(data)}"
        )


def compute_statistics(data: List[float]) -> Dict[str, float]:
    """Compute basic statistics for a list of numbers."""
    if not data:
        return {}

    sorted_data = sorted(data)
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
        "iqr": (
            sorted_data[int(0.75 * len(sorted_data))]
            - sorted_data[int(0.25 * len(sorted_data))]
            if len(sorted_data) > 1
            else 0.0
        ),
        "min": min(data),
        "max": max(data),
        "count": len(data),
        "sum": sum(data),
    }


def get_named_arguments(
    func: Callable,
    arguments: Optional[Tuple] = None,
    kwargs: Optional[Dict] = None,
) -> Dict:
    """Get named arguments from function signature"""
    if arguments is None:
        arguments = ()
    if kwargs is None:
        kwargs = {}

    sig = inspect.signature(func)
    bound = sig.bind(*arguments, **kwargs)
    bound.apply_defaults()
    return dict(bound.arguments)


def format_memory_unit(mem_bytes: float) -> str:
    """Format memory bytes into appropriate unit"""
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


# ########################
# Output Target Management
# ########################


class OutputTarget:
    """Handles output destination and format detection"""

    def __init__(self, target: Union[io.TextIOWrapper, str, Path, None]):
        self.target, self.format = self._resolve_target_and_format(target)
        self._should_close = False
        self._file_handle = None

    def _resolve_target_and_format(
        self, target
    ) -> Tuple[Union[io.TextIOWrapper, Path], OutputFormat]:
        """Resolve target and determine output format"""
        if target is None:
            return sys.stderr, OutputFormat.CONSOLE
        elif isinstance(target, io.TextIOWrapper):
            return target, OutputFormat.CONSOLE
        elif isinstance(target, (str, Path)):
            path = Path(target)
            path.parent.mkdir(exist_ok=True, parents=True)

            if path.suffix.lower() == ".csv":
                return path, OutputFormat.CSV
            else:
                return path, OutputFormat.TXT
        else:
            raise InvalidOutputError(
                f"Unsupported output target type: {type(target)}"
            )

    @contextmanager
    def get_writer(self):
        """Get a writer for the output target"""
        if self.format == OutputFormat.CSV:
            yield self.target
        elif isinstance(self.target, Path):
            with self.target.open("w") as f:
                yield f
        else:
            yield self.target


# #####################
# Abstract Base Classes
# #####################


class BaseFormatter(ABC):
    """Abstract base for all formatters"""

    def __init__(self, config: ReportConfig = None):
        self.config = config or ReportConfig()

    @abstractmethod
    def format_simple_metrics(self, data: List[float], title: str) -> str:
        """Format simple list of measurements"""
        pass

    @abstractmethod
    def format_line_metrics(
        self,
        data: Dict[Tuple[str, int], List[float]],
        title: str,
        root_file: str,
    ) -> str:
        """Format line-by-line measurements"""
        pass


class BaseProfileWriter(ABC):
    """Abstract base class for all profile writers"""

    def __init__(
        self,
        output_target: Union[io.TextIOWrapper, str, Path, None] = None,
        config: ReportConfig = None,
    ):
        self._output = OutputTarget(output_target)
        self._config = config or ReportConfig()
        self._func: Optional[Callable] = None
        self._func_args: Dict[str, Any] = {}
        self._formatters = self._create_formatters()

    @abstractmethod
    def _create_formatters(self) -> Dict[OutputFormat, BaseFormatter]:
        """Create formatters for different output formats"""
        pass

    @abstractmethod
    def _get_metric_name(self) -> str:
        """Get the name of the metric (e.g., 'Time', 'Memory')"""
        pass

    def with_func(
        self, func: Callable, *arguments, **kwarguments
    ) -> "BaseProfileWriter":
        """Bind function context for reporting"""
        self._func = func
        self._func_args = get_named_arguments(func, arguments, kwarguments)
        return self

    def write(
        self,
        values: Union[List[float], Dict[Tuple[str, int], List[float]]],
        **kwargs,
    ) -> None:
        """Write profiling data using appropriate formatter"""
        validate_measurement_data(values)

        formatter = self._formatters[self._output.format]
        title = self._generate_title()

        if isinstance(values, dict):
            if "root_file" not in kwargs:
                raise ValueError(
                    "Line-based reports require 'root_file' parameter"
                )
            content = formatter.format_line_metrics(
                values, title, kwargs["root_file"]
            )
        else:
            content = formatter.format_simple_metrics(values, title)

        with self._output.get_writer() as writer:
            if self._output.format == OutputFormat.CSV:
                with open(writer, "w", encoding="utf-8") as f:
                    f.write(content)
            else:
                writer.write(content)

    def _generate_title(self) -> str:
        """Generate report title with function context"""
        base_title = f"{self._get_metric_name()} Report"
        if self._func:
            args_str = ", ".join(
                f"{k}={v}" for k, v in self._func_args.items()
            )
            base_title += f" for {self._func.__name__}({args_str})"
        return base_title


# ##################
# Console Formatters
# ##################


class ConsoleTimeFormatter(BaseFormatter):
    """Console formatter for timing data"""

    def format_simple_metrics(self, times: List[float], title: str) -> str:
        """Format timing data for console output"""
        console = Console(file=io.StringIO())

        if not times:
            console.log("[bold yellow]No timing data available.[/bold yellow]")
        elif len(times) == 1:
            console.log(
                "[bold green]Elapsed time:[/bold green] "
                f"{times[0]:.{self.config.precision}f} seconds"
            )
        else:
            stats = compute_statistics(times)
            table = Table(title=title)
            table.add_column("Metric", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            table.add_row(
                "Total elapsed time",
                f"{sum(times):.{self.config.precision}f} seconds over "
                f"{stats['count']} runs",
            )
            table.add_row(
                "Average time per run",
                f"{stats['mean']:.{self.config.precision}f} seconds",
            )
            table.add_row(
                "Standard deviation",
                f"{stats['stdev']:.{self.config.precision}f} seconds",
            )
            table.add_row(
                "Median time",
                f"{stats['median']:.{self.config.precision}f} seconds",
            )
            table.add_row(
                "Interquartile range (IQR)",
                f"{stats['iqr']:.{self.config.precision}f} seconds",
            )
            table.add_row(
                "Minimum time",
                f"{stats['min']:.{self.config.precision}f} seconds",
            )
            table.add_row(
                "Maximum time",
                f"{stats['max']:.{self.config.precision}f} seconds",
            )

            console.log(table)

        return console.file.getvalue()

    def format_line_metrics(
        self,
        line_times: Dict[Tuple[str, int], List[float]],
        title: str,
        root_file: str,
    ) -> str:
        """Format line-by-line timing data for console"""
        console = Console(file=io.StringIO())
        table = Table(title=f"{title} for code in file '{root_file}'")
        table.add_column("Line No.", style="cyan", no_wrap=True)
        table.add_column("Code", style="green")
        table.add_column("Total Time (s)", style="magenta")
        table.add_column("Avg Time (s)", style="magenta")
        table.add_column("Count", style="yellow")

        leading_chars_trim = 0
        for (filename, line_no), times in sorted(line_times.items()):
            code_line = linecache.getline(filename, line_no)
            if leading_chars_trim == 0:
                leading_chars_trim = len(code_line) - len(code_line.lstrip())
            code_line = code_line.rstrip()[leading_chars_trim:]
            stats = compute_statistics(times)

            table.add_row(
                str(line_no),
                code_line,
                f"{stats['sum']:.{self.config.precision}f}",
                f"{stats['mean']:.{self.config.precision}f}",
                str(stats["count"]),
            )

        console.log(table)
        return console.file.getvalue()


class ConsoleMemoryFormatter(BaseFormatter):
    """Console formatter for memory data"""

    def format_simple_metrics(
        self, memory_usage: List[float], title: str
    ) -> str:
        """Format memory data for console output"""
        console = Console(file=io.StringIO())

        if not memory_usage:
            console.log(
                "[bold yellow]No memory usage data available.[/bold yellow]"
            )
        elif len(memory_usage) == 1:
            console.log(
                "[bold green]Total Memory Used:[/bold green] "
                f"{format_memory_unit(memory_usage[0])}"
            )
        else:
            stats = compute_statistics(memory_usage)
            table = Table(title=title)
            table.add_column("Metric", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            table.add_row(
                "Average memory per run",
                f"{format_memory_unit(stats['mean'])}",
            )
            table.add_row(
                "Standard deviation", f"{format_memory_unit(stats['stdev'])}"
            )
            table.add_row(
                "Median memory", f"{format_memory_unit(stats['median'])}"
            )
            table.add_row(
                "Interquartile range (IQR)",
                f"{format_memory_unit(stats['iqr'])}",
            )
            table.add_row(
                "Minimum memory", f"{format_memory_unit(stats['min'])}"
            )
            table.add_row(
                "Maximum memory", f"{format_memory_unit(stats['max'])}"
            )

            console.log(table)

        return console.file.getvalue()

    def format_line_metrics(
        self,
        line_memory: Dict[Tuple[str, int], List[float]],
        title: str,
        root_file: str,
    ) -> str:
        """Format line-by-line memory data for console"""
        console = Console(file=io.StringIO())
        table = Table(title=f"{title} for code in file '{root_file}'")
        table.add_column("Line No.", style="cyan", no_wrap=True)
        table.add_column("Code", style="green")
        table.add_column("Avg Memory", style="magenta")
        table.add_column("Count", style="yellow")

        leading_chars_trim = 0
        for (filename, line_no), memory_values in sorted(line_memory.items()):
            code_line = linecache.getline(filename, line_no)
            if leading_chars_trim == 0:
                leading_chars_trim = len(code_line) - len(code_line.lstrip())
            code_line = code_line.rstrip()[leading_chars_trim:]
            stats = compute_statistics(memory_values)

            table.add_row(
                str(line_no),
                code_line,
                format_memory_unit(stats["mean"]),
                str(stats["count"]),
            )

        console.log(table)
        return console.file.getvalue()


# ##############
# CSV Formatters
# ##############


class CSVTimeFormatter(BaseFormatter):
    """CSV formatter for timing data"""

    def format_simple_metrics(self, times: List[float], title: str) -> str:
        """Format timing data as CSV"""
        output = io.StringIO()
        output.write(f"{title}\n\n")

        headers = ["Metric", "Value"]
        stats = compute_statistics(times)

        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(
            [
                {"Metric": "Total elapsed time", "Value": sum(times)},
                {"Metric": "Number of runs", "Value": len(times)},
                {"Metric": "Average time", "Value": stats.get("mean", 0)},
                {
                    "Metric": "Standard deviation",
                    "Value": stats.get("stdev", 0),
                },
                {"Metric": "Median time", "Value": stats.get("median", 0)},
                {
                    "Metric": "Interquartile range (IQR)",
                    "Value": stats.get("iqr", 0),
                },
                {"Metric": "Minimum time", "Value": stats.get("min", 0)},
                {"Metric": "Maximum time", "Value": stats.get("max", 0)},
            ]
        )

        return output.getvalue()

    def format_line_metrics(
        self,
        line_times: Dict[Tuple[str, int], List[float]],
        title: str,
        root_file: str,
    ) -> str:
        """Format line-by-line timing data as CSV"""
        output = io.StringIO()
        output.write(f"{title} for code in file '{root_file}'\n\n")

        headers = [
            "Line No.",
            "Code",
            "Total Time (s)",
            "Avg Time (s)",
            "Count",
        ]
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        leading_chars_trim = 0
        for (filename, line_no), times in sorted(line_times.items()):
            stats = compute_statistics(times)
            code_line = linecache.getline(filename, line_no)
            if leading_chars_trim == 0:
                leading_chars_trim = len(code_line) - len(code_line.lstrip())
            code_line = code_line.rstrip()[leading_chars_trim:]

            writer.writerow(
                {
                    "Line No.": line_no,
                    "Code": code_line,
                    "Total Time (s)": stats["sum"],
                    "Avg Time (s)": stats["mean"],
                    "Count": stats["count"],
                }
            )

        return output.getvalue()


class CSVMemoryFormatter(BaseFormatter):
    """CSV formatter for memory data"""

    def format_simple_metrics(
        self, memory_usage: List[float], title: str
    ) -> str:
        """Format memory data as CSV"""
        output = io.StringIO()
        output.write(f"{title}\n\n")

        headers = ["Metric", "Memory Usage (bytes)"]
        stats = compute_statistics(memory_usage)

        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(
            [
                {
                    "Metric": "Number of runs",
                    "Memory Usage (bytes)": len(memory_usage),
                },
                {
                    "Metric": "Average memory",
                    "Memory Usage (bytes)": stats.get("mean", 0),
                },
                {
                    "Metric": "Standard deviation",
                    "Memory Usage (bytes)": stats.get("stdev", 0),
                },
                {
                    "Metric": "Median memory",
                    "Memory Usage (bytes)": stats.get("median", 0),
                },
                {
                    "Metric": "Interquartile range (IQR)",
                    "Memory Usage (bytes)": stats.get("iqr", 0),
                },
                {
                    "Metric": "Minimum memory",
                    "Memory Usage (bytes)": stats.get("min", 0),
                },
                {
                    "Metric": "Maximum memory",
                    "Memory Usage (bytes)": stats.get("max", 0),
                },
            ]
        )

        return output.getvalue()

    def format_line_metrics(
        self,
        line_memory: Dict[Tuple[str, int], List[float]],
        title: str,
        root_file: str,
    ) -> str:
        """Format line-by-line memory data as CSV"""
        output = io.StringIO()
        output.write(f"{title} for code in file '{root_file}'\n\n")

        headers = [
            "Line No.",
            "Code",
            "Total Memory (bytes)",
            "Avg Memory (bytes)",
            "Count",
        ]
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        leading_chars_trim = 0
        for (filename, line_no), memory_values in sorted(line_memory.items()):
            stats = compute_statistics(memory_values)
            code_line = linecache.getline(filename, line_no)
            if leading_chars_trim == 0:
                leading_chars_trim = len(code_line) - len(code_line.lstrip())
            code_line = code_line.rstrip()[leading_chars_trim:]

            writer.writerow(
                {
                    "Line No.": line_no,
                    "Code": code_line,
                    "Total Memory (bytes)": stats["sum"],
                    "Avg Memory (bytes)": stats["mean"],
                    "Count": stats["count"],
                }
            )

        return output.getvalue()


# ################
# Concrete Writers
# ################


class TimeWriter(BaseProfileWriter):
    """Writer for timing profiling data"""

    def _create_formatters(self) -> Dict[OutputFormat, BaseFormatter]:
        """Create formatters for timing data"""
        return {
            OutputFormat.CONSOLE: ConsoleTimeFormatter(self._config),
            OutputFormat.CSV: CSVTimeFormatter(self._config),
            OutputFormat.TXT: ConsoleTimeFormatter(self._config),
        }

    def _get_metric_name(self) -> str:
        return "Timing"


class MemoryWriter(BaseProfileWriter):
    """Writer for memory profiling data"""

    def _create_formatters(self) -> Dict[OutputFormat, BaseFormatter]:
        """Create formatters for memory data"""
        return {
            OutputFormat.CONSOLE: ConsoleMemoryFormatter(self._config),
            OutputFormat.CSV: CSVMemoryFormatter(self._config),
            OutputFormat.TXT: ConsoleMemoryFormatter(self._config),
        }

    def _get_metric_name(self) -> str:
        return "Memory Usage"


# ####################################
# Formatter Registry for Extensibility
# ####################################


class FormatterRegistry:
    """Registry for custom formatters"""

    _formatters: Dict[str, Type[BaseFormatter]] = {}

    @classmethod
    def register(cls, name: str, formatter_class: Type[BaseFormatter]) -> None:
        """Register a custom formatter"""
        if not issubclass(formatter_class, BaseFormatter):
            raise ValueError("Formatter must inherit from BaseFormatter")
        cls._formatters[name] = formatter_class

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseFormatter]]:
        """Get a registered formatter by name"""
        return cls._formatters.get(name)

    @classmethod
    def list_formatters(cls) -> List[str]:
        """List all registered formatter names"""
        return list(cls._formatters.keys())
