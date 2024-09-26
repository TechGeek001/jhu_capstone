import autonomous_uas.utils as utils


class Server:

    def __init__(self) -> None:
        self._logger = utils.logging.get_logger("server")

    @property
    def test(self):
        return 1

    def __enter__(self) -> None:
        self._logger.info("Starting companion server")

    def __exit__(self, exception_type, exception_value, exception_traceback) -> None:
        self._logger.info("Stopping companion server")
