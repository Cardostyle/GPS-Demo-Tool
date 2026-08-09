from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


ENVIRONMENT_ORDER = [
    "Freie Fläche",
    "Hauptweg",
    "Trampelpfad",
    "Unter Bäumen",
]


def _order_environment_rows(table: pd.DataFrame, column: str = "environmentType") -> pd.DataFrame:
    """Ordnet Umgebungstypen fachlich statt nach Messwert oder Alphabet."""
    if table.empty or column not in table.columns:
        return table.copy()

    result = table.copy()
    order_map = {name: index for index, name in enumerate(ENVIRONMENT_ORDER)}
    result["_environment_order"] = result[column].map(order_map).fillna(len(ENVIRONMENT_ORDER))
    return result.sort_values("_environment_order", kind="stable").drop(columns="_environment_order")


def save_bar_plot(table: pd.DataFrame, x_col: str, y_col: str, title: str, ylabel: str, output_path: Path) -> None:
    if table.empty or x_col not in table.columns or y_col not in table.columns:
        return

    plot_data = table.dropna(subset=[y_col]).copy()
    if plot_data.empty:
        return

    labels = plot_data[x_col].astype(str)
    values = plot_data[y_col]

    plt.figure(figsize=(10, 6))
    plt.bar(labels, values)
    plt.title(title)
    plt.xlabel(x_col)
    plt.ylabel(ylabel)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_line_plot(table: pd.DataFrame, x_col: str, y_col: str, title: str, ylabel: str, output_path: Path) -> None:
    if table.empty or x_col not in table.columns or y_col not in table.columns:
        return

    plot_data = table.dropna(subset=[x_col, y_col]).sort_values(x_col)
    if plot_data.empty:
        return

    plt.figure(figsize=(10, 6))
    plt.plot(plot_data[x_col], plot_data[y_col], marker="o")
    plt.title(title)
    plt.xlabel(x_col)
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_boxplot(df: pd.DataFrame, group_col: str, value_col: str, title: str, ylabel: str, output_path: Path) -> None:
    if df.empty or group_col not in df.columns or value_col not in df.columns:
        return

    plot_data = df.dropna(subset=[group_col, value_col])
    if plot_data.empty:
        return

    groups = [g[value_col].values for _, g in plot_data.groupby(group_col, observed=True)]
    labels = [str(name) for name, _ in plot_data.groupby(group_col, observed=True)]

    plt.figure(figsize=(10, 6))
    plt.boxplot(groups, labels=labels)
    plt.title(title)
    plt.xlabel(group_col)
    plt.ylabel(ylabel)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()



def save_mean_median_bar_plot(
    table: pd.DataFrame,
    x_col: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    """Gruppierter Balkenplot für Mittelwert und Median."""
    required = {x_col, "mittelwertMeter", "medianMeter"}
    if table.empty or not required.issubset(table.columns):
        return

    plot_data = table.dropna(subset=[x_col]).copy()
    if plot_data.empty:
        return

    x = list(range(len(plot_data)))
    width = 0.38
    plt.figure(figsize=(10, 6))
    plt.bar([i - width / 2 for i in x], plot_data["mittelwertMeter"], width=width, label="Mittelwert")
    plt.bar([i + width / 2 for i in x], plot_data["medianMeter"], width=width, label="Median")
    plt.xticks(x, plot_data[x_col].astype(str), rotation=30, ha="right")
    plt.title(title)
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_mean_median_line_plot(
    table: pd.DataFrame,
    x_col: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    required = {x_col, "mittelwertMeter", "medianMeter"}
    if table.empty or not required.issubset(table.columns):
        return

    plot_data = table.dropna(subset=[x_col]).sort_values(x_col)
    if plot_data.empty:
        return

    plt.figure(figsize=(10, 6))
    plt.plot(plot_data[x_col], plot_data["mittelwertMeter"], marker="o", label="Mittelwert")
    plt.plot(plot_data[x_col], plot_data["medianMeter"], marker="o", label="Median")
    plt.title(title)
    plt.xlabel("Zeitabstand [s]")
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()



def create_all_plots(tables: dict[str, pd.DataFrame], measurements_df: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    save_mean_median_line_plot(
        tables["F1_zeitabstand"],
        "offsetSeconds",
        "F1: Abweichung zur Referenz nach Zeitabstand",
        "Abweichung zur Referenz [m]",
        output_dir / "F1_zeitabstand.png",
    )

    save_line_plot(
        tables["F1_zeitabstand"],
        "offsetSeconds",
        "mittlere3dEntfernungMeter",
        "F1: Mittlere 3D-Abweichung zur Referenz nach Zeitabstand",
        "Mittlere 3D-Abweichung zur Referenz [m]",
        output_dir / "F1_zeitabstand_3d.png",
    )

    save_mean_median_bar_plot(
        _order_environment_rows(tables["F2_umgebungstypen"]),
        "environmentType",
        "F2: Abweichung nach Umgebungstyp",
        "Abweichung zur Referenz [m]",
        output_dir / "F2_umgebungstypen.png",
    )

    save_bar_plot(
        _order_environment_rows(tables["F2_umgebungstypen"]),
        "environmentType",
        "mittlere3dEntfernungMeter",
        "F2: Mittlere 3D-Abweichung nach Umgebungstyp",
        "Mittlere 3D-Abweichung zur Referenz [m]",
        output_dir / "F2_umgebungstypen_3d.png",
    )

    save_bar_plot(
        _order_environment_rows(tables["F2_umgebungstypen"]),
        "environmentType",
        "mittlereAbsoluteHoehenabweichungMeter",
        "F2: Mittlere absolute Höhenabweichung nach Umgebungstyp",
        "Mittlere absolute Höhenabweichung [m]",
        output_dir / "F2_hoehenabweichung_umgebungstypen.png",
    )

    save_mean_median_bar_plot(
        tables["F3_geraetemodelle"],
        "deviceModel",
        "F3: Abweichung nach Smartphone-Modell",
        "Abweichung zur Referenz [m]",
        output_dir / "F3_geraetemodelle.png",
    )

    save_bar_plot(
        tables["F3_geraetemodelle"],
        "deviceModel",
        "mittlere3dEntfernungMeter",
        "F3: Mittlere 3D-Abweichung nach Smartphone-Modell",
        "Mittlere 3D-Abweichung zur Referenz [m]",
        output_dir / "F3_geraetemodelle_3d.png",
    )

    save_bar_plot(
        tables["F3_geraetemodelle"],
        "deviceModel",
        "mittlereAbsoluteHoehenabweichungMeter",
        "F3: Mittlere absolute Höhenabweichung nach Smartphone-Modell",
        "Mittlere absolute Höhenabweichung [m]",
        output_dir / "F3_hoehenabweichung_geraetemodelle.png",
    )

    save_mean_median_bar_plot(
        tables["F4_foto_geotags_nach_geraet"],
        "deviceModel",
        "F4: Foto-Geotag vs. RTK-Referenz",
        "Abweichung zur Referenz [m]",
        output_dir / "F4_foto_geotags.png",
    )

    save_mean_median_bar_plot(
        tables["F4_foto_vs_0s_nach_geraet"],
        "deviceModel",
        "F4: Foto-Geotag vs. direkte 0-Sekunden-GNSS-Messung",
        "Distanz Foto-Geotag zu 0-s-Messung [m]",
        output_dir / "F4_foto_vs_0s.png",
    )

    save_bar_plot(
        _order_environment_rows(tables["F6_alle_umgebungstypen"]),
        "environmentType",
        "mittelwertMeter",
        "F6: Einfluss der Umgebung auf die Standortdaten",
        "Mittlere Abweichung zur Referenz [m]",
        output_dir / "F6_umgebungseinfluss.png",
    )

    save_mean_median_bar_plot(
        tables["F8_gebietvergleich"],
        "area",
        "F8: Abweichung nach Untersuchungsgebiet",
        "Abweichung zur Referenz [m]",
        output_dir / "F8_gebietvergleich.png",
    )

    save_bar_plot(
        tables["F8_gebietvergleich"],
        "area",
        "mittlere3dEntfernungMeter",
        "F8: Mittlere 3D-Abweichung nach Untersuchungsgebiet",
        "Mittlere 3D-Abweichung zur Referenz [m]",
        output_dir / "F8_gebietvergleich_3d.png",
    )

    save_bar_plot(
        tables["F8_gebietvergleich"],
        "area",
        "mittlereAbsoluteHoehenabweichungMeter",
        "F8: Mittlere absolute Höhenabweichung nach Untersuchungsgebiet",
        "Mittlere absolute Höhenabweichung [m]",
        output_dir / "F8_hoehenabweichung_gebiet.png",
    )

    environment_measurements = measurements_df.copy()
    if "environmentType" in environment_measurements.columns:
        environment_measurements["environmentType"] = pd.Categorical(
            environment_measurements["environmentType"],
            categories=ENVIRONMENT_ORDER,
            ordered=True,
        )

    save_boxplot(
        environment_measurements,
        "environmentType",
        "distanceToReferenceMeters",
        "Verteilung der Referenzabweichung nach Umgebungstyp",
        "Abweichung zur Referenz [m]",
        output_dir / "boxplot_umgebungstypen.png",
    )

    save_boxplot(
        measurements_df,
        "offsetSeconds",
        "distanceToReferenceMeters",
        "Verteilung der Referenzabweichung nach Zeitabstand",
        "Abweichung zur Referenz [m]",
        output_dir / "boxplot_zeitabstand.png",
    )

    save_boxplot(
        measurements_df,
        "area",
        "distanceToReferenceMeters",
        "Verteilung der Referenzabweichung nach Untersuchungsgebiet",
        "Abweichung zur Referenz [m]",
        output_dir / "boxplot_gebietvergleich.png",
    )



    save_boxplot(
        environment_measurements,
        "environmentType",
        "absoluteAltitudeDifferenceToReferenceMeters",
        "Verteilung der absoluten Höhenabweichung nach Umgebungstyp",
        "Absolute Höhenabweichung [m]",
        output_dir / "boxplot_hoehenabweichung_umgebungstypen.png",
    )
