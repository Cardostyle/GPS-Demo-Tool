from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


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

    groups = [g[value_col].values for _, g in plot_data.groupby(group_col)]
    labels = [str(name) for name, _ in plot_data.groupby(group_col)]

    plt.figure(figsize=(10, 6))
    plt.boxplot(groups, labels=labels)
    plt.title(title)
    plt.xlabel(group_col)
    plt.ylabel(ylabel)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def create_all_plots(tables: dict[str, pd.DataFrame], measurements_df: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    save_line_plot(
        tables["F1_zeitabstand"],
        "offsetSeconds",
        "mittelwertMeter",
        "F1: Mittlere Abweichung zur Referenz nach Zeitabstand",
        "Mittlere Abweichung zur Referenz [m]",
        output_dir / "F1_zeitabstand.png",
    )

    save_bar_plot(
        tables["F2_umgebungstypen"],
        "environmentType",
        "mittelwertMeter",
        "F2: Mittlere Abweichung nach Umgebungstyp",
        "Mittlere Abweichung zur Referenz [m]",
        output_dir / "F2_umgebungstypen.png",
    )

    save_bar_plot(
        tables["F3_geraetemodelle"],
        "deviceModel",
        "mittelwertMeter",
        "F3: Mittlere Abweichung nach Smartphone-Modell",
        "Mittlere Abweichung zur Referenz [m]",
        output_dir / "F3_geraetemodelle.png",
    )

    save_bar_plot(
        tables["F4_foto_geotags_nach_geraet"],
        "deviceModel",
        "mittelwertMeter",
        "F4: Mittlere Abweichung zwischen Foto-Geotag und Referenzdaten",
        "Mittlere Abweichung zur Referenz [m]",
        output_dir / "F4_foto_geotags.png",
    )

    save_bar_plot(
        tables["F6_alle_umgebungstypen"],
        "environmentType",
        "mittelwertMeter",
        "F6: Einfluss der Umgebung auf die Standortdaten",
        "Mittlere Abweichung zur Referenz [m]",
        output_dir / "F6_umgebungseinfluss.png",
    )

    save_bar_plot(
        tables["F8_gebietvergleich"],
        "area",
        "mittelwertMeter",
        "F8: Mittlere Abweichung nach Untersuchungsgebiet",
        "Mittlere Abweichung zur Referenz [m]",
        output_dir / "F8_gebietvergleich.png",
    )

    save_boxplot(
        measurements_df,
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
