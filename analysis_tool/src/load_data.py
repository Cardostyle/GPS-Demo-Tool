from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import AREA_FOLDERS, ENVIRONMENT_ALIASES, EXPECTED_OFFSET_SECONDS
from src.geo_utils import distance_meters, is_valid_lat_lon


def normalize_environment(value: Any) -> str:
    if value is None:
        return "unbekannt"

    text = str(value).strip()
    lowered = text.lower()
    return ENVIRONMENT_ALIASES.get(lowered, text)


def parse_offset_seconds(value: Any) -> int | None:
    if value is None:
        return None
    try:
        # Unterstützt sowohl JSON-Zahlen als auch Strings wie "90" oder "90.0".
        return int(float(value))
    except (TypeError, ValueError):
        return None


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
    ref_alt = reference.get("altitude")

    has_valid_reference = is_valid_lat_lon(ref_lat, ref_lon)
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

    photo_lat, photo_lon = parse_photo_lat_lon(data.get("photoMetadata"))
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
        "photoLatitude": photo_lat if has_photo_geotag else None,
        "photoLongitude": photo_lon if has_photo_geotag else None,
        "hasPhotoGeotag": has_photo_geotag,
        "photoOriginalDate": (data.get("photoMetadata") or {}).get("originalDate"),
    }

    measurement_rows: list[dict] = []

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

        distance_to_reference = None
        if has_valid_reference:
            distance_to_reference = distance_meters(lat, lon, ref_lat, ref_lon)

        distance_to_photo_geotag = None
        if has_photo_geotag:
            distance_to_photo_geotag = distance_meters(lat, lon, photo_lat, photo_lon)

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
            "altitude": m.get("altitude"),
            "timestampUtc": m.get("timestampUtc"),
            "measuredAtUtc": m.get("measuredAtUtc"),
            "androidAccuracyMeters": m.get("locationAccuracyMeters"),
            "altitudeAccuracyMeters": m.get("altitudeAccuracyMeters"),
            "heading": m.get("heading"),
            "speed": m.get("speed"),
            "visibleSatellites": m.get("visibleSatellites"),
            "usedSatellites": m.get("usedSatellites"),
            "cn0DbHz": m.get("cn0DbHz"),
            "hdop": m.get("hdop"),
            "pdop": m.get("pdop"),
            "vdop": m.get("vdop"),
            "referenceLatitude": float(ref_lat) if has_valid_reference else None,
            "referenceLongitude": float(ref_lon) if has_valid_reference else None,
            "hasValidReference": has_valid_reference,
            "distanceToReferenceMeters": distance_to_reference,
            "photoLatitude": photo_lat if has_photo_geotag else None,
            "photoLongitude": photo_lon if has_photo_geotag else None,
            "hasPhotoGeotag": has_photo_geotag,
            "distanceToPhotoGeotagMeters": distance_to_photo_geotag,
        })

    return experiment_row, measurement_rows, issues


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
