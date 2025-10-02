"""
Profiling utility functions.

@author: Jakub Walczak
@organization: HappyRavenLabs
"""

import inspect
import linecache
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

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


def get_named_arguments(func: Callable, args: Tuple, kwargs: Dict) -> Dict:
    sig = inspect.signature(func)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()
    return dict(bound.arguments)


def print_report(
    output: Any,
    times: List[float],
    func: Optional[Callable] = None,
    arguments: Optional[Tuple] = None,
) -> None:
    """Print a report of the timing results."""
    console = Console(file=_select_output(output))
    if not times:
        console.log("[bold yellow]No timing data available.[/bold yellow]")
        return
    if len(times) == 1:
        console.log(
            f"[bold green]Elapsed time:[/bold green] {sum(times):.6f} seconds"
        )
    else:
        statistics = compute_statistics(times)
        if func is not None and arguments is not None:
            table = Table(
                title=f"Timing Report for function '{func.__name__}'",
                caption=(
                    f"Timing report for function {func.__name__} "
                    "called with arguments "
                    f"{str(get_named_arguments(func, *arguments))}"
                ),
            )
        else:
            table = Table(title="Timing Report")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")

        table.add_row(
            "Total elapsed time",
            f"{sum(times):.6f} seconds over {statistics['count']} runs",
        )
        table.add_row(
            "Average time per run", f"{statistics['mean']:.6f} seconds"
        )
        table.add_row(
            "Standard deviation", f"{statistics['stdev']:.6f} seconds"
        )
        table.add_row("Median time", f"{statistics['median']:.6f} seconds")
        table.add_row(
            "Interquartile range (IQR)", f"{statistics['iqr']:.6f} seconds"
        )
        table.add_row("Minimum time", f"{statistics['min']:.6f} seconds")
        table.add_row("Maximum time", f"{statistics['max']:.6f} seconds")
        console.log(table)


def print_line_report(
    output, line_times: Dict[int, List[float]], root_file: str
) -> None:
    console = Console(file=_select_output(output))
    if not line_times:
        console.log(
            "[bold yellow]No line timing data available.[/bold yellow]"
        )
        return

    table = Table(
        title=f"Line Timing Report for '{root_file}'",
        caption=f"Timing report for lines executed in {root_file}",
    )
    table.add_column("Line No.", style="cyan", no_wrap=True)
    table.add_column("Code", style="green")
    table.add_column("Total Time (s)", style="magenta")
    table.add_column("Avg Time (s)", style="magenta")
    table.add_column("Count", style="yellow")

    for (filename, line_no), times in sorted(line_times.items()):
        code_line = linecache.getline(filename, line_no).strip()
        stats = compute_statistics(times)
        table.add_row(
            str(line_no),
            code_line,
            f"{stats['sum']:.6f}",
            f"{stats['mean']:.6f}",
            str(stats["count"]),
        )

    console.log(table)
