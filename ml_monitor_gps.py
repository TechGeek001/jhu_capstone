"""This is a simple example of a machine learning model monitor. It listens for incoming data from the model server, processes it, and sends back a verdict."""
# accuracy 50%

import json

import joblib
import numpy as np
import pandas as pd
import zmq

PORT = 55550


def preprocess_vehicle_data(current_data: dict) -> np.array:
    """Preprocess the vehicle data for prediction.

    Parameters
    ----------
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
        "gps_0.eph",
        "gps_0.epv",
        "gps_0.satellites_visible",
        "location.global_frame.lat",
        "location.global_frame.lon",
        "location.global_frame.alt",
        "heading",
    ]

    # Select all columns except those in columns_to_exclude
    df = df[features].copy()

    # Convert necessary columns to numeric values to avoid type errors
    df["location.global_frame.lat"] = pd.to_numeric(df["location.global_frame.lat"], errors="coerce")
    df["location.global_frame.lon"] = pd.to_numeric(df["location.global_frame.lon"], errors="coerce")
    df["location.global_frame.alt"] = pd.to_numeric(df["location.global_frame.alt"], errors="coerce")
    df["heading"] = pd.to_numeric(df["heading"], errors="coerce")
    df["gps_0.eph"] = pd.to_numeric(df["gps_0.eph"], errors="coerce")
    df["gps_0.epv"] = pd.to_numeric(df["gps_0.epv"], errors="coerce")
    df["gps_0.satellites_visible"] = pd.to_numeric(df["gps_0.satellites_visible"], errors="coerce")

    # Fill NaN values which might have been created during conversion to numeric
    df.fillna(0, inplace=True)

    # Feature Engineering
    # Calculate deltas for latitude, longitude, and altitude
    df["delta_lat"] = df["location.global_frame.lat"].diff().fillna(0)
    df["delta_lon"] = df["location.global_frame.lon"].diff().fillna(0)
    df["delta_alt"] = df["location.global_frame.alt"].diff().fillna(0)

    # Calculate Euclidean distance between successive GPS points
    df["distance"] = np.sqrt(df["delta_lat"] ** 2 + df["delta_lon"] ** 2 + df["delta_alt"] ** 2)

    # Load the scaler
    scaler = joblib.load("./drone_ips/models/scaler.pkl")

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


def make_prediction(model, current_data: dict) -> dict:
    """Make a prediction using the ML model.

    Parameters
    ----------
    model : object
        The loaded ML model.
    current_data : dict
        The current data from the vehicle.

    Returns
    -------
    dict
        The prediction result.
    """
    # Preprocess the data
    processed_data = preprocess_vehicle_data(current_data)

    # Make prediction
    prediction = model.predict(processed_data)

    # Return the prediction result in a dictionary
    return {"prediction": 1 if int(prediction[0]) == 1 else 0}


def main(model):
    """The main function for the monitor.

    Parameters
    ----------
    model : object
        The loaded ML model.
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
            response = make_prediction(model, current_data)
            # Send back a verdict
            verdict = response["prediction"]
            socket.send(bytes(str(verdict), "utf-8"))
        except KeyboardInterrupt:
            break
        except zmq.error.Again:
            continue


if __name__ == "__main__":
    # Load the model once at the module level
    model = load_model("./drone_ips/models/one_class_svm_model.pkl")
    main(model)
