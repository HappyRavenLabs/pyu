""" "
Profiling statistics utilities.

@author: Jakub Walczak
"""

from functools import cached_property
from numbers import Number
from typing import List


class Stats:
    """Compute basic statistics for a list of numbers."""

    def __init__(self, values: List[Number]):
        self.values = values

    @cached_property
    def mean(self) -> float:
        return sum(self.values) / len(self.values)

    @cached_property
    def sorted_values(self) -> List[float]:
        return sorted(self.values)

    @cached_property
    def median(self) -> float:
        sorted_values = self.sorted_values
        mid = len(sorted_values) // 2
        return (
            (sorted_values[mid] + sorted_values[mid - 1]) / 2
            if len(sorted_values) % 2 == 0
            else sorted_values[mid]
        )

    @cached_property
    def mode(self) -> float:
        return max(set(self.values), key=self.values.count)

    @cached_property
    def stddev(self) -> float:
        if len(self.values) < 2:
            return 0.0
        mean = self.mean
        return (
            sum((x - mean) ** 2 for x in self.values) / (len(self.values) - 1)
        ) ** 0.5
