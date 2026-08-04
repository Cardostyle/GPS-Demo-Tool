from __future__ import annotations

import math
from typing import Any, Optional

from geopy.distance import geodesic


def is_valid_lat_lon(latitude: Any, longitude: Any) -> bool:
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return False

    return -90 <= lat <= 90 and -180 <= lon <= 180


def optional_float(value: Any) -> Optional[float]:
    """Konvertiert optionale JSON-/EXIF-Zahlen robust in float.

    Unterstützt normale Zahlen, Dezimalstrings, Dezimalkomma und rationale
    EXIF-Werte wie ``14899/100``.
    """
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if "/" in text:
            numerator, denominator, *rest = text.split("/")
            if rest:
                return None
            try:
                denominator_value = float(denominator.replace(",", "."))
                if denominator_value == 0:
                    return None
                return float(numerator.replace(",", ".")) / denominator_value
            except (TypeError, ValueError):
                return None
        value = text.replace(",", ".")

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    return number if math.isfinite(number) else None


def distance_meters(lat1: Any, lon1: Any, lat2: Any, lon2: Any) -> Optional[float]:
    if not is_valid_lat_lon(lat1, lon1) or not is_valid_lat_lon(lat2, lon2):
        return None

    return float(geodesic((float(lat1), float(lon1)), (float(lat2), float(lon2))).meters)


def distance_3d_meters(
    lat1: Any,
    lon1: Any,
    altitude1: Any,
    lat2: Any,
    lon2: Any,
    altitude2: Any,
) -> Optional[float]:
    """Berechnet eine lokale 3D-Distanz aus horizontaler Geodäsie und Höhendifferenz.

    Für die hier auftretenden kurzen Distanzen ist die Kombination aus der
    geodätischen 2D-Distanz und der vertikalen Differenz über den Satz des
    Pythagoras eine passende und gut interpretierbare Näherung.
    """
    horizontal_distance = distance_meters(lat1, lon1, lat2, lon2)
    altitude_1 = optional_float(altitude1)
    altitude_2 = optional_float(altitude2)

    if horizontal_distance is None or altitude_1 is None or altitude_2 is None:
        return None

    return math.hypot(horizontal_distance, altitude_1 - altitude_2)


def mean_coordinate(rows):
    valid = rows.dropna(subset=["latitude", "longitude"])
    if valid.empty:
        return None, None
    return valid["latitude"].mean(), valid["longitude"].mean()
