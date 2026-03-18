"""Distance, elevation and objective error metrics for TrailMax."""

import math

import numpy as np


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute the Haversine distance between two lat/lon points.

    Args:
        lat1: Latitude of point 1 in decimal degrees.
        lon1: Longitude of point 1 in decimal degrees.
        lat2: Latitude of point 2 in decimal degrees.
        lon2: Longitude of point 2 in decimal degrees.

    Returns:
        Distance in kilometres.
    """
    earth_radius_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + (
        math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return earth_radius_km * c


def total_distance_km(geometry: list[tuple[float, float]]) -> float:
    """Compute the total distance of a route.

    Args:
        geometry: Ordered list of (latitude, longitude) pairs.

    Returns:
        Total route distance in kilometres.
    """
    if len(geometry) < 2:
        return 0.0
    total = 0.0
    for i in range(len(geometry) - 1):
        lat1, lon1 = geometry[i]
        lat2, lon2 = geometry[i + 1]
        total += haversine_distance(lat1, lon1, lat2, lon2)
    return total


def compute_elevation_gain_m(elevations: list[float]) -> float:
    """Compute total elevation gain from a sequence of elevation samples.

    Args:
        elevations: Elevation values in metres, ordered along the route.

    Returns:
        Sum of all positive elevation differences in metres.
    """
    if len(elevations) < 2:
        return 0.0
    arr = np.array(elevations)
    diffs = np.diff(arr)
    return float(np.sum(diffs[diffs > 0]))


def compute_grade_pct(
    elev1: float,
    elev2: float,
    distance_m: float,
) -> float:
    """Compute the grade percentage between two adjacent points.

    Args:
        elev1: Elevation at the start point in metres.
        elev2: Elevation at the end point in metres.
        distance_m: Horizontal distance between the points in metres.

    Returns:
        Grade as a percentage; positive values indicate uphill.
    """
    if distance_m == 0.0:
        return 0.0
    return 100.0 * (elev2 - elev1) / distance_m


def objective_error(  # noqa: PLR0913
    achieved_distance_km: float,
    achieved_elevation_m: float,
    target_distance_km: float,
    target_elevation_m: float,
    *,
    distance_weight: float = 1.0,
    elevation_weight: float = 1.0,
) -> float:
    """Compute a weighted mean absolute percentage error for a candidate route.

    The error combines normalised distance and elevation gain errors,
    weighted by ``distance_weight`` and ``elevation_weight`` respectively.
    When ``target_elevation_m`` is zero the elevation term is omitted.

    Args:
        achieved_distance_km: Actual route distance in kilometres.
        achieved_elevation_m: Actual elevation gain in metres.
        target_distance_km: Desired route distance in kilometres.
        target_elevation_m: Desired elevation gain in metres.
        distance_weight: Relative weight for the distance error term.
        elevation_weight: Relative weight for the elevation error term.

    Returns:
        Weighted MAPE value; 0.0 represents a perfect match.
    """
    dist_error = abs(achieved_distance_km - target_distance_km) / max(
        target_distance_km, 1e-9
    )
    if target_elevation_m > 0.0:
        elev_error = abs(achieved_elevation_m - target_elevation_m) / target_elevation_m
    else:
        elev_error = 0.0
    total_weight = distance_weight + elevation_weight
    return (distance_weight * dist_error + elevation_weight * elev_error) / total_weight
