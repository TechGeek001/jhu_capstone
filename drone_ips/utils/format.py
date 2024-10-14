"""Utility functions for formatting data."""

from datetime import datetime


def datetime_str(timestamp: float) -> str:
    """Convert a timestamp to a string in the format YYYY-MM-DD_HH-MM-SS.

    Parameters
    ----------
    timestamp : float
        The timestamp to convert (seconds since epoch).

    Returns
    -------
    str
        The formatted timestamp as a string.
    """
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d_%H-%M-%S")
