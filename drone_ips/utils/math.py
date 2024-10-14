"""Mathematical functions for drone_ips."""

import math

import numpy as np


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the Haversine distance between two GPS coordinates in meters.

    Parameters
    ----------
    lat1 : float
        Latitude of the first GPS coordinate in degrees.
    lon1 : float
        Longitude of the first GPS coordinate in degrees.
    lat2 : float
        Latitude of the second GPS coordinate in degrees.
    lon2 : float
        Longitude of the second GPS coordinate in degrees.

    Returns
    -------
    float
        The Haversine distance between the two GPS coordinates in meters.
    """
    R = 6371000  # Radius of the Earth in meters

    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Differences in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c  # Output distance in meters
    return distance


def add_gaussian_noise(lat: float, lon: float, sigma: float = 0.0001):
    """Add Gaussian noise to latitude and longitude values.

    Parameters
    ----------
    lat : float
        The original latitude.
    lon : float
        The original longitude.
    sigma : float, optional
        The standard deviation for Gaussian noise, by default .0001 (minor noise).

    Returns
    -------
    noisy_lat: float
        The latitude with added noise.
    noisy_lon: float
        The longitude with added noise.
    """
    noisy_lat = lat + np.random.normal(0, sigma)
    noisy_lon = lon + np.random.normal(0, sigma)
    return noisy_lat, noisy_lon
