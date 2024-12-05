"""This is a simple example of a machine learning model monitor. It listens for incoming data from the model server, processes it, and sends back a verdict."""

import json

import zmq


def main():
    """The main function for the monitor."""

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")
    socket.RCVTIMEO = 1000

    while True:
        try:
            data = json.loads(socket.recv().decode("utf-8"))
            current_data = data.get("current", {})  # noqa
            last_data = data.get("last", {})  # noqa
            # Do things here

            # Send back a verdict
            verdict = "benign"
            socket.send(bytes(verdict, "utf-8"))
        except KeyboardInterrupt:
            break
        except zmq.error.Again:
            continue


if __name__ == "__main__":
    main()
