"""This is a simple example of a machine learning model monitor. It listens for incoming data from the model server, processes it, and sends back a verdict."""

import json

import joblib
import numpy as np
import pandas as pd
import zmq

"""
    * accuracy:
        -> Training: 95%
        -> Testing: 94%

"""

PORT = 55552


def preprocess_vehicle_data(scaler, current_data: dict) -> np.array:
    """Preprocess the vehicle data for prediction.

    Parameters
    ----------
    scaler : object
        The scaler.
    current_data : dict
        The current data from the vehicle.

    Returns
    -------
    np.array
        The preprocessed data ready for prediction.
    """
    # Convert the current_data dictionary to a DataFrame
    df = pd.DataFrame([current_data])

    # Feature Extraction
    features = [
        "timestamp",
        "battery.current",
        "battery.level",
        "battery.voltage",
        "companion_computer.cpu_usage",
        "companion_computer.ram_usage",
    ]

    # Select all columns except those in columns_to_exclude
    df = df[features].copy()
    df = df.dropna()

    # Standardize the data using the loaded scaler
    scaled_data = scaler.transform(df)

    return scaled_data


def load_model(model_path: str):
    """Load the saved ML model.

    Parameters
    ----------
    model_path : str
        The path to the saved model file.

    Returns
    -------
    object
        The loaded model.
    """
    return joblib.load(model_path)


def make_prediction(model, scaler, current_data: dict) -> dict:
    """Make a prediction using the ML model.

    Parameters
    ----------
    model : object
        The loaded ML model.
    scaler : object
        The scaler.
    current_data : dict
        The current data from the vehicle.

    Returns
    -------
    dict
        The prediction result.
    """
    # Preprocess the data
    processed_data = preprocess_vehicle_data(scaler, current_data)

    # Make prediction
    prediction = model.predict(processed_data)
    print("Prediction:", prediction[0])

    # Return the prediction result in a dictionary
    return {"prediction": 1 if int(prediction[0]) == 1 else 0}


def main(model, scaler):
    """The main function for the monitor.

    Parameters
    ----------
    model : object
        The loaded ML model.
    scaler : object
        The scaler.
    """

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://*:{PORT}")
    socket.RCVTIMEO = 1000

    while True:
        try:
            data = json.loads(socket.recv().decode("utf-8"))
            current_data = data.get("current", {})  # noqa
            last_data = data.get("last", {})  # noqa
            # Do things here
            response = make_prediction(model, scaler, current_data)
            # Send back a verdict
            verdict = response["prediction"]
            socket.send(bytes(str(verdict), "utf-8"))
        except KeyboardInterrupt:
            break
        except zmq.error.Again:
            continue


if __name__ == "__main__":
    # Load the model once at the module level
    model = load_model("./drone_ips/models/one_class_cpu.pkl")
    # Load the scaler
    scaler = joblib.load("./drone_ips/models/preprocessor_cpu.pkl")
    main(model, scaler)
