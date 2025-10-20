"""
Time profiling utilities.

@author: Jakub Walczak
@organization: HappyRavenLabs
"""

__all__ = ["timer", "ltimer"]
import linecache
import sys
import threading
import time
from collections import defaultdict
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .stats import Stats
from .writing import ReportConfig, TimeWriter


class timer:
    _tracker: threading.local
    repeat: int
    out: Any
    precision: int
    stats: Stats

    def __init__(
        self, *, repeat: int = 1, out: Any = None, precision: int = 4
    ):
        self._tracker = threading.local()
        self._tracker.running: Set[Callable] = set()
        self.repeat = repeat
        self.out = out
        self.precision = precision

    def __call__(
        self,
        func: Optional[Callable] = None,
    ) -> Callable:
        """Decorator for measuring execution time of a function."""
        _times: List[float] = []
        if self.repeat < 1:
            raise ValueError("Repeat must be at least 1.")

        @wraps(func)
        def wrapper(*args, **kwargs):

            if func in self._tracker.running:
                return func(*args, **kwargs)
            try:
                self._tracker.running.add(func)
                for _ in range(self.repeat):
                    start_time = time.perf_counter()
                    result = func(*args, **kwargs)
                    _times.append(time.perf_counter() - start_time)
                return result
            finally:
                if not _times:
                    _times.append(time.perf_counter() - start_time)

                self.stats = Stats(_times)
                TimeWriter(
                    self.out, config=ReportConfig(precision=self.precision)
                ).with_func(func, *args, **kwargs).write(_times)
                if func in self._tracker.running:
                    self._tracker.running.remove(func)

        return wrapper

    def __enter__(self):
        if self.repeat > 1:
            raise ValueError(
                "Repeat must be 1 when used as a context manager."
            )
        self._start_time: float = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        _end_time: float = time.perf_counter()
        self.stats = Stats([_end_time - self._start_time])
        TimeWriter(
            self.out, config=ReportConfig(precision=self.precision)
        ).write([_end_time - self._start_time])


class ltimer:
    _tracker: threading.local
    out: Any
    precision: int
    stats: Dict[Tuple[str, int, str], Stats]

    def __init__(self, *, out: Any = None, precision: int = 4):
        self._tracker = threading.local()
        self._tracker.running: Set[Callable] = set()
        self.out = out
        self.precision = precision

    def __call__(
        self,
        func: Optional[Callable] = None,
    ) -> Callable:
        """Decorator for measuring execution time of a function."""

        @wraps(func)
        def wrapper(*args, **kwargs):

            if func in self._tracker.running:
                return func(*args, **kwargs)

            _line_time: Dict[int, List[float]] = defaultdict(list)
            _org_trace = sys.gettrace()
            _root_frame = sys._getframe(1)
            _root_file = _root_frame.f_code.co_filename
            _prev_line = None
            _prev_time = time.perf_counter()
            _last_line = None
            _with_line = _root_frame.f_lineno

            def _trace(frame, event: str, arg):
                nonlocal _prev_line, _prev_time, _last_line
                if event != "line":
                    return _trace
                current_time = time.perf_counter()
                current_file = frame.f_code.co_filename
                if current_file != _root_file:
                    return _trace
                if _prev_line is not None:
                    _line_time[_prev_line].append(current_time - _prev_time)

                filename = frame.f_code.co_filename
                lineno = frame.f_lineno
                _prev_line = (filename, lineno)
                _prev_time = current_time

                return _trace

            try:
                self._tracker.running.add(func)
                _root_frame.f_trace = _trace
                sys.settrace(_trace)
                return func(*args, **kwargs)
            finally:
                if _prev_line is not None:
                    end_time = time.perf_counter()
                    _line_time[_prev_line].append(end_time - _prev_time)
                _line_time = dict(
                    filter(
                        lambda item: item[0][1] != _with_line,
                        _line_time.items(),
                    )
                )
                if func in self._tracker.running:
                    self._tracker.running.remove(func)
                sys.settrace(_org_trace)
                self.stats = {
                    (
                        linecache.getline(filename, lineno).strip(),
                        lineno,
                        filename,
                    ): Stats(times)
                    for ((filename, lineno), times) in _line_time.items()
                }

                TimeWriter(
                    self.out, config=ReportConfig(precision=self.precision)
                ).with_func(func, *args, **kwargs).write(
                    _line_time, root_file=_root_file
                )

        return wrapper

    def __enter__(self):
        self._start_time: float = time.perf_counter()
        self._line_time: Dict[int, List[float]] = defaultdict(list)
        self._org_trace = sys.gettrace()
        self._root_frame = sys._getframe(1)
        self._root_file = self._root_frame.f_code.co_filename
        self._prev_line = None
        self._prev_time = time.perf_counter()
        self._last_line = None
        self._with_line = self._root_frame.f_lineno

        def _trace(frame, event: str, arg):
            if event != "line":
                return _trace
            current_time = time.perf_counter()
            current_file = frame.f_code.co_filename
            if current_file != self._root_file:
                return _trace
            if self._prev_line is not None:
                self._line_time[self._prev_line].append(
                    current_time - self._prev_time
                )

            filename = frame.f_code.co_filename
            lineno = frame.f_lineno
            self._prev_line = (filename, lineno)
            self._prev_time = current_time

            return _trace

        self._root_frame.f_trace = _trace
        sys.settrace(_trace)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._prev_line is not None:
            end_time = time.perf_counter()
            self._line_time[self._prev_line].append(end_time - self._prev_time)
        self._line_time = dict(
            filter(
                lambda item: item[0][1] != self._with_line,
                self._line_time.items(),
            )
        )
        self.stats = {
            (
                linecache.getline(filename, lineno).strip(),
                lineno,
                filename,
            ): Stats(times)
            for ((filename, lineno), times) in self._line_time.items()
        }
        TimeWriter(
            self.out, config=ReportConfig(precision=self.precision)
        ).write(self._line_time, root_file=self._root_file)
        sys.settrace(self._org_trace)
