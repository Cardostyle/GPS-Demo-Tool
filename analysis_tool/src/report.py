from __future__ import annotations

from pathlib import Path

import pandas as pd


def table_to_html(table: pd.DataFrame, max_rows: int = 20) -> str:
    if table.empty:
        return "<p>Keine gültigen Daten für diese Auswertung vorhanden.</p>"
    return table.head(max_rows).to_html(index=False, float_format=lambda x: f"{x:.3f}")


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
        "th, td { border: 1px solid #ddd; padding: 8px; }",
        "th { background: #f0f0f0; }",
        "h1, h2 { color: #222; }",
        ".note { background: #f7f7f7; padding: 12px; border-left: 4px solid #888; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Automatische GPS-Auswertung</h1>",
        "<div class='note'>",
        f"<p>Anzahl Experimente: {len(experiments_df)}</p>",
        f"<p>Anzahl Messungen: {len(measurements_df)}</p>",
        f"<p>Anzahl dokumentierte Datenqualitäts-Hinweise: {len(issues_df)}</p>",
        "</div>",
        "<h2>F1: Veränderung der Smartphone-GNSS-Positionen nach Zeitabstand</h2>",
        table_to_html(tables.get("F1_zeitabstand", pd.DataFrame())),
        "<h2>F2: Unterschiede zwischen Messumgebungen</h2>",
        table_to_html(tables.get("F2_umgebungstypen", pd.DataFrame())),
        "<h2>F3: Unterschiede zwischen Smartphone-Modellen</h2>",
        table_to_html(tables.get("F3_geraetemodelle", pd.DataFrame())),
        "<h2>F4: Abweichung von Foto-Geotags zu GNSS-Messungen</h2>",
        table_to_html(tables.get("F4_foto_geotags_nach_umgebung_und_zeit", pd.DataFrame())),
        "<h2>F5: Genauigkeit aller Smartphone-Messungen unter Praxisbedingungen</h2>",
        table_to_html(tables.get("F5_alle_messungen_gesamt", pd.DataFrame())),
        "<h2>F6: Einfluss der Umgebung</h2>",
        table_to_html(tables.get("F6_alle_umgebungstypen", pd.DataFrame())),
        "<h2>F7: Vergleich mit Referenzdaten</h2>",
        table_to_html(tables.get("F7_referenzvergleich_nach_experiment", pd.DataFrame())),
        "<h2>F8: Stadtwald vs. Biosphärenreservat</h2>",
        table_to_html(tables.get("F8_gebietvergleich", pd.DataFrame())),
        "<h2>Datenqualität</h2>",
        table_to_html(issues_df, max_rows=100),
        "</body></html>",
    ]

    (output_dir / "report.html").write_text("\n".join(html_parts), encoding="utf-8")
