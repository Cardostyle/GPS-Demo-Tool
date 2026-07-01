from __future__ import annotations

import json
from pathlib import Path

import folium
import pandas as pd
from branca.element import MacroElement, Template

from src.geo_utils import is_valid_lat_lon


def _center_for_area(df: pd.DataFrame) -> tuple[float, float]:
    valid = df.dropna(subset=["latitude", "longitude"])
    if valid.empty:
        return 51.0, 10.0
    return float(valid["latitude"].mean()), float(valid["longitude"].mean())


def _experiment_key(value) -> str:
    if pd.isna(value):
        return ""
    return str(value)


def _add_measurement_points(m: folium.Map, df: pd.DataFrame) -> list[dict[str, str]]:
    measurement_layers: list[dict[str, str]] = []

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

        marker = folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=5,
            popup=folium.Popup(popup, max_width=350),
            tooltip=f"{row.get('environmentType')} | {row.get('offsetSeconds')} s",
            color="blue",
            fill=True,
            fill_opacity=0.7,
        ).add_to(m)

        measurement_layers.append(
            {
                "layer": marker.get_name(),
                "experimentId": _experiment_key(row.get("experimentId")),
            }
        )

    return measurement_layers


def _add_reference_points(m: folium.Map, df: pd.DataFrame) -> list[dict[str, str]]:
    reference_layers: list[dict[str, str]] = []

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

        marker = folium.Marker(
            location=[row["referenceLatitude"], row["referenceLongitude"]],
            popup=folium.Popup(popup, max_width=300),
            tooltip="Referenzpunkt",
            icon=folium.Icon(color="green", icon="flag"),
        ).add_to(m)

        reference_layers.append(
            {
                "layer": marker.get_name(),
                "experimentId": _experiment_key(row.get("experimentId")),
            }
        )

    return reference_layers


def _add_photo_geotags(m: folium.Map, df: pd.DataFrame) -> list[dict[str, str]]:
    photo_layers: list[dict[str, str]] = []

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

        marker = folium.Marker(
            location=[row["photoLatitude"], row["photoLongitude"]],
            popup=folium.Popup(popup, max_width=300),
            tooltip="Foto-Geotag",
            icon=folium.Icon(color="purple", icon="camera"),
        ).add_to(m)

        photo_layers.append(
            {
                "layer": marker.get_name(),
                "experimentId": _experiment_key(row.get("experimentId")),
            }
        )

    return photo_layers


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


def _add_reference_click_highlighting(
    m: folium.Map,
    measurement_layers: list[dict[str, str]],
    photo_layers: list[dict[str, str]],
    reference_layers: list[dict[str, str]],
) -> None:
    measurement_items = ",\n".join(
        (
            "{"
            f"layer: {item['layer']}, "
            f"experimentId: {json.dumps(item['experimentId'])}"
            "}"
        )
        for item in measurement_layers
    )

    photo_items = ",\n".join(
        (
            "{"
            f"layer: {item['layer']}, "
            f"experimentId: {json.dumps(item['experimentId'])}"
            "}"
        )
        for item in photo_layers
    )

    reference_bindings = "\n".join(
        (
            f"{item['layer']}.on('click', function() {{ "
            f"highlightExperiment({json.dumps(item['experimentId'])}); "
            f"}});"
        )
        for item in reference_layers
    )

    script = f"""
        var measurementLayers = [
            {measurement_items}
        ];

        var photoLayers = [
            {photo_items}
        ];

        var defaultPhotoIcon = L.AwesomeMarkers.icon({{
            icon: 'camera',
            markerColor: 'purple',
            prefix: 'glyphicon',
            iconColor: 'white'
        }});

        var highlightedPhotoIcon = L.AwesomeMarkers.icon({{
            icon: 'camera',
            markerColor: 'orange',
            prefix: 'glyphicon',
            iconColor: 'white'
        }});

        function highlightExperiment(experimentId) {{
            measurementLayers.forEach(function(item) {{
                if (item.experimentId === experimentId) {{
                    item.layer.setStyle({{
                        color: 'orange',
                        fillColor: 'orange',
                        fillOpacity: 0.95,
                        weight: 4
                    }});
                    item.layer.bringToFront();
                }} else {{
                    item.layer.setStyle({{
                        color: 'blue',
                        fillColor: 'blue',
                        fillOpacity: 0.7,
                        weight: 3
                    }});
                }}
            }});

            photoLayers.forEach(function(item) {{
                if (item.experimentId === experimentId) {{
                    item.layer.setIcon(highlightedPhotoIcon);
                    item.layer.setZIndexOffset(1000);
                }} else {{
                    item.layer.setIcon(defaultPhotoIcon);
                    item.layer.setZIndexOffset(0);
                }}
            }});
        }}

        {reference_bindings}
    """

    macro = MacroElement()
    macro._template = Template(
        f"""
        {{% macro script(this, kwargs) %}}
        {script}
        {{% endmacro %}}
        """
    )

    m.add_child(macro)


def create_single_map(df: pd.DataFrame, output_path: Path) -> None:
    center = _center_for_area(df)
    m = folium.Map(location=center, zoom_start=16, tiles="OpenStreetMap")

    measurement_layers = _add_measurement_points(m, df)
    reference_layers = _add_reference_points(m, df)
    photo_layers = _add_photo_geotags(m, df)
    _add_mean_points(m, df)

    _add_reference_click_highlighting(m, measurement_layers, photo_layers, reference_layers)

    folium.LayerControl().add_to(m)
    m.save(output_path)


def create_maps(measurements_df: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # getrennte Karten je Gebiet.
    for area, group in measurements_df.groupby("area", dropna=False):
        safe_area = str(area).lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss").replace(" ", "_")
        create_single_map(group, output_dir / f"map_{safe_area}.html")