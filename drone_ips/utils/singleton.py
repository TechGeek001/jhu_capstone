class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Control the instantiation process to ensure only one instance."""
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
