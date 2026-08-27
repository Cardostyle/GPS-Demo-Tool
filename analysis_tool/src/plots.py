from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import pandas as pd

from src.config import EXPECTED_OFFSET_SECONDS, FOREST_ENVIRONMENTS, OPEN_ENVIRONMENTS
from src.geo_utils import distance_meters


ENVIRONMENT_ORDER = [
    "Freie Fläche",
    "Hauptweg",
    "Trampelpfad",
    "Unter Bäumen",
]

# Feste Reihenfolge für eine konsistente Darstellung in allen Geräteplots.
DEVICE_ORDER = [
    "samsung SM-S908B",
    "Google Pixel 9 Pro",
]

# Nur die Darstellung im Plot wird lesbarer gemacht. Die Daten selbst bleiben unverändert.
DEVICE_LABELS = {
    "samsung SM-S908B": "Samsung Galaxy S22 Ultra",
    "Google Pixel 9 Pro": "Google Pixel 9 Pro",
}

AREA_ORDER = [
    "Biosphärenreservat",
    "Stadtwald",
]

F6_GROUP_ORDER = [
    "Freie Fläche",
    "Waldumgebung",
]


def _order_environment_rows(
    table: pd.DataFrame,
    column: str = "environmentType",
) -> pd.DataFrame:
    """Ordnet Umgebungstypen fachlich statt nach Messwert oder Alphabet."""
    if table.empty or column not in table.columns:
        return table.copy()

    result = table.copy()
    order_map = {name: index for index, name in enumerate(ENVIRONMENT_ORDER)}
    result["_environment_order"] = (
        result[column]
        .map(order_map)
        .fillna(len(ENVIRONMENT_ORDER))
    )

    return (
        result
        .sort_values("_environment_order", kind="stable")
        .drop(columns="_environment_order")
    )


def _ordered_values(
    series: pd.Series,
    preferred_order: list,
) -> list:
    """
    Liefert vorhandene Werte zuerst in gewünschter,
    danach in stabiler Reihenfolge.
    """
    observed = [
        value
        for value in series.dropna().unique().tolist()
    ]

    ordered = [
        value
        for value in preferred_order
        if value in observed
    ]

    ordered.extend(
        value
        for value in observed
        if value not in ordered
    )

    return ordered


def _display_label(
    value,
    label_map: dict | None = None,
) -> str:
    if label_map is None:
        return str(value)

    return str(label_map.get(value, value))


def save_bar_plot(
    table: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    if (
        table.empty
        or x_col not in table.columns
        or y_col not in table.columns
    ):
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

    plt.xticks(
        rotation=30,
        ha="right",
    )

    plt.tight_layout()
    plt.savefig(
        output_path,
        dpi=200,
    )

    plt.close()


def save_line_plot(
    table: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    if (
        table.empty
        or x_col not in table.columns
        or y_col not in table.columns
    ):
        return

    plot_data = (
        table
        .dropna(subset=[x_col, y_col])
        .sort_values(x_col)
    )

    if plot_data.empty:
        return

    plt.figure(figsize=(10, 6))

    plt.plot(
        plot_data[x_col],
        plot_data[y_col],
        marker="o",
    )

    plt.title(title)
    plt.xlabel(x_col)
    plt.ylabel(ylabel)

    plt.grid(True)

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=200,
    )

    plt.close()


def save_boxplot(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    title: str,
    ylabel: str,
    output_path: Path,
    *,
    group_order: list | None = None,
    label_map: dict | None = None,
    xlabel: str | None = None,
) -> None:
    """
    Einfacher Boxplot für eine Gruppierungsvariable.

    Beispiel:
        Smartphone-Modell
        Umgebungstyp
        Untersuchungsgebiet
        Messzeitpunkt
    """

    if (
        df.empty
        or group_col not in df.columns
        or value_col not in df.columns
    ):
        return

    plot_data = df.dropna(
        subset=[
            group_col,
            value_col,
        ]
    ).copy()

    if plot_data.empty:
        return

    if group_order is None:
        group_values = (
            plot_data[group_col]
            .dropna()
            .unique()
            .tolist()
        )
    else:
        group_values = _ordered_values(
            plot_data[group_col],
            group_order,
        )

    groups = []
    labels = []

    for group_value in group_values:
        values = pd.to_numeric(
            plot_data.loc[
                plot_data[group_col] == group_value,
                value_col,
            ],
            errors="coerce",
        ).dropna()

        if values.empty:
            continue

        groups.append(
            values.to_numpy()
        )

        labels.append(
            _display_label(
                group_value,
                label_map,
            )
        )

    if not groups:
        return

    plt.figure(figsize=(10, 6))

    plt.boxplot(
        groups,
        labels=labels,
    )

    plt.title(title)

    plt.xlabel(
        xlabel
        if xlabel is not None
        else group_col
    )

    plt.ylabel(ylabel)

    plt.xticks(
        rotation=30,
        ha="right",
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=200,
    )

    plt.close()


def save_grouped_boxplot(
    df: pd.DataFrame,
    group_col: str,
    subgroup_col: str,
    value_col: str,
    title: str,
    ylabel: str,
    output_path: Path,
    *,
    group_order: list | None = None,
    subgroup_order: list | None = None,
    group_label_map: dict | None = None,
    subgroup_label_map: dict | None = None,
    xlabel: str | None = None,
) -> None:
    """
    Erzeugt einen gruppierten Boxplot mit einer Haupt- und einer Untergruppe.

    Beispiel:
        environmentType = Hauptgruppe
        deviceModel = Untergruppe

    Dadurch werden beispielsweise für jeden Umgebungstyp zwei
    nebeneinanderliegende Boxplots für die beiden Smartphones erzeugt.

    Die Einzelmessungen werden direkt verwendet. Aggregierte Mittelwerte
    werden für Boxplots bewusst nicht verwendet.
    """

    required = {
        group_col,
        subgroup_col,
        value_col,
    }

    if (
        df.empty
        or not required.issubset(df.columns)
    ):
        return

    plot_data = df.dropna(
        subset=[
            group_col,
            subgroup_col,
            value_col,
        ]
    ).copy()

    if plot_data.empty:
        return

    plot_data[value_col] = pd.to_numeric(
        plot_data[value_col],
        errors="coerce",
    )

    plot_data = plot_data.dropna(
        subset=[value_col]
    )

    if plot_data.empty:
        return

    if group_order is None:
        group_values = (
            plot_data[group_col]
            .dropna()
            .unique()
            .tolist()
        )
    else:
        group_values = _ordered_values(
            plot_data[group_col],
            group_order,
        )

    if subgroup_order is None:
        subgroup_values = (
            plot_data[subgroup_col]
            .dropna()
            .unique()
            .tolist()
        )
    else:
        subgroup_values = _ordered_values(
            plot_data[subgroup_col],
            subgroup_order,
        )

    if (
        not group_values
        or not subgroup_values
    ):
        return

    # Bei vielen Gruppen wird der Plot automatisch etwas breiter.
    figure_width = max(
        10.0,
        2.0 * len(group_values) + 2.0,
    )

    fig, ax = plt.subplots(
        figsize=(
            figure_width,
            6,
        )
    )

    # Farben werden aus dem normalen Matplotlib-Standardzyklus verwendet.
    color_cycle = (
        plt.rcParams[
            "axes.prop_cycle"
        ]
        .by_key()
        .get(
            "color",
            [],
        )
    )

    if not color_cycle:
        color_cycle = [
            None
        ] * len(subgroup_values)

    group_centers = list(
        range(
            1,
            len(group_values) + 1,
        )
    )

    # Gesamter horizontaler Platz je Hauptgruppe.
    total_group_width = 0.72

    subgroup_width = (
        total_group_width
        / max(
            len(subgroup_values),
            1,
        )
    )

    box_width = (
        subgroup_width
        * 0.78
    )

    legend_handles: list[Patch] = []

    for (
        subgroup_index,
        subgroup_value,
    ) in enumerate(subgroup_values):

        offset = (
            -total_group_width / 2
            + subgroup_width / 2
            + subgroup_index * subgroup_width
        )

        box_data = []
        positions = []

        for (
            group_index,
            group_value,
        ) in enumerate(group_values):

            values = plot_data.loc[
                (
                    plot_data[group_col]
                    == group_value
                )
                & (
                    plot_data[subgroup_col]
                    == subgroup_value
                ),
                value_col,
            ].dropna()

            if values.empty:
                continue

            box_data.append(
                values.to_numpy()
            )

            positions.append(
                group_centers[group_index]
                + offset
            )

        if not box_data:
            continue

        color = color_cycle[
            subgroup_index
            % len(color_cycle)
        ]

        boxplot = ax.boxplot(
            box_data,
            positions=positions,
            widths=box_width,
            patch_artist=True,
            manage_ticks=False,
        )

        if color is not None:
            for box in boxplot["boxes"]:
                box.set_facecolor(
                    color
                )

                box.set_alpha(
                    0.65
                )

            legend_handles.append(
                Patch(
                    facecolor=color,
                    alpha=0.65,
                    label=_display_label(
                        subgroup_value,
                        subgroup_label_map,
                    ),
                )
            )

        else:
            legend_handles.append(
                Patch(
                    label=_display_label(
                        subgroup_value,
                        subgroup_label_map,
                    )
                )
            )

    ax.set_title(
        title
    )

    ax.set_xlabel(
        xlabel
        if xlabel is not None
        else group_col
    )

    ax.set_ylabel(
        ylabel
    )

    ax.set_xticks(
        group_centers
    )

    ax.set_xticklabels(
        [
            _display_label(
                value,
                group_label_map,
            )
            for value
            in group_values
        ],
        rotation=30,
        ha="right",
    )

    if legend_handles:
        ax.legend(
            handles=legend_handles,
            title="Smartphone",
        )

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=200,
    )

    plt.close(fig)


def save_mean_median_bar_plot(
    table: pd.DataFrame,
    x_col: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    """
    Gruppierter Balkenplot für Mittelwert und Median.
    """

    required = {
        x_col,
        "mittelwertMeter",
        "medianMeter",
    }

    if (
        table.empty
        or not required.issubset(table.columns)
    ):
        return

    plot_data = table.dropna(
        subset=[x_col]
    ).copy()

    if plot_data.empty:
        return

    x = list(
        range(
            len(plot_data)
        )
    )

    width = 0.38

    plt.figure(
        figsize=(10, 6)
    )

    plt.bar(
        [
            i - width / 2
            for i in x
        ],
        plot_data[
            "mittelwertMeter"
        ],
        width=width,
        label="Mittelwert",
    )

    plt.bar(
        [
            i + width / 2
            for i in x
        ],
        plot_data[
            "medianMeter"
        ],
        width=width,
        label="Median",
    )

    plt.xticks(
        x,
        plot_data[x_col].astype(str),
        rotation=30,
        ha="right",
    )

    plt.title(title)
    plt.ylabel(ylabel)

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=200,
    )

    plt.close()


def save_mean_median_line_plot(
    table: pd.DataFrame,
    x_col: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    required = {
        x_col,
        "mittelwertMeter",
        "medianMeter",
    }

    if (
        table.empty
        or not required.issubset(table.columns)
    ):
        return

    plot_data = (
        table
        .dropna(subset=[x_col])
        .sort_values(x_col)
    )

    if plot_data.empty:
        return

    plt.figure(
        figsize=(10, 6)
    )

    plt.plot(
        plot_data[x_col],
        plot_data[
            "mittelwertMeter"
        ],
        marker="o",
        label="Mittelwert",
    )

    plt.plot(
        plot_data[x_col],
        plot_data[
            "medianMeter"
        ],
        marker="o",
        label="Median",
    )

    plt.title(
        title
    )

    plt.xlabel(
        "Zeitabstand [s]"
    )

    plt.ylabel(
        ylabel
    )

    plt.grid(
        True
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=200,
    )

    plt.close()


def create_all_plots(
    tables: dict[str, pd.DataFrame],
    measurements_df: pd.DataFrame,
    output_dir: Path,
) -> None:
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ==============================================================
    # Bestehende Diagramme
    # ==============================================================

    save_mean_median_line_plot(
        tables[
            "F1_zeitabstand"
        ],
        "offsetSeconds",
        "F1: Abweichung zur Referenz nach Zeitabstand",
        "Abweichung zur Referenz [m]",
        output_dir
        / "F1_zeitabstand.png",
    )

    save_line_plot(
        tables[
            "F1_zeitabstand"
        ],
        "offsetSeconds",
        "mittlere3dEntfernungMeter",
        "F1: Mittlere 3D-Abweichung zur Referenz nach Zeitabstand",
        "Mittlere 3D-Abweichung zur Referenz [m]",
        output_dir
        / "F1_zeitabstand_3d.png",
    )

    save_mean_median_bar_plot(
        _order_environment_rows(
            tables[
                "F2_umgebungstypen"
            ]
        ),
        "environmentType",
        "F2: Abweichung nach Umgebungstyp",
        "Abweichung zur Referenz [m]",
        output_dir
        / "F2_umgebungstypen.png",
    )

    save_bar_plot(
        _order_environment_rows(
            tables[
                "F2_umgebungstypen"
            ]
        ),
        "environmentType",
        "mittlere3dEntfernungMeter",
        "F2: Mittlere 3D-Abweichung nach Umgebungstyp",
        "Mittlere 3D-Abweichung zur Referenz [m]",
        output_dir
        / "F2_umgebungstypen_3d.png",
    )

    save_bar_plot(
        _order_environment_rows(
            tables[
                "F2_umgebungstypen"
            ]
        ),
        "environmentType",
        "mittlereAbsoluteHoehenabweichungMeter",
        "F2: Mittlere absolute Höhenabweichung nach Umgebungstyp",
        "Mittlere absolute Höhenabweichung [m]",
        output_dir
        / "F2_hoehenabweichung_umgebungstypen.png",
    )

    save_mean_median_bar_plot(
        tables[
            "F3_geraetemodelle"
        ],
        "deviceModel",
        "F3: Abweichung nach Smartphone-Modell",
        "Abweichung zur Referenz [m]",
        output_dir
        / "F3_geraetemodelle.png",
    )

    save_bar_plot(
        tables[
            "F3_geraetemodelle"
        ],
        "deviceModel",
        "mittlere3dEntfernungMeter",
        "F3: Mittlere 3D-Abweichung nach Smartphone-Modell",
        "Mittlere 3D-Abweichung zur Referenz [m]",
        output_dir
        / "F3_geraetemodelle_3d.png",
    )

    save_bar_plot(
        tables[
            "F3_geraetemodelle"
        ],
        "deviceModel",
        "mittlereAbsoluteHoehenabweichungMeter",
        "F3: Mittlere absolute Höhenabweichung nach Smartphone-Modell",
        "Mittlere absolute Höhenabweichung [m]",
        output_dir
        / "F3_hoehenabweichung_geraetemodelle.png",
    )

    save_mean_median_bar_plot(
        tables[
            "F4_foto_geotags_nach_geraet"
        ],
        "deviceModel",
        "F4: Foto-Geotag vs. RTK-Referenz",
        "Abweichung zur Referenz [m]",
        output_dir
        / "F4_foto_geotags.png",
    )

    f4_photo_vs_zero_plot = (
        tables[
            "F4_foto_vs_0s_nach_geraet"
        ]
    )

    if (
        "deviceModel"
        in f4_photo_vs_zero_plot.columns
    ):
        f4_photo_vs_zero_plot = (
            f4_photo_vs_zero_plot[
                f4_photo_vs_zero_plot[
                    "deviceModel"
                ]
                != "Gesamt"
            ]
        )

    save_mean_median_bar_plot(
        f4_photo_vs_zero_plot,
        "deviceModel",
        "F4: Foto-Geotag vs. direkte 0-Sekunden-GNSS-Messung",
        "Distanz Foto-Geotag zu 0-s-Messung [m]",
        output_dir
        / "F4_foto_vs_0s.png",
    )

    save_bar_plot(
        _order_environment_rows(
            tables[
                "F6_alle_umgebungstypen"
            ]
        ),
        "environmentType",
        "mittelwertMeter",
        "F6: Einfluss der Umgebung auf die Standortdaten",
        "Mittlere Abweichung zur Referenz [m]",
        output_dir
        / "F6_umgebungseinfluss.png",
    )

    save_mean_median_bar_plot(
        tables[
            "F8_gebietvergleich"
        ],
        "area",
        "F8: Abweichung nach Untersuchungsgebiet",
        "Abweichung zur Referenz [m]",
        output_dir
        / "F8_gebietvergleich.png",
    )

    save_bar_plot(
        tables[
            "F8_gebietvergleich"
        ],
        "area",
        "mittlere3dEntfernungMeter",
        "F8: Mittlere 3D-Abweichung nach Untersuchungsgebiet",
        "Mittlere 3D-Abweichung zur Referenz [m]",
        output_dir
        / "F8_gebietvergleich_3d.png",
    )

    save_bar_plot(
        tables[
            "F8_gebietvergleich"
        ],
        "area",
        "mittlereAbsoluteHoehenabweichungMeter",
        "F8: Mittlere absolute Höhenabweichung nach Untersuchungsgebiet",
        "Mittlere absolute Höhenabweichung [m]",
        output_dir
        / "F8_hoehenabweichung_gebiet.png",
    )

    environment_measurements = (
        measurements_df.copy()
    )

    if (
        "environmentType"
        in environment_measurements.columns
    ):
        environment_measurements[
            "environmentType"
        ] = pd.Categorical(
            environment_measurements[
                "environmentType"
            ],
            categories=ENVIRONMENT_ORDER,
            ordered=True,
        )

    save_boxplot(
        environment_measurements,
        "environmentType",
        "distanceToReferenceMeters",
        "Verteilung der Referenzabweichung nach Umgebungstyp",
        "Abweichung zur Referenz [m]",
        output_dir
        / "boxplot_umgebungstypen.png",
        group_order=ENVIRONMENT_ORDER,
        xlabel="Umgebungstyp",
    )

    save_boxplot(
        measurements_df,
        "offsetSeconds",
        "distanceToReferenceMeters",
        "Verteilung der Referenzabweichung nach Zeitabstand",
        "Abweichung zur Referenz [m]",
        output_dir
        / "boxplot_zeitabstand.png",
        group_order=EXPECTED_OFFSET_SECONDS,
        xlabel="Zeitabstand [s]",
    )

    save_boxplot(
        measurements_df,
        "area",
        "distanceToReferenceMeters",
        "Verteilung der Referenzabweichung nach Untersuchungsgebiet",
        "Abweichung zur Referenz [m]",
        output_dir
        / "boxplot_gebietvergleich.png",
        group_order=AREA_ORDER,
        xlabel="Untersuchungsgebiet",
    )

    save_boxplot(
        environment_measurements,
        "environmentType",
        "absoluteAltitudeDifferenceToReferenceMeters",
        "Verteilung der absoluten Höhenabweichung nach Umgebungstyp",
        "Absolute Höhenabweichung [m]",
        output_dir
        / "boxplot_hoehenabweichung_umgebungstypen.png",
        group_order=ENVIRONMENT_ORDER,
        xlabel="Umgebungstyp",
    )

    # ==============================================================
    # Neue Boxplots
    # ==============================================================

    # --------------------------------------------------------------
    # F2
    #
    # Für jeden Umgebungstyp stehen die beiden Smartphones
    # direkt nebeneinander.
    #
    # Ausgabe:
    # boxplot_umgebungstypen_nach_geraet.png
    # --------------------------------------------------------------

    save_grouped_boxplot(
        measurements_df,
        "environmentType",
        "deviceModel",
        "distanceToReferenceMeters",
        "F2: Verteilung der Referenzabweichung nach Umgebungstyp und Smartphone",
        "Abweichung zur Referenz [m]",
        output_dir
        / "boxplot_umgebungstypen_nach_geraet.png",
        group_order=ENVIRONMENT_ORDER,
        subgroup_order=DEVICE_ORDER,
        subgroup_label_map=DEVICE_LABELS,
        xlabel="Umgebungstyp",
    )

    # --------------------------------------------------------------
    # F6
    #
    # Freie Fläche wird den drei waldbezogenen Kategorien
    # Hauptweg, Trampelpfad und Unter Bäumen gegenübergestellt.
    #
    # Zusätzlich erfolgt die Trennung nach Smartphone.
    #
    # Ausgabe:
    # boxplot_freie_flaeche_vs_wald_nach_geraet.png
    # --------------------------------------------------------------

    f6_measurements = (
        measurements_df.copy()
    )

    if (
        "environmentType"
        in f6_measurements.columns
    ):
        f6_measurements[
            "_f6EnvironmentGroup"
        ] = pd.NA

        f6_measurements.loc[
            f6_measurements[
                "environmentType"
            ].isin(
                OPEN_ENVIRONMENTS
            ),
            "_f6EnvironmentGroup",
        ] = "Freie Fläche"

        f6_measurements.loc[
            f6_measurements[
                "environmentType"
            ].isin(
                FOREST_ENVIRONMENTS
            ),
            "_f6EnvironmentGroup",
        ] = "Waldumgebung"

        f6_measurements = (
            f6_measurements
            .dropna(
                subset=[
                    "_f6EnvironmentGroup"
                ]
            )
        )

        save_grouped_boxplot(
            f6_measurements,
            "_f6EnvironmentGroup",
            "deviceModel",
            "distanceToReferenceMeters",
            "F6: Freie Fläche und Waldumgebung nach Smartphone",
            "Abweichung zur Referenz [m]",
            output_dir
            / "boxplot_freie_flaeche_vs_wald_nach_geraet.png",
            group_order=F6_GROUP_ORDER,
            subgroup_order=DEVICE_ORDER,
            subgroup_label_map=DEVICE_LABELS,
            xlabel="Messumgebung",
        )

    # --------------------------------------------------------------
    # F3
    #
    # Gesamtverteilung beider Smartphones.
    #
    # Dieser Boxplot eignet sich in der Arbeit besonders als Ersatz
    # für das bisherige F3-Balkendiagramm.
    #
    # Ausgabe:
    # boxplot_geraetemodelle.png
    # --------------------------------------------------------------

    save_boxplot(
        measurements_df,
        "deviceModel",
        "distanceToReferenceMeters",
        "F3: Verteilung der Referenzabweichung nach Smartphone-Modell",
        "Abweichung zur Referenz [m]",
        output_dir
        / "boxplot_geraetemodelle.png",
        group_order=DEVICE_ORDER,
        label_map=DEVICE_LABELS,
        xlabel="Smartphone-Modell",
    )

    # --------------------------------------------------------------
    # F8
    #
    # Stadtwald und Biosphärenreservat werden jeweils nochmals
    # getrennt nach Smartphone dargestellt.
    #
    # Ausgabe:
    # boxplot_gebietvergleich_nach_geraet.png
    # --------------------------------------------------------------

    save_grouped_boxplot(
        measurements_df,
        "area",
        "deviceModel",
        "distanceToReferenceMeters",
        "F8: Verteilung der Referenzabweichung nach Untersuchungsgebiet und Smartphone",
        "Abweichung zur Referenz [m]",
        output_dir
        / "boxplot_gebietvergleich_nach_geraet.png",
        group_order=AREA_ORDER,
        subgroup_order=DEVICE_ORDER,
        subgroup_label_map=DEVICE_LABELS,
        xlabel="Untersuchungsgebiet",
    )

    # --------------------------------------------------------------
    # F1
    #
    # Für jeden Messzeitpunkt stehen die Boxplots der beiden
    # Smartphones direkt nebeneinander.
    #
    # Ausgabe:
    # boxplot_zeitabstand_nach_geraet.png
    # --------------------------------------------------------------

    save_grouped_boxplot(
        measurements_df,
        "offsetSeconds",
        "deviceModel",
        "distanceToReferenceMeters",
        "F1: Verteilung der Referenzabweichung nach Zeitabstand und Smartphone",
        "Abweichung zur Referenz [m]",
        output_dir
        / "boxplot_zeitabstand_nach_geraet.png",
        group_order=EXPECTED_OFFSET_SECONDS,
        subgroup_order=DEVICE_ORDER,
        subgroup_label_map=DEVICE_LABELS,
        xlabel="Zeitabstand [s]",
    )

    # --------------------------------------------------------------
    # F4
    #
    # Bei den Foto-Geotags ist wichtig, dass ein Foto-Geotag nur
    # einmal pro Experiment berücksichtigt werden darf.
    #
    # In all_measurements wird dieselbe Foto-Geotag-Information
    # bei allen sechs Messzeitpunkten wiederholt.
    #
    # Deshalb werden hier ausschließlich die 0-Sekunden-Zeilen
    # verwendet. Damit entspricht jede Zeile genau einem
    # Foto-Experiment je Smartphone.
    # --------------------------------------------------------------

    if (
        "offsetSeconds"
        in measurements_df.columns
    ):
        zero_second_rows = (
            measurements_df[
                pd.to_numeric(
                    measurements_df[
                        "offsetSeconds"
                    ],
                    errors="coerce",
                ).eq(0)
            ]
            .copy()
        )

    else:
        zero_second_rows = (
            pd.DataFrame()
        )

    # --------------------------------------------------------------
    # F4a
    #
    # Foto-Geotag gegen RTK-Referenz.
    #
    # Ausgabe:
    # boxplot_foto_geotags_nach_geraet.png
    # --------------------------------------------------------------

    save_boxplot(
        zero_second_rows,
        "deviceModel",
        "distanceToPhotoGeotagMeters",
        "F4: Verteilung der Foto-Geotag-Abweichung zur RTK-Referenz nach Smartphone",
        "Abweichung Foto-Geotag zur RTK-Referenz [m]",
        output_dir
        / "boxplot_foto_geotags_nach_geraet.png",
        group_order=DEVICE_ORDER,
        label_map=DEVICE_LABELS,
        xlabel="Smartphone-Modell",
    )

    # --------------------------------------------------------------
    # F4b
    #
    # Foto-Geotag gegen direkte 0-Sekunden-GNSS-Messung.
    #
    # Da diese Distanz bisher nur innerhalb von analysis.py für
    # die Zusammenfassung berechnet wird, wird sie hier nochmals
    # aus den vorhandenen Einzelkoordinaten erzeugt.
    #
    # Ausgabe:
    # boxplot_foto_vs_0s_nach_geraet.png
    # --------------------------------------------------------------

    required_photo_zero_columns = {
        "photoLatitude",
        "photoLongitude",
        "latitude",
        "longitude",
        "deviceModel",
    }

    if (
        not zero_second_rows.empty
        and required_photo_zero_columns.issubset(
            zero_second_rows.columns
        )
    ):
        photo_vs_zero_rows = (
            zero_second_rows.copy()
        )

        photo_vs_zero_rows[
            "distancePhotoToZeroSecondMeters"
        ] = (
            photo_vs_zero_rows.apply(
                lambda row: distance_meters(
                    row[
                        "photoLatitude"
                    ],
                    row[
                        "photoLongitude"
                    ],
                    row[
                        "latitude"
                    ],
                    row[
                        "longitude"
                    ],
                ),
                axis=1,
            )
        )

        save_boxplot(
            photo_vs_zero_rows,
            "deviceModel",
            "distancePhotoToZeroSecondMeters",
            "F4: Verteilung der Distanz zwischen Foto-Geotag und 0-Sekunden-Messung nach Smartphone",
            "Distanz Foto-Geotag zu 0-s-Messung [m]",
            output_dir
            / "boxplot_foto_vs_0s_nach_geraet.png",
            group_order=DEVICE_ORDER,
            label_map=DEVICE_LABELS,
            xlabel="Smartphone-Modell",
        )