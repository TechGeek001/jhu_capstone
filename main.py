import argparse

import autonomous_uas as uas
import autonomous_uas.companion as comp
import autonomous_uas.utils as utils


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run the autonomous UAS system.")
    # Add a group that determines which node is being run in this process
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--sitl", action="store_true", help="Run the Software-in-the-Loop (SITL) vehicle in this process"
    )
    group.add_argument("--server", action="store_true", help="Run the companion computer's server in this process")
    # Parse the main command argument
    mode, args = parser.parse_known_args()
    # Based on which mode is running, parse the remaining arguments
    if mode.sitl:
        sitl_parser = argparse.ArgumentParser(prog="SITL")
        sitl_parser.add_argument(
            "--vehicle-type", choices=["quadcopter", "plane"], required=True, help="Specify the vehicle type"
        )
        sitl_parser.add_argument("--altitude", type=int, help="Initial altitude for the SITL vehicle")

    elif mode.server:
        pass

    return mode, args


def run_sitl(args):
    with uas.SITL_Vehicle() as sitl:  # noqa: F841
        pass


def run_server(args):
    with comp.Server() as svr:  # noqa: F841
        pass


if __name__ == "__main__":
    # Initialize the logger
    logger = utils.LogManager
    # Parse any CLI arguments
    global_args, local_args = parse_arguments()

    if global_args.sitl:
        run_sitl(local_args)
    elif global_args.server:
        run_server(local_args)
    else:
        raise NotImplementedError()
