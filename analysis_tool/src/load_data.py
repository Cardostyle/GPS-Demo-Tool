from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import AREA_FOLDERS, ENVIRONMENT_ALIASES, EXPECTED_OFFSET_SECONDS, REFERENCE_DISTANCE_WARNING_METERS
from src.geo_utils import distance_3d_meters, distance_meters, is_valid_lat_lon, optional_float


def normalize_environment(value: Any) -> str:
    if value is None:
        return "unbekannt"

    text = str(value).strip()
    lowered = text.lower()
    return ENVIRONMENT_ALIASES.get(lowered, text)


def parse_offset_seconds(value: Any) -> int | None:
    number = optional_float(value)
    if number is None:
        return None
    return int(number)


def parse_photo_lat_lon(photo_metadata: dict | None) -> tuple[float | None, float | None]:
    if not photo_metadata:
        return None, None

    lat_long = photo_metadata.get("latLong")
    if lat_long is None:
        return None, None

    # Unterstützt mehrere mögliche Formate:
    # {"latitude": 51.1, "longitude": 12.6}
    # [51.1, 12.6]
    # "51.1,12.6"
    if isinstance(lat_long, dict):
        lat = lat_long.get("latitude") or lat_long.get("lat")
        lon = lat_long.get("longitude") or lat_long.get("lon") or lat_long.get("lng")
        if is_valid_lat_lon(lat, lon):
            return float(lat), float(lon)

    if isinstance(lat_long, (list, tuple)) and len(lat_long) >= 2:
        lat, lon = lat_long[0], lat_long[1]
        if is_valid_lat_lon(lat, lon):
            return float(lat), float(lon)

    if isinstance(lat_long, str) and "," in lat_long:
        parts = [part.strip() for part in lat_long.split(",")]
        if len(parts) >= 2 and is_valid_lat_lon(parts[0], parts[1]):
            return float(parts[0]), float(parts[1])

    return None, None


def parse_photo_altitude(photo_metadata: dict | None) -> float | None:
    """Liest die Foto-Höhe aus direkten Feldern oder EXIF-GPSAltitude.

    ``GPSAltitudeRef=1`` kennzeichnet eine Höhe unterhalb des Meeresspiegels.
    Rationale EXIF-Werte wie ``14899/100`` werden unterstützt.
    """
    if not photo_metadata:
        return None

    direct_altitude = optional_float(photo_metadata.get("altitude"))
    if direct_altitude is not None:
        return direct_altitude

    lat_long = photo_metadata.get("latLong")
    if isinstance(lat_long, dict):
        lat_long_altitude = optional_float(lat_long.get("altitude") or lat_long.get("alt"))
        if lat_long_altitude is not None:
            return lat_long_altitude

    attributes = photo_metadata.get("attributes") or {}
    altitude = optional_float(attributes.get("GPSAltitude"))
    if altitude is None:
        return None

    altitude_ref = optional_float(attributes.get("GPSAltitudeRef"))
    if altitude_ref == 1:
        altitude = -abs(altitude)

    return altitude


def load_json_file(path: Path, area_name: str) -> tuple[dict, list[dict], list[dict]]:
    issues: list[dict] = []

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    experiment_id = data.get("id", path.stem)
    environment = normalize_environment(data.get("environmentType"))
    device_model = data.get("deviceModel")
    created_at = data.get("createdAtUtc")
    note = data.get("note")

    reference = data.get("referenceData") or {}
    ref_lat = reference.get("latitude")
    ref_lon = reference.get("longitude")
    ref_alt = optional_float(reference.get("altitude"))

    has_valid_reference = is_valid_lat_lon(ref_lat, ref_lon)
    has_reference_altitude = ref_alt is not None
    if reference and not has_valid_reference:
        issues.append({
            "file": str(path),
            "experimentId": experiment_id,
            "issue": "Ungültige Referenzkoordinaten",
            "details": f"latitude={ref_lat}, longitude={ref_lon}",
        })
    elif not reference:
        issues.append({
            "file": str(path),
            "experimentId": experiment_id,
            "issue": "Keine Referenzdaten",
            "details": "referenceData fehlt oder ist null",
        })

    if has_valid_reference and not has_reference_altitude:
        issues.append({
            "file": str(path),
            "experimentId": experiment_id,
            "issue": "Keine gültige Referenzhöhe",
            "details": f"referenceData.altitude={reference.get('altitude')}",
        })

    photo_metadata = data.get("photoMetadata")
    photo_lat, photo_lon = parse_photo_lat_lon(photo_metadata)
    photo_alt = parse_photo_altitude(photo_metadata)
    has_photo_geotag = is_valid_lat_lon(photo_lat, photo_lon)
    if not has_photo_geotag:
        issues.append({
            "file": str(path),
            "experimentId": experiment_id,
            "issue": "Kein gültiger Foto-Geotag",
            "details": "photoMetadata.latLong fehlt, ist null oder ungültig",
        })

    measurements = data.get("measurements") or []
    offsets_found = {parse_offset_seconds(m.get("offsetSeconds")) for m in measurements}
    offsets_found.discard(None)
    missing_offsets = [o for o in EXPECTED_OFFSET_SECONDS if o not in offsets_found]
    if missing_offsets:
        issues.append({
            "file": str(path),
            "experimentId": experiment_id,
            "issue": "Fehlende Zeitabstände",
            "details": ",".join(map(str, missing_offsets)),
        })

    photo_distance_to_reference = None
    photo_distance_to_reference_3d = None
    photo_altitude_difference = None
    photo_absolute_altitude_difference = None
    if has_photo_geotag and has_valid_reference:
        photo_distance_to_reference = distance_meters(photo_lat, photo_lon, ref_lat, ref_lon)
        photo_distance_to_reference_3d = distance_3d_meters(
            photo_lat,
            photo_lon,
            photo_alt,
            ref_lat,
            ref_lon,
            ref_alt,
        )
        if photo_alt is not None and ref_alt is not None:
            photo_altitude_difference = photo_alt - ref_alt
            photo_absolute_altitude_difference = abs(photo_altitude_difference)

    experiment_row = {
        "file": str(path),
        "experimentId": experiment_id,
        "area": area_name,
        "environmentType": environment,
        "deviceModel": device_model,
        "androidVersion": data.get("androidVersion"),
        "createdAtUtc": created_at,
        "note": note,
        "referenceLatitude": float(ref_lat) if has_valid_reference else None,
        "referenceLongitude": float(ref_lon) if has_valid_reference else None,
        "referenceAltitude": ref_alt,
        "hasValidReference": has_valid_reference,
        "hasReferenceAltitude": has_reference_altitude,
        "photoLatitude": photo_lat if has_photo_geotag else None,
        "photoLongitude": photo_lon if has_photo_geotag else None,
        "photoAltitude": photo_alt,
        "hasPhotoGeotag": has_photo_geotag,
        "distanceToPhotoGeotagMeters": photo_distance_to_reference,
        "distanceToPhotoGeotag3dMeters": photo_distance_to_reference_3d,
        "photoAltitudeDifferenceToReferenceMeters": photo_altitude_difference,
        "absolutePhotoAltitudeDifferenceToReferenceMeters": photo_absolute_altitude_difference,
        "photoOriginalDate": (photo_metadata or {}).get("originalDate"),
    }

    measurement_rows: list[dict] = []
    reference_distances: list[float] = []

    for m in measurements:
        lat = m.get("latitude")
        lon = m.get("longitude")

        if not is_valid_lat_lon(lat, lon):
            issues.append({
                "file": str(path),
                "experimentId": experiment_id,
                "issue": "Ungültige Messkoordinate",
                "details": f"measurementId={m.get('id')}, latitude={lat}, longitude={lon}",
            })
            continue

        altitude = optional_float(m.get("altitude"))
        altitude_accuracy = optional_float(m.get("altitudeAccuracyMeters"))

        distance_to_reference = None
        distance_to_reference_3d = None
        altitude_difference_to_reference = None
        absolute_altitude_difference_to_reference = None
        if has_valid_reference:
            distance_to_reference = distance_meters(lat, lon, ref_lat, ref_lon)
            if distance_to_reference is not None:
                reference_distances.append(distance_to_reference)

            distance_to_reference_3d = distance_3d_meters(
                lat,
                lon,
                altitude,
                ref_lat,
                ref_lon,
                ref_alt,
            )
            if altitude is not None and ref_alt is not None:
                altitude_difference_to_reference = altitude - ref_alt
                absolute_altitude_difference_to_reference = abs(altitude_difference_to_reference)

        offset_seconds = parse_offset_seconds(m.get("offsetSeconds"))

        measurement_rows.append({
            "file": str(path),
            "experimentId": experiment_id,
            "measurementId": m.get("id"),
            "area": area_name,
            "environmentType": environment,
            "deviceModel": device_model,
            "createdAtUtc": created_at,
            "offsetSeconds": offset_seconds,
            "sequenceNumber": m.get("sequenceNumber"),
            "latitude": float(lat),
            "longitude": float(lon),
            "altitude": altitude,
            "timestampUtc": m.get("timestampUtc"),
            "measuredAtUtc": m.get("measuredAtUtc"),
            "androidAccuracyMeters": optional_float(m.get("locationAccuracyMeters")),
            "altitudeAccuracyMeters": altitude_accuracy,
            "heading": optional_float(m.get("heading")),
            "speed": optional_float(m.get("speed")),
            "visibleSatellites": optional_float(m.get("visibleSatellites")),
            "usedSatellites": optional_float(m.get("usedSatellites")),
            "cn0DbHz": optional_float(m.get("cn0DbHz")),
            "hdop": optional_float(m.get("hdop")),
            "pdop": optional_float(m.get("pdop")),
            "vdop": optional_float(m.get("vdop")),
            "referenceLatitude": float(ref_lat) if has_valid_reference else None,
            "referenceLongitude": float(ref_lon) if has_valid_reference else None,
            "referenceAltitude": ref_alt,
            "hasValidReference": has_valid_reference,
            "hasReferenceAltitude": has_reference_altitude,
            "distanceToReferenceMeters": distance_to_reference,
            "distanceToReference3dMeters": distance_to_reference_3d,
            "altitudeDifferenceToReferenceMeters": altitude_difference_to_reference,
            "absoluteAltitudeDifferenceToReferenceMeters": absolute_altitude_difference_to_reference,
            "photoLatitude": photo_lat if has_photo_geotag else None,
            "photoLongitude": photo_lon if has_photo_geotag else None,
            "photoAltitude": photo_alt,
            "hasPhotoGeotag": has_photo_geotag,
            "distanceToPhotoGeotagMeters": photo_distance_to_reference,
            "distanceToPhotoGeotag3dMeters": photo_distance_to_reference_3d,
            "photoAltitudeDifferenceToReferenceMeters": photo_altitude_difference,
            "absolutePhotoAltitudeDifferenceToReferenceMeters": photo_absolute_altitude_difference,
        })

    if reference_distances:
        average_distance_to_reference = sum(reference_distances) / len(reference_distances)
        if average_distance_to_reference > REFERENCE_DISTANCE_WARNING_METERS:
            details = (
                f"averageDistanceToReferenceMeters={average_distance_to_reference:.3f}, "
                f"thresholdMeters={REFERENCE_DISTANCE_WARNING_METERS:g}, "
                f"measurementCount={len(reference_distances)}, "
                f"maxDistanceToReferenceMeters={max(reference_distances):.3f}, "
                f"referenceLatitude={ref_lat}, referenceLongitude={ref_lon}"
            )
            issues.append({
                "file": str(path),
                "experimentId": experiment_id,
                "issue": "Durchschnittlicher Abstand mehr als 100 m vom Referenzpunkt entfernt",
                "details": details,
            })

    return experiment_row, measurement_rows, issues


def reference_point_key(row: dict) -> tuple[float | None, float | None, float | str | None] | None:
    if not row.get("hasValidReference"):
        return None

    altitude = row.get("referenceAltitude")
    try:
        altitude_key = round(float(altitude), 3) if altitude is not None else None
    except (TypeError, ValueError):
        altitude_key = str(altitude)

    return (
        round(float(row["referenceLatitude"]), 7),
        round(float(row["referenceLongitude"]), 7),
        altitude_key,
    )


def load_all_experiments(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    experiment_rows: list[dict] = []
    measurement_rows: list[dict] = []
    issue_rows: list[dict] = []

    for folder_name, area_name in AREA_FOLDERS.items():
        folder = data_dir / folder_name
        if not folder.exists():
            issue_rows.append({
                "file": str(folder),
                "experimentId": None,
                "issue": "Ordner fehlt",
                "details": f"Erwarteter Ordner: {folder}",
            })
            continue

        for path in sorted(folder.rglob("*.json")):
            try:
                experiment, measurements, issues = load_json_file(path, area_name)
                experiment_rows.append(experiment)
                measurement_rows.extend(measurements)
                issue_rows.extend(issues)
            except Exception as exc:
                issue_rows.append({
                    "file": str(path),
                    "experimentId": None,
                    "issue": "JSON konnte nicht geladen werden",
                    "details": repr(exc),
                })

    measurements_df = pd.DataFrame(measurement_rows)
    experiments_df = pd.DataFrame(experiment_rows)
    issues_df = pd.DataFrame(issue_rows)

    return measurements_df, experiments_df, issues_df
