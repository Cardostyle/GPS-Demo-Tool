from pathlib import Path

from src.load_data import load_all_experiments
from src.analysis import run_all_analyses
from src.plots import create_all_plots
from src.maps import create_maps
from src.report import create_html_report


def main() -> None:
    data_dir = Path("data")
    results_dir = Path("results")

    results_dir.mkdir(exist_ok=True)
    (results_dir / "tables").mkdir(exist_ok=True)
    (results_dir / "plots").mkdir(exist_ok=True)
    (results_dir / "maps").mkdir(exist_ok=True)
    (results_dir / "report").mkdir(exist_ok=True)

    measurements_df, experiments_df, issues_df = load_all_experiments(data_dir)

    if measurements_df.empty:
        print("Keine Messdaten gefunden. Lege JSON-Dateien in data/stadtwald/ oder data/biosphaerenreservat/ ab.")
        return

    tables = run_all_analyses(measurements_df, experiments_df)

    measurements_df.to_csv(results_dir / "tables" / "all_measurements.csv", index=False)
    experiments_df.to_csv(results_dir / "tables" / "all_experiments.csv", index=False)
    issues_df.to_csv(results_dir / "tables" / "data_quality_issues.csv", index=False)

    for name, table in tables.items():
        table.to_csv(results_dir / "tables" / f"{name}.csv", index=False)

    create_all_plots(tables, measurements_df, results_dir / "plots")
    create_maps(measurements_df, results_dir / "maps")
    create_html_report(tables, measurements_df, experiments_df, issues_df, results_dir / "report")

    print("Auswertung abgeschlossen.")
    print(f"Tabellen: {results_dir / 'tables'}")
    print(f"Diagramme: {results_dir / 'plots'}")
    print(f"Karten: {results_dir / 'maps'}")
    print(f"Bericht: {results_dir / 'report' / 'report.html'}")


if __name__ == "__main__":
    main()
