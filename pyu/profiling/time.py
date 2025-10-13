"""
Time profiling utilities.

@author: Jakub Walczak
@organization: HappyRavenLabs
"""

__all__ = ["timer", "ltimer"]
import sys
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set

from .utils import TimeWriter


class Timer:
    _tracker: threading.local

    def __init__(self):
        self._tracker = threading.local()
        self._tracker.running: Set[Callable] = set()

    def __call__(
        self,
        func: Optional[Callable] = None,
        *,
        repeat: int = 1,
        out: Any = None,
    ) -> Callable:
        """Decorator for measuring execution time of a function."""
        if func is None:
            return self._wrap_with_arguments(repeat=repeat, out=out)
        else:
            return self._wrap_function(func)

    def _wrap_with_arguments(
        self, *, repeat: int, out: Any = None
    ) -> Callable:
        def wrapper(func: Callable) -> Callable:
            return self._wrap_function(func, repeat, out)

        return wrapper

    def _wrap_function(
        self, func: Callable, repeat: int = 1, out: Any = None
    ) -> Callable:
        """Decorator for measuring execution time of a function."""
        _times: List[float] = []
        if repeat < 1:
            raise ValueError("Repeat must be at least 1.")

        @wraps(func)
        def wrapper(*args, **kwargs):

            if func in self._tracker.running:
                return func(*args, **kwargs)
            try:
                self._tracker.running.add(func)
                for _ in range(repeat):
                    start_time = time.perf_counter()
                    result = func(*args, **kwargs)
                    _times.append(time.perf_counter() - start_time)
                TimeWriter(out).with_func(func, *args, **kwargs).write(_times)
                return result
            finally:
                if func in self._tracker.running:
                    self._tracker.running.remove(func)

        return wrapper

    @contextmanager
    def run(self, out: Any = None):
        """Context manager for measuring execution time."""
        _start_time: float = time.perf_counter()
        try:
            yield
        finally:
            _end_time: float = time.perf_counter()
            TimeWriter(out).write([_end_time - _start_time])


class LineTimer:
    _tracker: threading.local

    def __init__(self):
        self._tracker = threading.local()
        self._tracker.running: Set[Callable] = set()

    def __call__(
        self,
        func: Optional[Callable] = None,
        *,
        out: Any = None,
    ) -> Callable:
        """Decorator for measuring execution time of a function."""
        if func is None:
            return self._wrap_with_arguments(out=out)
        else:
            return self._wrap_function(func)

    def _wrap_with_arguments(self, *, out: Any = None) -> Callable:
        def wrapper(func: Callable) -> Callable:
            return self._wrap_function(func, out)

        return wrapper

    def _wrap_function(self, func: Callable, out: Any = None) -> Callable:
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
                result = func(*args, **kwargs)
                if _prev_line is not None:
                    end_time = time.perf_counter()
                    _line_time[_prev_line].append(end_time - _prev_time)
                _line_time = dict(
                    filter(
                        lambda item: item[0][1] != _with_line,
                        _line_time.items(),
                    )
                )
                return result
            finally:
                if func in self._tracker.running:
                    self._tracker.running.remove(func)
                sys.settrace(_org_trace)
                TimeWriter(out).with_func(func, *args, **kwargs).write(
                    _line_time, root_file=_root_file
                )

        return wrapper

    @contextmanager
    def run(self, out: Any = None):
        """Context manager for measuring execution time line by line."""
        _line_time: Dict[int, List[float]] = defaultdict(list)
        _org_trace = sys.gettrace()
        # NOTE: as we are using context_manager decorator, we need to
        # go two levels up the stack
        _root_frame = sys._getframe(2)
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

        _root_frame.f_trace = _trace
        sys.settrace(_trace)
        try:
            yield
        finally:
            if _prev_line is not None:
                end_time = time.perf_counter()
                _line_time[_prev_line].append(end_time - _prev_time)
            _line_time = dict(
                filter(
                    lambda item: item[0][1] != _with_line, _line_time.items()
                )
            )
            TimeWriter(out).write(_line_time, root_file=_root_file)
            sys.settrace(_org_trace)


timer = Timer()
ltimer = LineTimer()
