from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd


TABLE_TITLES = {
    "F1_zeitabstand": "F1: Veränderung der Smartphone-GNSS-Positionen nach Zeitabstand",
    "F1_zeitabstand_nach_umgebung": "F1: Zeitabstand nach Umgebungstyp",
    "F2_umgebungstypen": "F2: Unterschiede zwischen Messumgebungen",
    "F3_geraetemodelle": "F3: Unterschiede zwischen Smartphone-Modellen",
    "F4_foto_geotags_nach_umgebung_und_zeit": "F4: Abweichung von Foto-Geotags zu Referenzdaten nach Umgebung",
    "F4_foto_geotags_nach_geraet": "F4: Abweichung von Foto-Geotags zu Referenzdaten nach Gerät",
    "F5_alle_messungen_nach_geraet": "F5: Genauigkeit aller Smartphone-Messungen nach Gerät",
    "F5_alle_messungen_gesamt": "F5: Genauigkeit aller Smartphone-Messungen gesamt",
    "F6_alle_umgebungstypen": "F6: Einfluss der Umgebung – alle Umgebungstypen",
    "F6_waldumgebung_vs_freie_flaeche": "F6: Waldumgebung vs. freie Fläche",
    "F7_referenzvergleich_nach_experiment": "F7: Vergleich mit Referenzdaten nach Experiment",
    "F7_referenzvergleich_nach_zeit": "F7: Vergleich mit Referenzdaten nach Zeitabstand",
    "F8_gebietvergleich": "F8: Stadtwald vs. Biosphärenreservat",
    "F8_gebiet_und_umgebung": "F8: Gebiet und Umgebung",
    "GNSS_qualitaet_nach_handy": "GNSS- und Höhenqualität nach Handy: DOP, C/N₀, Satelliten, Altitude und 3D-Entfernung",
    "GNSS_qualitaet_nach_umgebungstyp": "GNSS- und Höhenqualität nach Umgebungstyp: DOP, C/N₀, Satelliten, Altitude und 3D-Entfernung",
    "GNSS_qualitaet_nach_waldtyp": "GNSS- und Höhenqualität nach Waldgebiet: Stadtwald / Biosphärenreservat",
    "zusatz_hoehe_und_3d_einzelmessungen": "Zusatz: Höhe, Höhenabweichung und 3D-Entfernung je Einzelmessung",
    "zusatz_stabilitaet_ohne_referenz": "Zusatz: Stabilität der Messpunkte ohne Referenzdaten",
    "F1_zeitabstand_nach_geraet": "F1: Zeitabstand nach Smartphone",
    "F2_umgebungstypen_nach_geraet": "F2: Umgebungstyp nach Smartphone",
    "F4_foto_vs_0s_nach_geraet": "F4: Foto-Geotag vs. direkte 0-Sekunden-Messung",
    "F8_gebiet_nach_geraet": "F8: Untersuchungsgebiet nach Smartphone",
    "bericht_datengrundlage": "Datengrundlage und Verfügbarkeit",
    "bericht_gesamtgenauigkeit": "Gesamtgenauigkeit der direkten Smartphone-Messungen",
    "bericht_accuracy_radius": "RTK-Referenz innerhalb des Android-Accuracy-Radius",
}


MAIN_REPORT_TABLES = [
    "bericht_datengrundlage",
    "bericht_gesamtgenauigkeit",
    "bericht_accuracy_radius",
]


MAIN_REPORT_PLOTS = [
    ("F1_zeitabstand.png", "F1: Messdauer – Mittelwert und Median"),
    ("boxplot_zeitabstand.png", "F1: Verteilung nach Messdauer"),
    ("F2_umgebungstypen.png", "F2: Umgebungstypen – Mittelwert und Median"),
    ("boxplot_umgebungstypen.png", "F2: Verteilung nach Umgebungstyp"),
    ("F3_geraetemodelle.png", "F3: Smartphone-Modelle – Mittelwert und Median"),
    ("F4_foto_vs_0s.png", "F4: Foto-Geotag vs. direkte 0-Sekunden-Messung"),
    ("F4_foto_geotags.png", "F4: Foto-Geotag vs. RTK-Referenz"),
    ("F8_gebietvergleich.png", "F8: Untersuchungsgebiete – Mittelwert und Median"),
    ("boxplot_gebietvergleich.png", "F8: Verteilung nach Untersuchungsgebiet"),
]


def table_to_html(table: pd.DataFrame, max_rows: int | None = None) -> str:
    if table.empty:
        return "<p>Keine gültigen Daten für diese Auswertung vorhanden.</p>"

    display_table = table if max_rows is None else table.head(max_rows)
    return display_table.to_html(
        index=False,
        float_format=lambda x: f"{x:.3f}",
        classes="data-table",
        border=0,
    )


def _table_title(key: str) -> str:
    return TABLE_TITLES.get(key, key.replace("_", " "))


def _render_report_table(key: str, table: pd.DataFrame) -> list[str]:
    title = escape(_table_title(key))
    row_count = len(table)
    return [
        f"<h2>{title}</h2>",
        f"<p class='table-meta'>Vollständige Tabelle: {row_count} Zeile(n)</p>",
        "<div class='table-wrapper'>",
        table_to_html(table),
        "</div>",
    ]


def create_html_report(
    tables: dict[str, pd.DataFrame],
    measurements_df: pd.DataFrame,
    experiments_df: pd.DataFrame,
    issues_df: pd.DataFrame,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    html_parts = [
        "<!doctype html>",
        "<html lang='de'>",
        "<head>",
        "<meta charset='utf-8'>",
        "<title>GPS-Auswertung</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.5; }",
        "table { border-collapse: collapse; width: 100%; margin-bottom: 30px; }",
        "th, td { border: 1px solid #ddd; padding: 8px; vertical-align: top; }",
        "th { background: #f0f0f0; position: sticky; top: 0; }",
        "h1, h2 { color: #222; }",
        ".note { background: #f7f7f7; padding: 12px; border-left: 4px solid #888; }",
        ".table-meta { color: #555; margin-top: -8px; }",
        ".table-wrapper { overflow-x: auto; margin-bottom: 36px; }",
        ".plot { max-width: 100%; height: auto; border: 1px solid #ddd; margin-bottom: 8px; }",
        ".figure { margin-bottom: 32px; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Automatische GPS-Auswertung</h1>",
        "<div class='note'>",
        f"<p>Anzahl Experimente: {len(experiments_df)}</p>",
        f"<p>Anzahl Messungen: {len(measurements_df)}</p>",
        f"<p>Anzahl dokumentierte Datenqualitäts-Hinweise: {len(issues_df)}</p>",
        "</div>",
    ]

    html_parts.append("<h1>Kernauswertungen für den Ergebnisteil</h1>")

    for key in MAIN_REPORT_TABLES:
        table = tables.get(key)
        if table is not None:
            html_parts.extend(_render_report_table(key, table))


    html_parts.append("<h1>Anhang: vollständige Auswertungstabellen</h1>")
    for key, table in tables.items():
        if key in MAIN_REPORT_TABLES:
            continue
        html_parts.extend(_render_report_table(key, table))

    html_parts.extend([
        "<h2>Datenqualität – vollständige Hinweise</h2>",
        f"<p class='table-meta'>Vollständige Tabelle: {len(issues_df)} Zeile(n)</p>",
        "<div class='table-wrapper'>",
        table_to_html(issues_df),
        "</div>",
        "</body></html>",
    ])

    (output_dir / "report.html").write_text("\n".join(html_parts), encoding="utf-8")
