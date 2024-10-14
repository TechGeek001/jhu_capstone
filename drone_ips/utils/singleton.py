"""Singleton metaclass to ensure only one instance of a class is created."""


class Singleton(type):
    """Metaclass to ensure only one instance of a class is created.

    This metaclass is used to ensure that only one instance of a class is created. If an
    instance of the class already exists, the metaclass will return the existing instance.
    If an instance does not exist, the metaclass will create a new instance and return it.
    """

    # Dict holding the class object and its instance
    _instances: dict["Singleton", type["Singleton"]] = {}

    def __call__(cls, *args: list, **kwargs: dict) -> type["Singleton"]:
        """Control the instantiation process to ensure only one instance.

        Parameters
        ----------
        *args : list
            The arguments to pass to the class constructor.
        **kwargs : dict
            The keyword arguments to pass to the class constructor.

        Returns
        -------
        Singleton
            The instance of the class.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
