"""
Memory profiling utilities.

@author: Jakub Walczak
@organization: HappyRavenLabs
"""

__all__ = ["mem", "lmem"]
import sys
import threading
import tracemalloc
from collections import defaultdict
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from .writing import MemoryWriter


class MemTracer:
    _tracker: threading.local

    def __init__(self):
        self._tracker = threading.local()
        self._tracker.running: set[Callable] = set()

    def __call__(
        self, func: Optional[Callable] = None, repeat: int = 1, out: Any = None
    ) -> Callable:
        """Decorator for measuring memory usage of a function."""
        if func is None:
            return self._wrap_with_arguments(repeat=repeat, out=out)
        else:
            return self._wrap_function(func)

    def _wrap_with_arguments(self, *, repeat: int, out: Any) -> Callable:
        def wrapper(func: Callable) -> Callable:
            return self._wrap_function(func, repeat, out=out)

        return wrapper

    def _wrap_function(
        self, func: Callable, repeat: int = 1, out: Any = None
    ) -> Callable:
        """Decorator for measuring memory usage of a function."""
        _mem_usages = []
        if repeat < 1:
            raise ValueError("Repeat must be at least 1.")

        @wraps(func)
        def wrapper(*args, **kwargs):
            if func in self._tracker.running:
                return func(*args, **kwargs)
            try:
                self._tracker.running.add(func)
                result = None
                for _ in range(repeat):
                    tracemalloc.start()
                    result = func(*args, **kwargs)
                    _, peak = tracemalloc.get_traced_memory()
                    _mem_usages.append(peak)
                    tracemalloc.stop()
            finally:
                self._tracker.running.remove(func)

                MemoryWriter(out).with_func(func, *args, **kwargs).write(
                    _mem_usages
                )
            return result

        return wrapper

    @contextmanager
    def run(self, out: Any = None):
        """Context manager for measuring memory usage of a code block."""
        tracemalloc.start()
        try:
            yield
        finally:
            peak = tracemalloc.get_traced_memory()[1]
            tracemalloc.stop()
            MemoryWriter(output_target=out).write([peak])


class LineMemoryTracer:
    _tracker: threading.local

    def __init__(self):
        self._tracker = threading.local()
        self._tracker.running: set[Callable] = set()

    def __call__(
        self, func: Optional[Callable] = None, out: Any = None
    ) -> Callable:
        """Decorator for measuring memory usage of a function."""
        if func is None:
            return self._wrap_with_arguments(out=out)
        else:
            return self._wrap_function(func)

    def _wrap_with_arguments(self, *, out: Any) -> Callable:
        def wrapper(func: Callable) -> Callable:
            return self._wrap_function(func, out=out)

        return wrapper

    def _wrap_function(self, func: Callable, out: Any = None) -> Callable:
        """Decorator for measuring memory usage of a function."""
        _mem_usages = []
        if func is None:
            raise ValueError("Function to be decorated must not be None.")

        @wraps(func)
        def wrapper(*args, **kwargs):
            if func in self._tracker.running:
                return func(*args, **kwargs)
            try:
                self._tracker.running.add(func)
                tracemalloc.start()
                result = func(*args, **kwargs)
                _, peak = tracemalloc.get_traced_memory()
                _mem_usages.append(peak)
                tracemalloc.stop()
            finally:
                self._tracker.running.remove(func)

                MemoryWriter(out).with_func(func, *args, **kwargs).write(
                    _mem_usages
                )
            return result

        return wrapper

    @contextmanager
    def run(self, out: Any = None):
        """Context manager for measuring memory usage of a code block."""
        _line_mem: Dict[int, List[float]] = defaultdict(list)
        _org_trace = sys.gettrace()
        _root_frame = sys._getframe(2)
        _root_file = _root_frame.f_code.co_filename
        _prev_line = None
        _prev_peak_mem = tracemalloc.get_traced_memory()[1]
        _last_line = None
        _with_line = _root_frame.f_lineno

        def _trace(frame, event: str, arg):
            nonlocal _prev_line, _prev_peak_mem, _last_line
            if event != "line":
                return _trace

            current_file = frame.f_code.co_filename
            if current_file != _root_file:
                return _trace
            _, peak = tracemalloc.get_traced_memory()
            if _prev_line is not None:
                _line_mem[_prev_line].append(peak - _prev_peak_mem)

            filename = frame.f_code.co_filename
            lineno = frame.f_lineno
            _prev_line = (filename, lineno)
            _prev_peak_mem = peak
            return _trace

        _root_frame.f_trace = _trace
        sys.settrace(_trace)
        tracemalloc.start()
        try:
            yield
        finally:
            if _prev_line is not None:
                peak = tracemalloc.get_traced_memory()[1]
                _line_mem[_prev_line].append(peak - _prev_peak_mem)
            tracemalloc.stop()
            _line_mem = dict(
                filter(
                    lambda item: item[0][1] != _with_line, _line_mem.items()
                )
            )
            MemoryWriter(out).write(_line_mem, root_file=_root_file)
            sys.settrace(_org_trace)


mem = MemTracer()
lmem = LineMemoryTracer()
