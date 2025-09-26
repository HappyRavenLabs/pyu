"""
Time profiling utilities.

@author: Jakub Walczak
@organization: HappyRavenLabs
"""
from collections import defaultdict
import linecache
import sys
from typing import Callable
import time
from functools import wraps
from rich.table import Table
from .. import console
from .utils import compute_statistics


class Timer:
    """Context manager for measuring execution time for code blocks."""
    elapsed_time: float = 0.0
    _start_time: float = 0.0
    _end_time: float = 0.0
    _times: list[float]
    verbose: bool

    def __init__(self, verbose: bool = True) -> None:
        self._times = []
        self.verbose = verbose

    # ######################
    # Context manager logic
    # ######################
    def __enter__(self):
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._end_time = time.perf_counter()
        self.elapsed_time = self._end_time - self._start_time
        if self.verbose:
            console.log(f"[bold green]Elapsed time:[/bold green] {self.elapsed_time:.6f} seconds")
        return None
    
        
    # ######################
    # Decorator logic
    # ######################
    def __call__(self, func: Callable | None = None, *, repeat: int = 1) -> Callable:
        if func is None:
            return self._wrap_with_arguments(repeat=repeat)
        else:
            return self._wrap_function(func)

    def _wrap_with_arguments(self, *, repeat: int) -> Callable:
        def wrapper(func: Callable) -> Callable:
            return self._wrap_function(func, repeat)
        return wrapper


    def _wrap_function(self, func: Callable, repeat: int = 1) -> Callable:
        """Decorator for measuring execution time of a function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(repeat):
                with type(self)() as t:
                    result = func(*args, **kwargs)
                self._times.append(t.elapsed_time)
            self.elapsed_time = sum(self._times)
            # NOTE: Always return the last function result
            if self.verbose:
                self.print_report()
            return result
        return wrapper

    @property
    def statistics(self) -> dict[str, float]:
        """Statistics about the timing results."""
        return compute_statistics(self._times)

    def print_report(self) -> None:
        """Print a report of the timing results."""
        if not self._times:
            console.log("[bold yellow]No timing data available.[/bold yellow]")
            return
        if len(self._times) == 1:
            console.log(f"[bold green]Elapsed time:[/bold green] {self.elapsed_time:.6f} seconds")
        else:
            statistics = self.statistics
            table = Table(title="Timing Report")
            table.add_column("Metric", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            table.add_row("Total elapsed time", f"{self.elapsed_time:.6f} seconds over {statistics['count']} runs")
            table.add_row("Average time per run", f"{statistics['mean']:.6f} seconds")
            table.add_row("Standard deviation", f"{statistics['stdev']:.6f} seconds")
            table.add_row("Median time", f"{statistics['median']:.6f} seconds")
            table.add_row("Interquartile range (IQR)", f"{statistics['iqr']:.6f} seconds")
            table.add_row("Minimum time", f"{statistics['min']:.6f} seconds")
            table.add_row("Maximum time", f"{statistics['max']:.6f} seconds")
            console.log(table)


class LineTimer:
    """Profiler for measuring execution time line by line."""

    _line_time: dict[int, float]
    _prev_line: int | None = None
    _prev_time: float | None = None
    verbose: bool
    _top_frame_filename: str | None = None

    def __init__(self, verbose: bool = True) -> None:
        self._line_time = defaultdict(list)
        self.verbose = verbose

    @property
    def elapsed_time(self) -> float:
        return sum(sum(times) for times in self._line_time.values())

    # ######################
    # Context manager logic
    # ######################
    def _trace_call(self, frame, event: str, arg):
        if event != "line":
            return self._trace_call
        current_time = time.perf_counter()
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        if filename == self._top_frame_filename:
            if self._prev_line is not None:
                self._line_time[self._prev_line].append(current_time - self._prev_time)
        self._prev_line = (filename, lineno)
        self._prev_time = current_time
        return self._trace_call
        
    
    # ######################
    # Decorator logic
    # ######################
    def __call__(self, func: Callable | None = None, *, repeat: int = 1) -> Callable:
        if func is None:
            return self._wrap_with_arguments(repeat=repeat)
        else:
            return self._wrap_function(func)    
        
    def _wrap_with_arguments(self, *, repeat: int) -> Callable:
        def wrapper(func: Callable) -> Callable:
            return self._wrap_function(func, repeat)
        return wrapper


    def _wrap_function(self, func: Callable, repeat: int = 1) -> Callable:
        """Decorator for measuring execution time of a function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(repeat):
                self._prev_line = None
                self._top_frame_filename = sys._getframe(1).f_code.co_filename
                self._prev_time = time.perf_counter()   
                _org_trace = sys.gettrace()
                sys.settrace(self._trace_call)
                result = func(*args, **kwargs)
                sys.settrace(_org_trace)
            # NOTE: Always return the last function result
            if self.verbose:
                self.print_report()
            return result
        return wrapper        
    
    def print_report(self) -> None:
        if not self._line_time:
            console.log("[bold yellow]No timing data available.[/bold yellow]")
            return
        table = Table(title="Line-by-Line Timing Report")
        table.add_column("Line No.", style="cyan", no_wrap=True)
        table.add_column("Code", style="green")
        table.add_column("Mean elapsed Time (s)", style="yellow")
        table.add_column("Std. dev. (s)", style="white")
        table.add_column("Total Time (s)", style="red")
        table.add_column("Calls", style="blue")
        for (filename, lineno), entry in self._line_time.items():
            code = linecache.getline(filename, lineno).strip()
            stats = compute_statistics(entry)
            table.add_row(
                str(lineno),
                code,
                f"{stats['mean']:.6f}",
                f"{stats['stdev']:.6f}",
                f"{stats['sum']:.6f}",
                str(stats['count'])
            )

        console.log(table)