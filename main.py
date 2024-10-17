"""Application entry point."""


def start_monitor(connection_string):
    """Start the monitor with the given connection string.

    Parameters
    ----------
    connection_string : str
        The connection string for the vehicle.
    """
    from drone_ips.monitor import Monitor

    m = Monitor(connection_string)
    m.start()


def start_testbed_monitor(connection_string):
    """Start the testbed monitor with the given connection string.

    Parameters
    ----------
    connection_string : str
        The connection string for the vehicle.
    """
    from drone_ips.testbed import Monitor

    m = Monitor(connection_string)
    m.attack_manager.add_test("gps_spoofer", time_window=(5, 30))
    m.start()


if __name__ == "__main__":
    start_testbed_monitor("udp:0.0.0.0:14540")
