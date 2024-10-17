"""Application entry point."""

import argparse


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns
    -------
    argparse.Namespace
        The parsed command-line arguments.
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter, description="Monitor a drone's data stream."
    )
    parser.add_argument("connection_string", type=str, help="the connection string for the vehicle.")
    parser.add_argument("--testbed", action="store_true", help="run the monitor in testbed mode.")
    return parser.parse_args()


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
    args = parse_args()
    start_func = start_monitor if not args.testbed else start_testbed_monitor
    start_func(args.connection_string)
