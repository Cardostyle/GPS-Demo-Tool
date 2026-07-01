from __future__ import annotations

from pathlib import Path

import folium
import pandas as pd

from src.geo_utils import is_valid_lat_lon


def _center_for_area(df: pd.DataFrame) -> tuple[float, float]:
    valid = df.dropna(subset=["latitude", "longitude"])
    if valid.empty:
        return 51.0, 10.0
    return float(valid["latitude"].mean()), float(valid["longitude"].mean())


def _add_measurement_points(m: folium.Map, df: pd.DataFrame) -> None:
    for _, row in df.iterrows():
        popup = (
            f"<b>Messung</b><br>"
            f"Experiment: {row.get('experimentId')}<br>"
            f"Umgebung: {row.get('environmentType')}<br>"
            f"Gerät: {row.get('deviceModel')}<br>"
            f"Zeitabstand: {row.get('offsetSeconds')} s<br>"
            f"Android Accuracy: {row.get('androidAccuracyMeters')} m<br>"
            f"Abweichung Referenz: {row.get('distanceToReferenceMeters')} m"
        )

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=5,
            popup=folium.Popup(popup, max_width=350),
            tooltip=f"{row.get('environmentType')} | {row.get('offsetSeconds')} s",
            color="blue",
            fill=True,
            fill_opacity=0.7,
        ).add_to(m)


def _add_reference_points(m: folium.Map, df: pd.DataFrame) -> None:
    refs = (
        df.dropna(subset=["referenceLatitude", "referenceLongitude"])
        .drop_duplicates(subset=["experimentId", "referenceLatitude", "referenceLongitude"])
    )

    for _, row in refs.iterrows():
        if not is_valid_lat_lon(row["referenceLatitude"], row["referenceLongitude"]):
            continue

        popup = (
            f"<b>Referenzpunkt</b><br>"
            f"Experiment: {row.get('experimentId')}<br>"
            f"Umgebung: {row.get('environmentType')}"
        )

        folium.Marker(
            location=[row["referenceLatitude"], row["referenceLongitude"]],
            popup=folium.Popup(popup, max_width=300),
            tooltip="Referenzpunkt",
            icon=folium.Icon(color="green", icon="flag"),
        ).add_to(m)


def _add_photo_geotags(m: folium.Map, df: pd.DataFrame) -> None:
    photos = (
        df.dropna(subset=["photoLatitude", "photoLongitude"])
        .drop_duplicates(subset=["experimentId", "photoLatitude", "photoLongitude"])
    )

    for _, row in photos.iterrows():
        popup = (
            f"<b>Foto-Geotag</b><br>"
            f"Experiment: {row.get('experimentId')}<br>"
            f"Umgebung: {row.get('environmentType')}<br>"
            f"Gerät: {row.get('deviceModel')}"
        )

        folium.Marker(
            location=[row["photoLatitude"], row["photoLongitude"]],
            popup=folium.Popup(popup, max_width=300),
            tooltip="Foto-Geotag",
            icon=folium.Icon(color="purple", icon="camera"),
        ).add_to(m)


def _add_mean_points(m: folium.Map, df: pd.DataFrame) -> None:
    grouped = df.groupby(["experimentId", "area", "environmentType", "deviceModel"], dropna=False)

    for (experiment_id, area, environment, device), group in grouped:
        center_lat = group["latitude"].mean()
        center_lon = group["longitude"].mean()

        popup = (
            f"<b>Mittelwert der Messpunkte</b><br>"
            f"Experiment: {experiment_id}<br>"
            f"Umgebung: {environment}<br>"
            f"Gerät: {device}<br>"
            f"Anzahl Messungen: {len(group)}"
        )

        folium.Marker(
            location=[center_lat, center_lon],
            popup=folium.Popup(popup, max_width=300),
            tooltip="Mittelwert",
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(m)


def create_single_map(df: pd.DataFrame, output_path: Path) -> None:
    center = _center_for_area(df)
    m = folium.Map(location=center, zoom_start=16, tiles="OpenStreetMap")

    _add_measurement_points(m, df)
    _add_reference_points(m, df)
    _add_photo_geotags(m, df)
    _add_mean_points(m, df)

    folium.LayerControl().add_to(m)
    m.save(output_path)


def create_maps(measurements_df: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # getrennte Karten je Gebiet.
    for area, group in measurements_df.groupby("area", dropna=False):
        safe_area = str(area).lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss").replace(" ", "_")
        create_single_map(group, output_dir / f"map_{safe_area}.html")
