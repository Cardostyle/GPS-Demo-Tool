from __future__ import annotations

import pandas as pd

from src.config import FOREST_ENVIRONMENTS, OPEN_ENVIRONMENTS, URBAN_ENVIRONMENTS


def summarize_group(df: pd.DataFrame, group_cols: list[str], value_col: str = "distanceToReferenceMeters") -> pd.DataFrame:
    valid = df.dropna(subset=[value_col]).copy()

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
        "zusatz_stabilitaet_ohne_referenz": stability_by_experiment,
    }
