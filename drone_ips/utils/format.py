"""Utility functions for formatting data."""

import datetime as dt
from typing import Optional


def datetime_str(timestamp: Optional[float] = None) -> str:
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
    if timestamp is None:
        timestamp = dt.datetime.today().timestamp()
    return dt.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d_%H-%M-%S")
