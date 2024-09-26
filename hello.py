import dronekit
import dronekit_sitl


def main():
    print("Start simulator (SITL)")
    sitl = dronekit_sitl.start_default()
    connection_string = sitl.connection_string()

    # Connect to the Vehicle.
    print("Connecting to vehicle on: %s" % (connection_string,))
    vehicle = dronekit.connect(connection_string, wait_ready=True)
    # Get the vehicle attributes (state)
    for key, value in get_all_sensor_data(vehicle).items():
        print(key, value)
    vehicle.close()

    # Shut down simulator
    sitl.stop()
    print("Completed")


def get_all_sensor_data(vehicle):
    # Get all sensor data from the vehicle
    sensor_data = {
        "imu": vehicle.attitude,
        "gps": vehicle.gps_0,
        "battery": vehicle.battery,
        "last_heartbeat": vehicle.last_heartbeat,
        "is_armable": vehicle.is_armable,
        "system_status": vehicle.system_status.state,
        "mode": vehicle.mode.name,
        "latitude": vehicle.location.global_relative_frame.lat,
        "longitude": vehicle.location.global_relative_frame.lon,
        "altitude": vehicle.location.global_relative_frame.alt,
        "heading": vehicle.heading,
        "airspeed": vehicle.airspeed,
        "groundspeed": vehicle.groundspeed,
        "roll": vehicle.attitude.roll,
        "pitch": vehicle.attitude.pitch,
        "yaw": vehicle.attitude.yaw,
        "throttle": vehicle.channels["3"],
        "armed": vehicle.armed,
        "ekf_ok": vehicle.ekf_ok,
        "gps_fix": vehicle.gps_0.fix_type,
        "gps_satellites_visible": vehicle.gps_0.satellites_visible,
        "battery_voltage": vehicle.battery.voltage,
        "battery_current": vehicle.battery.current,
        "battery_level": vehicle.battery.level,
    }
    return sensor_data


if __name__ == "__main__":
    main()
