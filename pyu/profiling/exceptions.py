"""
Module for custom exceptions used in profiling utilities.

@author: Jakub Walczak
@organization: HappyRavenLabs
"""


class ProfilingError(Exception):
    """Base exception for profiling errors"""

    pass


class InvalidOutputError(ProfilingError):
    """Raised when output target is invalid"""

    pass


class DataValidationError(ProfilingError):
    """Raised when measurement data is invalid"""

    pass
