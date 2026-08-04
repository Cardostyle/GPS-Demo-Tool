from __future__ import annotations

import pandas as pd

from src.config import AREA_FOLDERS, FOREST_ENVIRONMENTS, OPEN_ENVIRONMENTS, URBAN_ENVIRONMENTS


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
}


def summarize_gnss_quality(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Fasst GNSS-Qualitätswerte unabhängig von vorhandenen Referenzdaten zusammen.

    Neben den Mittelwerten werden je Kennzahl die vorhandenen und fehlenden
    Werte gezählt. So bleiben HDOP, PDOP, C/N0 und Satellitendaten auch dann
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


def summarize_group(df: pd.DataFrame, group_cols: list[str], value_col: str = "distanceToReferenceMeters") -> pd.DataFrame:
    valid = df.copy()
    numeric_columns = [
        value_col,
        "androidAccuracyMeters",
        "visibleSatellites",
        "usedSatellites",
        "cn0DbHz",
        "hdop",
        "pdop",
    ]
    for column in numeric_columns:
        if column not in valid.columns:
            valid[column] = pd.NA
        valid[column] = pd.to_numeric(valid[column], errors="coerce")

    valid = valid.dropna(subset=[value_col])

    if valid.empty:
        return pd.DataFrame(columns=group_cols + [
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
        ])

    result = (
        valid
        .groupby(group_cols, dropna=False)
        .agg(
            anzahlMessungen=(value_col, "count"),
            mittelwertMeter=(value_col, "mean"),
            medianMeter=(value_col, "median"),
            standardabweichungMeter=(value_col, "std"),
            minMeter=(value_col, "min"),
            maxMeter=(value_col, "max"),
            mittlereAndroidAccuracyMeter=("androidAccuracyMeters", "mean"),
            mittlereSichtbareSatelliten=("visibleSatellites", "mean"),
            mittlereGenutzteSatelliten=("usedSatellites", "mean"),
            mittlererCn0DbHz=("cn0DbHz", "mean"),
            mittlererHdop=("hdop", "mean"),
            mittlererPdop=("pdop", "mean"),
        )
        .reset_index()
    )

    return result


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

    # F4: Foto-Geotag vs. Referenzdaten
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
    # Gewünscht: alle Daten unabhängig von Umgebung und Tag.
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
    # Gewünscht: alle Umgebungstypen vergleichen.
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

    # GNSS-Qualitätsdaten: HDOP, PDOP, C/N0 und Satellitenwerte.
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
    # Damit können Experimente ohne Referenz immerhin auf der Karte und über Streuung beschrieben werden.
    stability_rows = []
    for experiment_id, group in df.groupby("experimentId", dropna=False):
        center_lat = group["latitude"].mean()
        center_lon = group["longitude"].mean()

        distances = []
        from src.geo_utils import distance_meters
        for _, row in group.iterrows():
            d = distance_meters(row["latitude"], row["longitude"], center_lat, center_lon)
            if d is not None:
                distances.append(d)

        stability_rows.append({
            "experimentId": experiment_id,
            "area": group["area"].iloc[0],
            "environmentType": group["environmentType"].iloc[0],
            "deviceModel": group["deviceModel"].iloc[0],
            "anzahlMessungen": len(group),
            "mittelpunktLatitude": center_lat,
            "mittelpunktLongitude": center_lon,
            "mittlereDistanzZumExperimentMittelpunktMeter": sum(distances) / len(distances) if distances else None,
            "maxDistanzZumExperimentMittelpunktMeter": max(distances) if distances else None,
        })

    stability_by_experiment = pd.DataFrame(stability_rows)

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
        "zusatz_stabilitaet_ohne_referenz": stability_by_experiment,
    }
