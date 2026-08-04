from __future__ import annotations

import pandas as pd

from src.config import AREA_FOLDERS, FOREST_ENVIRONMENTS, OPEN_ENVIRONMENTS, URBAN_ENVIRONMENTS
from src.geo_utils import distance_meters


GNSS_QUALITY_METRICS = {
    "visibleSatellites": {
        "mean": "mittlereSichtbareSatelliten",
        "available": "vorhandeneSichtbareSatellitenWerte",
        "missing": "fehlendeSichtbareSatellitenWerte",
    },
    "usedSatellites": {
        "mean": "mittlereGenutzteSatelliten",
        "available": "vorhandeneGenutzteSatellitenWerte",
        "missing": "fehlendeGenutzteSatellitenWerte",
    },
    "cn0DbHz": {
        "mean": "mittlererCn0DbHz",
        "available": "vorhandeneCn0Werte",
        "missing": "fehlendeCn0Werte",
    },
    "hdop": {
        "mean": "mittlererHdop",
        "available": "vorhandeneHdopWerte",
        "missing": "fehlendeHdopWerte",
    },
    "pdop": {
        "mean": "mittlererPdop",
        "available": "vorhandenePdopWerte",
        "missing": "fehlendePdopWerte",
    },
    "vdop": {
        "mean": "mittlererVdop",
        "available": "vorhandeneVdopWerte",
        "missing": "fehlendeVdopWerte",
    },
    "altitude": {
        "mean": "mittlereAltitudeMeter",
        "available": "vorhandeneAltitudeWerte",
        "missing": "fehlendeAltitudeWerte",
    },
    "altitudeAccuracyMeters": {
        "mean": "mittlereHoehengenauigkeitMeter",
        "available": "vorhandeneHoehengenauigkeitsWerte",
        "missing": "fehlendeHoehengenauigkeitsWerte",
    },
    "altitudeDifferenceToReferenceMeters": {
        "mean": "mittlereHoehenabweichungMeter",
        "available": "vorhandeneHoehenabweichungsWerte",
        "missing": "fehlendeHoehenabweichungsWerte",
    },
    "absoluteAltitudeDifferenceToReferenceMeters": {
        "mean": "mittlereAbsoluteHoehenabweichungMeter",
        "available": "vorhandeneAbsoluteHoehenabweichungsWerte",
        "missing": "fehlendeAbsoluteHoehenabweichungsWerte",
    },
    "distanceToReference3dMeters": {
        "mean": "mittlere3dEntfernungZumReferenzpunktMeter",
        "available": "vorhandene3dEntfernungsWerte",
        "missing": "fehlende3dEntfernungsWerte",
    },
}


HEIGHT_CONTEXTS = {
    "distanceToReferenceMeters": {
        "altitude": "altitude",
        "reference_altitude": "referenceAltitude",
        "difference": "altitudeDifferenceToReferenceMeters",
        "absolute_difference": "absoluteAltitudeDifferenceToReferenceMeters",
        "accuracy": "altitudeAccuracyMeters",
        "distance_3d": "distanceToReference3dMeters",
        "horizontal_accuracy": "androidAccuracyMeters",
    },
    "distanceToPhotoGeotagMeters": {
        "altitude": "photoAltitude",
        "reference_altitude": "referenceAltitude",
        "difference": "photoAltitudeDifferenceToReferenceMeters",
        "absolute_difference": "absolutePhotoAltitudeDifferenceToReferenceMeters",
        "accuracy": None,
        "distance_3d": "distanceToPhotoGeotag3dMeters",
        "horizontal_accuracy": None,
    },
}


BASE_SUMMARY_COLUMNS = [
    "anzahlMessungen",
    "mittelwertMeter",
    "medianMeter",
    "standardabweichungMeter",
    "minMeter",
    "maxMeter",
    "mittlereAndroidAccuracyMeter",
    "mittlereSichtbareSatelliten",
    "mittlereGenutzteSatelliten",
    "mittlererCn0DbHz",
    "mittlererHdop",
    "mittlererPdop",
    "mittlererVdop",
]


HEIGHT_SUMMARY_COLUMNS = [
    "mittlereAltitudeMeter",
    "medianAltitudeMeter",
    "mittlereReferenzAltitudeMeter",
    "mittlereHoehenabweichungMeter",
    "mittlereAbsoluteHoehenabweichungMeter",
    "medianAbsoluteHoehenabweichungMeter",
    "standardabweichungHoehenabweichungMeter",
    "mittlereHoehengenauigkeitMeter",
    "mittlere3dEntfernungMeter",
    "median3dEntfernungMeter",
    "min3dEntfernungMeter",
    "max3dEntfernungMeter",
    "vorhandeneHoehenWerte",
    "fehlendeHoehenWerte",
    "vorhandene3dEntfernungen",
    "fehlende3dEntfernungen",
    "anteil2dInnerhalbAndroidAccuracyProzent",
    "anteilHoeheInnerhalbAltitudeAccuracyProzent",
]


def summarize_gnss_quality(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Fasst GNSS-Qualitätswerte unabhängig von vorhandenen Referenzdaten zusammen.

    Neben den Mittelwerten werden je Kennzahl die vorhandenen und fehlenden
    Werte gezählt. So bleiben HDOP, PDOP, VDOP, C/N0 und Satellitendaten auch dann
    sichtbar, wenn für eine Messung keine gültige Referenzdistanz vorliegt.
    """
    output_columns = list(group_cols) + ["anzahlMessungen"]
    for names in GNSS_QUALITY_METRICS.values():
        output_columns.extend([names["mean"], names["available"], names["missing"]])

    if df.empty or any(col not in df.columns for col in group_cols):
        return pd.DataFrame(columns=output_columns)

    working = df.copy()
    for metric in GNSS_QUALITY_METRICS:
        if metric not in working.columns:
            working[metric] = pd.NA
        working[metric] = pd.to_numeric(working[metric], errors="coerce")

    rows: list[dict] = []
    group_key = group_cols[0] if len(group_cols) == 1 else group_cols
    for group_values, group in working.groupby(group_key, dropna=False):
        if len(group_cols) == 1:
            group_values = (group_values,)

        row = dict(zip(group_cols, group_values))
        row["anzahlMessungen"] = len(group)

        for metric, names in GNSS_QUALITY_METRICS.items():
            values = group[metric]
            row[names["mean"]] = values.mean()
            row[names["available"]] = int(values.notna().sum())
            row[names["missing"]] = int(values.isna().sum())

        rows.append(row)

    return pd.DataFrame(rows, columns=output_columns)


def _percentage_of_true(values: pd.Series) -> float:
    valid = values.dropna()
    if valid.empty:
        return float("nan")
    return float(valid.astype(bool).mean() * 100.0)


def summarize_group(
    df: pd.DataFrame,
    group_cols: list[str],
    value_col: str = "distanceToReferenceMeters",
) -> pd.DataFrame:
    """Fasst Positions-, Höhen- und 3D-Abweichungen für eine Gruppe zusammen."""
    valid = df.copy()
    height_context = HEIGHT_CONTEXTS.get(value_col)

    numeric_columns = {
        value_col,
        "androidAccuracyMeters",
        "visibleSatellites",
        "usedSatellites",
        "cn0DbHz",
        "hdop",
        "pdop",
        "vdop",
    }
    if height_context:
        numeric_columns.update(col for col in height_context.values() if col is not None)

    for column in numeric_columns:
        if column not in valid.columns:
            valid[column] = pd.NA
        valid[column] = pd.to_numeric(valid[column], errors="coerce")

    valid = valid.dropna(subset=[value_col])
    output_columns = group_cols + BASE_SUMMARY_COLUMNS + (HEIGHT_SUMMARY_COLUMNS if height_context else [])

    if valid.empty:
        return pd.DataFrame(columns=output_columns)

    if height_context:
        altitude_col = height_context["altitude"]
        absolute_difference_col = height_context["absolute_difference"]
        accuracy_col = height_context["accuracy"]
        horizontal_accuracy_col = height_context["horizontal_accuracy"]

        valid["_heightAvailable"] = valid[altitude_col].notna()
        valid["_distance3dAvailable"] = valid[height_context["distance_3d"]].notna()

        if horizontal_accuracy_col:
            valid["_withinHorizontalAccuracy"] = pd.NA
            horizontal_mask = valid[value_col].notna() & valid[horizontal_accuracy_col].notna()
            valid.loc[horizontal_mask, "_withinHorizontalAccuracy"] = (
                valid.loc[horizontal_mask, value_col]
                <= valid.loc[horizontal_mask, horizontal_accuracy_col]
            )
        else:
            valid["_withinHorizontalAccuracy"] = pd.NA

        if accuracy_col:
            valid["_withinAltitudeAccuracy"] = pd.NA
            altitude_mask = valid[absolute_difference_col].notna() & valid[accuracy_col].notna()
            valid.loc[altitude_mask, "_withinAltitudeAccuracy"] = (
                valid.loc[altitude_mask, absolute_difference_col]
                <= valid.loc[altitude_mask, accuracy_col]
            )
        else:
            valid["_withinAltitudeAccuracy"] = pd.NA

    rows: list[dict] = []
    group_key = group_cols[0] if len(group_cols) == 1 else group_cols
    for group_values, group in valid.groupby(group_key, dropna=False):
        if len(group_cols) == 1:
            group_values = (group_values,)

        row = dict(zip(group_cols, group_values))
        main_values = group[value_col]
        row.update({
            "anzahlMessungen": int(main_values.count()),
            "mittelwertMeter": main_values.mean(),
            "medianMeter": main_values.median(),
            "standardabweichungMeter": main_values.std(),
            "minMeter": main_values.min(),
            "maxMeter": main_values.max(),
            "mittlereAndroidAccuracyMeter": group["androidAccuracyMeters"].mean(),
            "mittlereSichtbareSatelliten": group["visibleSatellites"].mean(),
            "mittlereGenutzteSatelliten": group["usedSatellites"].mean(),
            "mittlererCn0DbHz": group["cn0DbHz"].mean(),
            "mittlererHdop": group["hdop"].mean(),
            "mittlererPdop": group["pdop"].mean(),
            "mittlererVdop": group["vdop"].mean(),
        })

        if height_context:
            altitude_values = group[height_context["altitude"]]
            reference_altitude_values = group[height_context["reference_altitude"]]
            difference_values = group[height_context["difference"]]
            absolute_difference_values = group[height_context["absolute_difference"]]
            distance_3d_values = group[height_context["distance_3d"]]
            accuracy_col = height_context["accuracy"]

            row.update({
                "mittlereAltitudeMeter": altitude_values.mean(),
                "medianAltitudeMeter": altitude_values.median(),
                "mittlereReferenzAltitudeMeter": reference_altitude_values.mean(),
                "mittlereHoehenabweichungMeter": difference_values.mean(),
                "mittlereAbsoluteHoehenabweichungMeter": absolute_difference_values.mean(),
                "medianAbsoluteHoehenabweichungMeter": absolute_difference_values.median(),
                "standardabweichungHoehenabweichungMeter": difference_values.std(),
                "mittlereHoehengenauigkeitMeter": group[accuracy_col].mean() if accuracy_col else float("nan"),
                "mittlere3dEntfernungMeter": distance_3d_values.mean(),
                "median3dEntfernungMeter": distance_3d_values.median(),
                "min3dEntfernungMeter": distance_3d_values.min(),
                "max3dEntfernungMeter": distance_3d_values.max(),
                "vorhandeneHoehenWerte": int(altitude_values.notna().sum()),
                "fehlendeHoehenWerte": int(altitude_values.isna().sum()),
                "vorhandene3dEntfernungen": int(distance_3d_values.notna().sum()),
                "fehlende3dEntfernungen": int(distance_3d_values.isna().sum()),
                "anteil2dInnerhalbAndroidAccuracyProzent": _percentage_of_true(group["_withinHorizontalAccuracy"]),
                "anteilHoeheInnerhalbAltitudeAccuracyProzent": _percentage_of_true(group["_withinAltitudeAccuracy"]),
            })

        rows.append(row)

    return pd.DataFrame(rows, columns=output_columns)


def add_environment_comparison_group(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()

    def classify(env: str) -> str:
        if env in OPEN_ENVIRONMENTS:
            return "Freie Fläche"
        if env in FOREST_ENVIRONMENTS:
            return "Waldumgebung"
        if env in URBAN_ENVIRONMENTS:
            return "Urban"
        return "Sonstige / unbekannt"

    enriched["environmentComparison"] = enriched["environmentType"].apply(classify)
    return enriched


def create_altitude_detail_table(df: pd.DataFrame) -> pd.DataFrame:
    """Erstellt eine transparente Einzelmessungstabelle für Höhe und 3D-Distanz."""
    detail_columns = [
        "area",
        "experimentId",
        "measurementId",
        "environmentType",
        "deviceModel",
        "sequenceNumber",
        "offsetSeconds",
        "latitude",
        "longitude",
        "altitude",
        "referenceAltitude",
        "altitudeDifferenceToReferenceMeters",
        "absoluteAltitudeDifferenceToReferenceMeters",
        "altitudeAccuracyMeters",
        "distanceToReferenceMeters",
        "distanceToReference3dMeters",
        "androidAccuracyMeters",
        "hdop",
        "pdop",
        "vdop",
        "visibleSatellites",
        "usedSatellites",
        "cn0DbHz",
    ]

    working = df.copy()
    for column in detail_columns:
        if column not in working.columns:
            working[column] = pd.NA

    return (
        working[detail_columns]
        .sort_values(["area", "experimentId", "offsetSeconds", "sequenceNumber"], na_position="last")
        .reset_index(drop=True)
    )


def run_all_analyses(measurements_df: pd.DataFrame, experiments_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    df = measurements_df.copy()

    # F1: Veränderung bei kurzen Zeitabständen
    f1_time_offsets = summarize_group(
        df,
        ["offsetSeconds"],
        "distanceToReferenceMeters",
    ).sort_values("offsetSeconds")

    # F1 zusätzlich je Umgebung
    f1_time_offsets_by_environment = summarize_group(
        df,
        ["environmentType", "offsetSeconds"],
        "distanceToReferenceMeters",
    ).sort_values(["environmentType", "offsetSeconds"])

    # F2: Umgebungstypen
    f2_environment = summarize_group(
        df,
        ["environmentType"],
        "distanceToReferenceMeters",
    ).sort_values("mittelwertMeter")

    # F3: Smartphone-Modelle
    f3_devices = summarize_group(
        df,
        ["deviceModel"],
        "distanceToReferenceMeters",
    ).sort_values("mittelwertMeter")

    # F4: Foto-Geotag vs. Referenzdaten – inklusive EXIF-Höhe, sofern vorhanden.
    f4_photo_geotags = summarize_group(
        df,
        ["environmentType"],
        "distanceToPhotoGeotagMeters",
    ).sort_values(["environmentType"])

    f4_photo_geotags_overall = summarize_group(
        df,
        ["deviceModel"],
        "distanceToPhotoGeotagMeters",
    ).sort_values("mittelwertMeter")

    # F5: Genauigkeit aller Smartphone-Messungen unter Praxisbedingungen
    f5_all_practical = summarize_group(
        df,
        ["deviceModel"],
        "distanceToReferenceMeters",
    ).sort_values("mittelwertMeter")

    f5_all_practical_overall = summarize_group(
        df.assign(gesamt="Alle Messungen"),
        ["gesamt"],
        "distanceToReferenceMeters",
    )

    # F6: Einfluss der Waldumgebung im Vergleich zu freien Flächen.
    f6_environment_all_types = summarize_group(
        df,
        ["environmentType"],
        "distanceToReferenceMeters",
    ).sort_values("mittelwertMeter")

    df_env_comparison = add_environment_comparison_group(df)
    f6_forest_vs_open = summarize_group(
        df_env_comparison,
        ["environmentComparison"],
        "distanceToReferenceMeters",
    ).sort_values("mittelwertMeter")

    # F7: Referenzdatenvergleich
    f7_reference_by_experiment = summarize_group(
        df,
        ["area", "experimentId", "environmentType", "deviceModel"],
        "distanceToReferenceMeters",
    ).sort_values("mittelwertMeter")

    f7_reference_by_offset = summarize_group(
        df,
        ["area", "environmentType", "offsetSeconds"],
        "distanceToReferenceMeters",
    ).sort_values(["area", "environmentType", "offsetSeconds"])

    # GNSS- und Höhenqualitätsdaten: DOP, C/N0, Satelliten, Höhe und 3D-Distanz.
    # Diese Auswertungen hängen bewusst nicht von einer Referenzdistanz ab.
    gnss_quality_by_device = summarize_gnss_quality(
        df,
        ["deviceModel"],
    ).sort_values("deviceModel")

    gnss_quality_by_environment = summarize_gnss_quality(
        df,
        ["environmentType"],
    ).sort_values("environmentType")

    # Mit "Waldtyp" ist hier das Untersuchungsgebiet gemeint:
    # Stadtwald oder Biosphärenreservat – nicht die Vegetations-/Wegklasse.
    forest_measurements = df[df["area"].isin(AREA_FOLDERS.values())].copy()
    forest_measurements["forestType"] = forest_measurements["area"]
    gnss_quality_by_forest_type = summarize_gnss_quality(
        forest_measurements,
        ["forestType"],
    ).sort_values("forestType")

    # F8: Stadtwald vs. Biosphärenreservat
    f8_area = summarize_group(
        df,
        ["area"],
        "distanceToReferenceMeters",
    ).sort_values("mittelwertMeter")

    f8_area_environment = summarize_group(
        df,
        ["area", "environmentType"],
        "distanceToReferenceMeters",
    ).sort_values(["area", "mittelwertMeter"])

    # Zusatz: Stabilität/Streuung der Messpunkte auch ohne Referenzdaten.
    stability_rows = []
    for experiment_id, group in df.groupby("experimentId", dropna=False):
        center_lat = group["latitude"].mean()
        center_lon = group["longitude"].mean()

        distances = []
        for _, row in group.iterrows():
            d = distance_meters(row["latitude"], row["longitude"], center_lat, center_lon)
            if d is not None:
                distances.append(d)

        altitudes = pd.to_numeric(group.get("altitude"), errors="coerce")
        stability_rows.append({
            "experimentId": experiment_id,
            "area": group["area"].iloc[0],
            "environmentType": group["environmentType"].iloc[0],
            "deviceModel": group["deviceModel"].iloc[0],
            "anzahlMessungen": len(group),
            "mittelpunktLatitude": center_lat,
            "mittelpunktLongitude": center_lon,
            "mittlereAltitudeMeter": altitudes.mean(),
            "standardabweichungAltitudeMeter": altitudes.std(),
            "minAltitudeMeter": altitudes.min(),
            "maxAltitudeMeter": altitudes.max(),
            "mittlereDistanzZumExperimentMittelpunktMeter": sum(distances) / len(distances) if distances else None,
            "maxDistanzZumExperimentMittelpunktMeter": max(distances) if distances else None,
        })

    stability_by_experiment = pd.DataFrame(stability_rows)
    altitude_details = create_altitude_detail_table(df)

    return {
        "F1_zeitabstand": f1_time_offsets,
        "F1_zeitabstand_nach_umgebung": f1_time_offsets_by_environment,
        "F2_umgebungstypen": f2_environment,
        "F3_geraetemodelle": f3_devices,
        "F4_foto_geotags_nach_umgebung_und_zeit": f4_photo_geotags,
        "F4_foto_geotags_nach_geraet": f4_photo_geotags_overall,
        "F5_alle_messungen_nach_geraet": f5_all_practical,
        "F5_alle_messungen_gesamt": f5_all_practical_overall,
        "F6_alle_umgebungstypen": f6_environment_all_types,
        "F6_waldumgebung_vs_freie_flaeche": f6_forest_vs_open,
        "F7_referenzvergleich_nach_experiment": f7_reference_by_experiment,
        "F7_referenzvergleich_nach_zeit": f7_reference_by_offset,
        "F8_gebietvergleich": f8_area,
        "F8_gebiet_und_umgebung": f8_area_environment,
        "GNSS_qualitaet_nach_handy": gnss_quality_by_device,
        "GNSS_qualitaet_nach_umgebungstyp": gnss_quality_by_environment,
        "GNSS_qualitaet_nach_waldtyp": gnss_quality_by_forest_type,
        "zusatz_hoehe_und_3d_einzelmessungen": altitude_details,
        "zusatz_stabilitaet_ohne_referenz": stability_by_experiment,
    }
