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



def create_data_basis_table(measurements_df: pd.DataFrame, experiments_df: pd.DataFrame) -> pd.DataFrame:
    """Kompakte Datengrundlage für Kapitel 6.1.

    Die detaillierten Qualitätsauswertungen bleiben separat erhalten; diese Tabelle
    enthält nur die Kennzahlen, die im Fließtext tatsächlich benötigt werden.
    """
    measurement_count = len(measurements_df)
    experiment_count = len(experiments_df)

    def available_count(df: pd.DataFrame, column: str) -> int:
        if column not in df.columns:
            return 0
        return int(pd.to_numeric(df[column], errors="coerce").notna().sum())

    def percent(count: int, total: int) -> float:
        return (count / total * 100.0) if total else float("nan")

    photo_count = 0
    if "hasPhotoGeotag" in experiments_df.columns:
        photo_count = int(experiments_df["hasPhotoGeotag"].fillna(False).astype(bool).sum())

    rows = [
        {"Kennzahl": "Foto-Experimente", "Anzahl": experiment_count, "AnteilProzent": 100.0},
        {"Kennzahl": "Direkte GNSS-Messungen", "Anzahl": measurement_count, "AnteilProzent": 100.0},
        {"Kennzahl": "Gültige Foto-Geotags", "Anzahl": photo_count, "AnteilProzent": percent(photo_count, experiment_count)},
    ]

    for label, column in [
        ("Sichtbare Satelliten", "visibleSatellites"),
        ("Genutzte Satelliten", "usedSatellites"),
        ("C/N0", "cn0DbHz"),
        ("HDOP", "hdop"),
        ("PDOP", "pdop"),
    ]:
        count = available_count(measurements_df, column)
        rows.append({"Kennzahl": label, "Anzahl": count, "AnteilProzent": percent(count, measurement_count)})

    return pd.DataFrame(rows)


def create_photo_vs_zero_second_table(df: pd.DataFrame) -> pd.DataFrame:
    """Vergleicht je Experiment den Foto-Geotag mit der direkten 0-s-Messung."""
    zero = df[pd.to_numeric(df.get("offsetSeconds"), errors="coerce").eq(0)].copy()
    required = ["latitude", "longitude", "photoLatitude", "photoLongitude", "deviceModel"]
    if zero.empty or any(column not in zero.columns for column in required):
        return pd.DataFrame(columns=[
            "deviceModel", "anzahlExperimente", "mittelwertMeter", "medianMeter",
            "standardabweichungMeter", "fotoGeotagNaeherAls0SekundenProzent",
        ])

    zero["distancePhotoToZeroSecondMeters"] = zero.apply(
        lambda row: distance_meters(
            row["photoLatitude"], row["photoLongitude"], row["latitude"], row["longitude"]
        ),
        axis=1,
    )
    zero = zero.dropna(subset=["distancePhotoToZeroSecondMeters"])

    def summarize_subset(label: str, group: pd.DataFrame) -> dict:
        values = pd.to_numeric(
            group["distancePhotoToZeroSecondMeters"], errors="coerce"
        ).dropna()

        closer = pd.Series(dtype="bool")
        if {"distanceToPhotoGeotagMeters", "distanceToReferenceMeters"}.issubset(group.columns):
            photo_ref = pd.to_numeric(group["distanceToPhotoGeotagMeters"], errors="coerce")
            zero_ref = pd.to_numeric(group["distanceToReferenceMeters"], errors="coerce")
            valid = photo_ref.notna() & zero_ref.notna()
            closer = photo_ref[valid] < zero_ref[valid]

        return {
            "deviceModel": label,
            "anzahlExperimente": int(values.count()),
            "mittelwertMeter": values.mean(),
            "medianMeter": values.median(),
            "standardabweichungMeter": values.std(),
            "fotoGeotagNaeherAls0SekundenProzent": (
                float(closer.mean() * 100.0) if not closer.empty else float("nan")
            ),
        }

    rows = [
        summarize_subset(str(device), group)
        for device, group in zero.groupby("deviceModel", dropna=False)
    ]

    # Gesamtwert über alle gültigen Experimente, damit Mittelwert und Median
    # nicht aus den beiden Gerätegruppen abgeleitet werden müssen.
    rows.append(summarize_subset("Gesamt", zero))

    result = pd.DataFrame(rows)
    device_rows = result[result["deviceModel"] != "Gesamt"].sort_values("deviceModel")
    total_row = result[result["deviceModel"] == "Gesamt"]
    return pd.concat([device_rows, total_row], ignore_index=True)


def add_photo_reference_extras(table: pd.DataFrame, experiments_df: pd.DataFrame) -> pd.DataFrame:
    """Ergänzt den Foto-Referenzvergleich um den Anteil der Abweichungen > 100 m."""
    if table.empty:
        return table

    result = table.copy()
    shares = {}
    for device, group in experiments_df.groupby("deviceModel", dropna=False):
        values = pd.to_numeric(group.get("distanceToPhotoGeotagMeters"), errors="coerce").dropna()
        shares[device] = float((values > 100.0).mean() * 100.0) if not values.empty else float("nan")
    result["anteilUeber100mProzent"] = result["deviceModel"].map(shares)
    return result


def create_overall_accuracy_table(df: pd.DataFrame) -> pd.DataFrame:
    values = pd.to_numeric(df.get("distanceToReferenceMeters"), errors="coerce").dropna()
    if values.empty:
        return pd.DataFrame(columns=[
            "Anzahl", "MittelwertMeter", "MedianMeter", "StandardabweichungMeter", "MinimumMeter", "MaximumMeter"
        ])
    return pd.DataFrame([{
        "Anzahl": int(values.count()),
        "MittelwertMeter": values.mean(),
        "MedianMeter": values.median(),
        "StandardabweichungMeter": values.std(),
        "MinimumMeter": values.min(),
        "MaximumMeter": values.max(),
    }])


def create_accuracy_radius_table(df: pd.DataFrame) -> pd.DataFrame:
    """Kompakte Tabelle für F7: liegt die RTK-Referenz innerhalb Android Accuracy?"""
    rows = []
    for label, subset in [
        ("Gesamt", df),
        ("0 Sekunden", df[pd.to_numeric(df.get("offsetSeconds"), errors="coerce").eq(0)]),
        ("10 Sekunden", df[pd.to_numeric(df.get("offsetSeconds"), errors="coerce").eq(10)]),
        ("30 Sekunden", df[pd.to_numeric(df.get("offsetSeconds"), errors="coerce").eq(30)]),
        ("60 Sekunden", df[pd.to_numeric(df.get("offsetSeconds"), errors="coerce").eq(60)]),
        ("90 Sekunden", df[pd.to_numeric(df.get("offsetSeconds"), errors="coerce").eq(90)]),
        ("120 Sekunden", df[pd.to_numeric(df.get("offsetSeconds"), errors="coerce").eq(120)]),
    ]:
        distance = pd.to_numeric(subset.get("distanceToReferenceMeters"), errors="coerce")
        accuracy = pd.to_numeric(subset.get("androidAccuracyMeters"), errors="coerce")
        valid = distance.notna() & accuracy.notna()
        within = (distance[valid] <= accuracy[valid])
        rows.append({
            "Zeitraum": label,
            "AuswertbareMessungen": int(valid.sum()),
            "InnerhalbAccuracyRadius": int(within.sum()),
            "AnteilProzent": float(within.mean() * 100.0) if not within.empty else float("nan"),
        })
    return pd.DataFrame(rows)

ENVIRONMENT_ORDER = [
    "Freie Fläche",
    "Hauptweg",
    "Trampelpfad",
    "Unter Bäumen",
]


def sort_by_environment_order(
    table: pd.DataFrame,
    leading_columns: list[str] | None = None,
    trailing_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Sortiert environmentType in der fachlich vorgegebenen Reihenfolge."""
    if table.empty or "environmentType" not in table.columns:
        return table

    leading_columns = leading_columns or []
    trailing_columns = trailing_columns or []
    order_map = {name: index for index, name in enumerate(ENVIRONMENT_ORDER)}
    result = table.copy()
    result["_environmentOrder"] = result["environmentType"].map(order_map).fillna(len(ENVIRONMENT_ORDER))
    sort_columns = [*leading_columns, "_environmentOrder", *trailing_columns]
    return result.sort_values(sort_columns, kind="stable").drop(columns="_environmentOrder").reset_index(drop=True)


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
    )
    f1_time_offsets_by_environment = sort_by_environment_order(
        f1_time_offsets_by_environment, trailing_columns=["offsetSeconds"]
    )

    # F1 zusätzlich je Smartphone – wird im Text für den 0/120-s-Vergleich benötigt.
    f1_time_offsets_by_device = summarize_group(
        df,
        ["deviceModel", "offsetSeconds"],
        "distanceToReferenceMeters",
    ).sort_values(["deviceModel", "offsetSeconds"])

    # F2: Umgebungstypen
    f2_environment = summarize_group(
        df,
        ["environmentType"],
        "distanceToReferenceMeters",
    )
    f2_environment = sort_by_environment_order(f2_environment)

    f2_environment_by_device = summarize_group(
        df,
        ["deviceModel", "environmentType"],
        "distanceToReferenceMeters",
    )
    f2_environment_by_device = sort_by_environment_order(
        f2_environment_by_device, leading_columns=["deviceModel"]
    )

    # F3: Smartphone-Modelle
    f3_devices = summarize_group(
        df,
        ["deviceModel"],
        "distanceToReferenceMeters",
    ).sort_values("mittelwertMeter")

    # F4 ist eine Experiment-Auswertung: ein Foto-Geotag gehört genau zu einem Experiment.
    # Deshalb hier bewusst experiments_df verwenden (nicht jede der sechs Messungen).
    f4_photo_geotags = summarize_group(
        experiments_df,
        ["environmentType"],
        "distanceToPhotoGeotagMeters",
    )
    f4_photo_geotags = sort_by_environment_order(f4_photo_geotags)

    f4_photo_geotags_overall = summarize_group(
        experiments_df,
        ["deviceModel"],
        "distanceToPhotoGeotagMeters",
    ).sort_values("mittelwertMeter")
    f4_photo_geotags_overall = add_photo_reference_extras(f4_photo_geotags_overall, experiments_df)

    f4_photo_vs_zero = create_photo_vs_zero_second_table(df)

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
    )
    f6_environment_all_types = sort_by_environment_order(f6_environment_all_types)

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
    )
    f7_reference_by_offset = sort_by_environment_order(
        f7_reference_by_offset, leading_columns=["area"], trailing_columns=["offsetSeconds"]
    )

    # GNSS- und Höhenqualitätsdaten: DOP, C/N0, Satelliten, Höhe und 3D-Distanz.
    # Diese Auswertungen hängen bewusst nicht von einer Referenzdistanz ab.
    gnss_quality_by_device = summarize_gnss_quality(
        df,
        ["deviceModel"],
    ).sort_values("deviceModel")

    gnss_quality_by_environment = summarize_gnss_quality(
        df,
        ["environmentType"],
    )
    gnss_quality_by_environment = sort_by_environment_order(gnss_quality_by_environment)

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

    f8_area_by_device = summarize_group(
        df,
        ["deviceModel", "area"],
        "distanceToReferenceMeters",
    ).sort_values(["deviceModel", "area"])

    f8_area_environment = summarize_group(
        df,
        ["area", "environmentType"],
        "distanceToReferenceMeters",
    )
    f8_area_environment = sort_by_environment_order(
        f8_area_environment, leading_columns=["area"]
    )

    # Zusatz: Stabilität/Streuung der Messpunkte auch ohne Referenzdaten.
    stability_rows = []
    for (area, experiment_id, device_model), group in df.groupby(
        ["area", "experimentId", "deviceModel"], dropna=False
    ):
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
            "area": area,
            "environmentType": group["environmentType"].iloc[0],
            "deviceModel": device_model,
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

    # Kleine Tabellen für den eigentlichen Ergebnisteil. Die detaillierten Tabellen
    # bleiben unverändert im Dictionary und damit als CSV/Report-Anhang erhalten.
    report_data_basis = create_data_basis_table(df, experiments_df)
    report_overall_accuracy = create_overall_accuracy_table(df)
    report_accuracy_radius = create_accuracy_radius_table(df)

    return {
        "F1_zeitabstand": f1_time_offsets,
        "F1_zeitabstand_nach_umgebung": f1_time_offsets_by_environment,
        "F1_zeitabstand_nach_geraet": f1_time_offsets_by_device,
        "F2_umgebungstypen": f2_environment,
        "F2_umgebungstypen_nach_geraet": f2_environment_by_device,
        "F3_geraetemodelle": f3_devices,
        "F4_foto_geotags_nach_umgebung_und_zeit": f4_photo_geotags,
        "F4_foto_geotags_nach_geraet": f4_photo_geotags_overall,
        "F4_foto_vs_0s_nach_geraet": f4_photo_vs_zero,
        "F5_alle_messungen_nach_geraet": f5_all_practical,
        "F5_alle_messungen_gesamt": f5_all_practical_overall,
        "F6_alle_umgebungstypen": f6_environment_all_types,
        "F6_waldumgebung_vs_freie_flaeche": f6_forest_vs_open,
        "F7_referenzvergleich_nach_experiment": f7_reference_by_experiment,
        "F7_referenzvergleich_nach_zeit": f7_reference_by_offset,
        "F8_gebietvergleich": f8_area,
        "F8_gebiet_nach_geraet": f8_area_by_device,
        "F8_gebiet_und_umgebung": f8_area_environment,
        "GNSS_qualitaet_nach_handy": gnss_quality_by_device,
        "GNSS_qualitaet_nach_umgebungstyp": gnss_quality_by_environment,
        "GNSS_qualitaet_nach_waldtyp": gnss_quality_by_forest_type,
        "zusatz_hoehe_und_3d_einzelmessungen": altitude_details,
        "zusatz_stabilitaet_ohne_referenz": stability_by_experiment,
        "bericht_datengrundlage": report_data_basis,
        "bericht_gesamtgenauigkeit": report_overall_accuracy,
        "bericht_accuracy_radius": report_accuracy_radius,
    }
