"""
Memory profiling utilities.

@author: Jakub Walczak
@organization: HappyRavenLabs
"""

__all__ = ["mem", "lmem"]
import sys
import threading
import tracemalloc
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable

from .utils import MemoryWriter


class MemTracer:
    _tracker: threading.local

    def __init__(self):
        self._tracker = threading.local()
        self._tracker.running: set[Callable] = set()

    def __call__(
        self, func: Callable | None = None, repeat: int = 1, out: Any = None
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

        _root_file_name = sys._getframe(2).f_code.co_filename
        _filter = tracemalloc.Filter(True, filename_pattern=_root_file_name)

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
                    after_mem = tracemalloc.take_snapshot()
                    after_mem = after_mem.filter_traces([_filter])
                    stats = after_mem.statistics("lineno")
                    total_mem_bytes = sum(stat.size for stat in stats)
                    _mem_usages.append(total_mem_bytes)
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
        yield
        snapshot = tracemalloc.take_snapshot()
        tracemalloc.stop()

        MemoryWriter(out).write(
            [stat.size for stat in snapshot.statistics("lineno")]
        )


class LineMemoryTracer:
    pass


mem = MemTracer()
lmem = LineMemoryTracer()
