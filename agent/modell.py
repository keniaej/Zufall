"""Gemeinsames Datenmodell: welche Spalten jede Quelle liefern muss, und das Ergebnis eines Laufs.

Die Bekanntmachungen selbst bleiben pandas-Tabellen (DataFrame), eine Zeile pro Bekanntmachung.
Eine eigene Klasse pro Ausschreibung würde den Code nur länger und langsamer machen.
"""
from dataclasses import dataclass, field

import pandas as pd

# Der "Vertrag" zwischen den Quellen und dem Rest des Programms.
# Jede Quelle muss in Quelle.umwandeln() eine Tabelle mit genau diesen Spalten liefern.
SPALTEN = [
    "Ausschreibungs ID Platform",  # ID auf der jeweiligen Plattform
    "Verfahrens ID",               # ID des Vergabeverfahrens, für Dubletten
    "Publikation",                 # Datum (datetime)
    "Art",                         # Art der Bekanntmachung
    "Titel",
    "Vergabe Branchen Code",       # Haupt-CPV-Code
    "Alle CPV",                    # alle CPV-Codes, kommagetrennt
    "Auftraggeber",
    "Email",                       # E-Mail des Auftraggebers
    "Stadt",
    "Straße",
    "PLZ",                         # als Text, sonst verschwindet die 0 in 02625
    "Land",                        # ausgeschrieben, z. B. "Deutschland"
    "Vergabeart",                  # ausgeschrieben, siehe werte.VERGABEARTEN
    "Vertragsdauer in Monaten",    # Zahl oder leer, siehe werte.laufzeit()
    "Vertragsbeginn",              # Datum (datetime) oder leer, frühester Beginn aller Lose
    "Vertragsende",                # Datum (datetime) oder leer, spätestes Ende aller Lose (ohne Verlängerungen)
    "Leistungsort NUTS",           # Regionscodes des Leistungsorts, kommagetrennt
    "Angebotsfrist",               # Datum (datetime) oder leer
    "Fristart",                    # "Angebot", "Teilnahmeantrag" oder "keine Angabe"
    "Plattform",                   # = Quelle.name
    "Link zur Plattform",
]


def leere_tabelle():
    return pd.DataFrame(columns=SPALTEN)


def verfahrens_ids(tabelle):
    """Merkmal je Zeile, über das dieselbe Ausschreibung erkannt wird (Dubletten, Abgleich der Übersicht).
    Ohne Verfahrens-ID die Plattform-ID (kommt bei TED/öffentlichevergabe.de nicht vor).
    Die Spalte "Verfahrens ID" selbst bleibt dabei unverändert (nichts erfinden)."""
    return tabelle["Verfahrens ID"].fillna(tabelle["Ausschreibungs ID Platform"]).astype(str)


@dataclass
class LaufErgebnis:
    """Alles, was ein Lauf erzeugt. Wird an den Bericht (Excel) übergeben.

    alle        jede abgerufene Bekanntmachung, aller Quellen
    behalten    nach der Dubletten-Erkennung (eine Zeile pro Verfahren)
    relevant    hat alle Prüfungen bestanden
    aussortiert von einer Prüfung aussortiert, mit Spalte "Ausschlussgrund"
    gesamt      = alle, ergänzt um "Ergebnis" (relevant / aussortiert: Grund / Dublette ...)
    status      pro Quelle "ok, N Bekanntmachungen" oder "FEHLER: ..."
    """
    alle: pd.DataFrame
    behalten: pd.DataFrame
    relevant: pd.DataFrame
    aussortiert: pd.DataFrame
    gesamt: pd.DataFrame
    status: dict = field(default_factory=dict)
