from __future__ import annotations

from typing import Optional, Any

from geopy.distance import geodesic


def is_valid_lat_lon(latitude: Any, longitude: Any) -> bool:
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return False

    return -90 <= lat <= 90 and -180 <= lon <= 180


def distance_meters(lat1: Any, lon1: Any, lat2: Any, lon2: Any) -> Optional[float]:
    if not is_valid_lat_lon(lat1, lon1) or not is_valid_lat_lon(lat2, lon2):
        return None

    return float(geodesic((float(lat1), float(lon1)), (float(lat2), float(lon2))).meters)


def mean_coordinate(rows):
    valid = rows.dropna(subset=["latitude", "longitude"])
    if valid.empty:
        return None, None
    return valid["latitude"].mean(), valid["longitude"].mean()
