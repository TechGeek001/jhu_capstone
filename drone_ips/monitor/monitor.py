import time

import dronekit

import drone_ips.logging as logging
import drone_ips.utils as ips_utils


class Monitor:

    def __init__(self, conn_str):
        self.conn_str = conn_str
        self.logger = logging.LogManager.get_logger("monitor")
        self.vehicle = None
        self._data = []
        self.csv_writer = None

    def start(self):
        # Register a listener for all MAVLink messages
        # @self.vehicle.on_message('*')
        # def message_listener(vehicle, name, message):
        #     source_system = message.get_srcSystem()
        #     source_component = message.get_srcComponent()

        #     if source_system == 1:
        #         source = "Flight Controller (FC)"
        #     elif source_system == 255:
        #         source = "Ground Control Station (GCS)"
        #     else:
        #         source = f"Unknown system ID {source_system}"

        #     self.logger.info(f"Received message from {source}:{source_component}: {message}")
        # self.logger.info("Listening for incoming MAVLink messages.")
        self._start_time = int(time.time())
        # Connect to the MAVLink stream using DroneKit
        self.logger.info(f"Connecting to the vehicle on {self.conn_str}...")
        try:
            self.vehicle = dronekit.connect(self.conn_str, wait_ready=True)
            self._event_loop()
        except dronekit.APIException:
            self.logger.error("Timeout! No vehicle connection.")

    def stop(self):
        # Close the vehicle connection
        self.vehicle.close()
        self.logger.info("Connection closed.")

    def _event_loop(self):
        try:
            while True:
                self.logger.debug("Gathering data...")
                current_data = ips_utils.misc.flatten_dict(
                    {
                        "timestamp": int(time.time()),
                        "system": self._get_system_data(),
                        "location": self._get_location_data(),
                    }
                )
                if self.csv_writer is None:
                    self.csv_writer = logging.CSVLogger(
                        f"logs/{ips_utils.format.strftime(self._start_time)}_data.csv", list(current_data.keys())
                    )
                self.csv_writer.log(current_data)
                self._data.append(current_data)
                time.sleep(1)  # Sleep for a short duration to keep the script alive

        except KeyboardInterrupt:
            self.logger.info("Stopped listening for messages.")
            self.stop()

    def _get_system_data(self):
        # Get the system status and mode of the vehicle
        return {
            "armed": self.vehicle.armed,
            "mode": self.vehicle.mode.name,
            "battery": {
                "voltage": self.vehicle.battery.voltage,
                "current": self.vehicle.battery.current,
                "level": self.vehicle.battery.level,
            },
        }

    def _get_location_data(self):
        # Get the current location of the vehicle
        location = self.vehicle.location.global_frame
        if len(self._data) > 0:
            prev = self._data[-1]
        else:
            prev = None
        return {
            "lat": location.lat,
            "lon": location.lon,
            "alt": location.alt,
            "ll_delta": (
                ips_utils.math.haversine_distance(
                    prev["location.lat"], prev["location.lon"], location.lat, location.lon
                )
                if prev is not None
                else 0.0
            ),
        }

    # Uncomment and adjust if you want to implement the sensor_data property using DroneKit
    # @property
    # def sensor_data(self):
    #     # Get all sensor data from the vehicle
    #     sensor_data = {
    #         "imu": self.vehicle.attitude,
    #         "gps": self.vehicle.gps_0,
    #         "battery": self.vehicle.battery,
    #         "last_heartbeat": self.vehicle.last_heartbeat,
    #         "is_armable": self.vehicle.is_armable,
    #         "system_status": self.vehicle.system_status.state,
    #         "mode": self.vehicle.mode.name,
    #         "latitude": self.vehicle.location.global_relative_frame.lat,
    #         "longitude": self.vehicle.location.global_relative_frame.lon,
    #         "altitude": self.vehicle.location.global_relative_frame.alt,
    #         "heading": self.vehicle.heading,
    #         "airspeed": self.vehicle.airspeed,
    #         "groundspeed": self.vehicle.groundspeed,
    #         "roll": self.vehicle.attitude.roll,
    #         "pitch": self.vehicle.attitude.pitch,
    #         "yaw": self.vehicle.attitude.yaw,
    #         "throttle": self.vehicle.channels["3"],
    #         "armed": self.vehicle.armed,
    #         "ekf_ok": self.vehicle.ekf_ok,
    #         "gps_fix": self.vehicle.gps_0.fix_type,
    #         "gps_satell
