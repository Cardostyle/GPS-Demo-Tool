from pathlib import Path

EXPECTED_OFFSET_SECONDS = [0, 10, 30, 60, 120]

AREA_FOLDERS = {
    "stadtwald": "Stadtwald",
    "biosphaerenreservat": "Biosphärenreservat",
}

ENVIRONMENT_ALIASES = {
    "freie fläche": "freie Fläche",
    "freie flaeche": "freie Fläche",
    "weg": "Weg",
    "unter bäumen": "unter Bäumen",
    "unter baeumen": "unter Bäumen",
}

# Für F6: Waldumgebung vs. offene Fläche.
# Kann später leicht erweitert werden.
OPEN_ENVIRONMENTS = {"freie Fläche"}
FOREST_ENVIRONMENTS = {"Weg", "unter Bäumen"}
