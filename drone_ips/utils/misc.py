def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """
    Recursively flattens a nested dictionary.

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
    items = []
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
