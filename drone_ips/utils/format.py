from datetime import datetime


def strftime(timestamp: float) -> str:
    """
    Convert a timestamp to a string in the format YYYY-MM-DD_HH-MM-SS.
    If no timestamp is provided, use the current time.

    Parameters
    ----------
    timestamp : float,
        The timestamp to convert (seconds since epoch)

    Returns
    -------
    str
        The formatted timestamp as a string.
    """
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d_%H-%M-%S")
