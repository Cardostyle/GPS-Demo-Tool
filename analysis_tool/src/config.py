from pathlib import Path

# Erwartete Zeitabstände der Foto-GNSS-Messungen.
EXPECTED_OFFSET_SECONDS = [0, 10, 30, 60, 90, 120]

AREA_FOLDERS = {
    "stadtwald": "Stadtwald",
    "biosphaerenreservat": "Biosphärenreservat",
}

# Kanonische Namen passend zu den Umgebungstypen in der App.
# Zusätzlich bleiben alte Schreibweisen aus bisherigen Datensätzen auswertbar.
ENVIRONMENT_ALIASES = {
    "freie fläche": "Freie Fläche",
    "freie flaeche": "Freie Fläche",
    "freifläche": "Freie Fläche",
    "freiflaeche": "Freie Fläche",
}

# Für F6: Vergleichsgruppen.
OPEN_ENVIRONMENTS = {"Freie Fläche"}
FOREST_ENVIRONMENTS = {
    "Hauptweg (offenes Blätterdach)",
    "Trampelpfad (geschlossenes Blätterdach)",
    "Unter Bäumen",
}
URBAN_ENVIRONMENTS = {"Urban"}
# Schwelle für Datenqualitäts-Hinweise: Wenn der durchschnittliche Abstand
# aller gültigen Messungen eines Experiments zum Referenzpunkt größer ist,
# wird der Fall im Report protokolliert.
REFERENCE_DISTANCE_WARNING_METERS = 250.0

