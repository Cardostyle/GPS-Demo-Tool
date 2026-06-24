from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd


TABLE_TITLES = {
    "F1_zeitabstand": "F1: Veränderung der Smartphone-GNSS-Positionen nach Zeitabstand",
    "F1_zeitabstand_nach_umgebung": "F1: Zeitabstand nach Umgebungstyp",
    "F2_umgebungstypen": "F2: Unterschiede zwischen Messumgebungen",
    "F3_geraetemodelle": "F3: Unterschiede zwischen Smartphone-Modellen",
    "F4_foto_geotags_nach_umgebung_und_zeit": "F4: Abweichung von Foto-Geotags zu GNSS-Messungen nach Umgebung und Zeit",
    "F4_foto_geotags_nach_geraet": "F4: Abweichung von Foto-Geotags zu GNSS-Messungen nach Gerät",
    "F5_alle_messungen_nach_geraet": "F5: Genauigkeit aller Smartphone-Messungen nach Gerät",
    "F5_alle_messungen_gesamt": "F5: Genauigkeit aller Smartphone-Messungen gesamt",
    "F6_alle_umgebungstypen": "F6: Einfluss der Umgebung – alle Umgebungstypen",
    "F6_waldumgebung_vs_freie_flaeche": "F6: Waldumgebung vs. freie Fläche",
    "F7_referenzvergleich_nach_experiment": "F7: Vergleich mit Referenzdaten nach Experiment",
    "F7_referenzvergleich_nach_zeit": "F7: Vergleich mit Referenzdaten nach Zeitabstand",
    "F8_gebietvergleich": "F8: Stadtwald vs. Biosphärenreservat",
    "F8_gebiet_und_umgebung": "F8: Gebiet und Umgebung",
    "zusatz_stabilitaet_ohne_referenz": "Zusatz: Stabilität der Messpunkte ohne Referenzdaten",
}


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

    for key, table in tables.items():
        html_parts.extend(_render_report_table(key, table))

    html_parts.extend([
        "<h2>Datenqualität</h2>",
        f"<p class='table-meta'>Vollständige Tabelle: {len(issues_df)} Zeile(n)</p>",
        "<div class='table-wrapper'>",
        table_to_html(issues_df),
        "</div>",
        "</body></html>",
    ])

    (output_dir / "report.html").write_text("\n".join(html_parts), encoding="utf-8")
