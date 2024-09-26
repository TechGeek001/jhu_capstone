import dronekit_sitl

import autonomous_uas.utils as utils


class SITL_Vehicle:

    def __init__(self, lat=None, lon=None, svr_conn_string=""):
        self._logger = utils.logging.get_logger("sitl")
        self._sitl = None
        self._home_lat = lat
        self._home_lon = lon
        self._svr_conn_string = svr_conn_string

    def __enter__(self) -> None:
        self._logger.info("Starting SITL vehicle")
        self._sitl = dronekit_sitl.start_default(self._home_lat, self._home_lon)

    def __exit__(self, exception_type, exception_value, exception_traceback) -> None:
        if self._sitl:
            self._logger.info("Stopping SITL vehicle")
            self._sitl.close()

    @property
    def conn_string(self):
        return self._sitl.connection_string()

    def register(self):
        return None
