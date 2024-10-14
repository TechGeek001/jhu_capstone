"""Miscellaneous utility functions."""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Recursively flattens a nested dictionary.

    Parameters
    ----------
    d : dict
        The dictionary to flatten.
    parent_key : str
        The base key to use for nested keys (default is an empty string).
    sep : str
        The separator to use between keys (default is a dot).

    Returns
    -------
    dict
        A flattened dictionary with dot-separated keys.
    """
    items: list[tuple[str, Any]] = []
    for key, value in d.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key  # Create the new key
        if isinstance(value, dict):
            # Recursively flatten nested dictionaries
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        elif isinstance(value, list):
            # Handle lists by creating index-based keys
            for index, item in enumerate(value):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f"{new_key}[{index}]", sep=sep).items())
                else:
                    items.append((f"{new_key}[{index}]", item))
        else:
            items.append((new_key, value))
    return dict(items)


def get_object_properties(o: Any, pattern: str = r"(?!_)\w+") -> dict:
    """Get the properties of an object that match a pattern.

    Parameters
    ----------
    o : Any
        The object to get the properties from.
    pattern : str
        The regular expression pattern to match the properties (default is any word character).

    Returns
    -------
    dict
        A dictionary of the object's properties that match the pattern.
    """
    prog = re.compile(pattern)
    # Filter out callables from the object's attributes
    attrs = [attr for attr in dir(o) if prog.fullmatch(attr) is not None and not callable(getattr(o, attr))]
    return {k: getattr(o, k) for k in attrs}
