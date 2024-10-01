class Singleton(type):
    _instances = {}

    def __call__(cls, *args: list, **kwargs: dict) -> "Singleton":
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
