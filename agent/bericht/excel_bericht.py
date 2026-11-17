"""Die Excel-Datei output/ausschreibungen.xlsx: öffnen, Blätter schreiben, sichern, speichern.

Immer DIESELBE Datei, damit Power BI fest mit ihr verbunden bleiben kann.
Blätter: Übersicht (abgeglichen, siehe uebersicht.py), ein Blatt je Plattform und Status (neu, siehe blaetter.py).
Jedes Blatt ist als Excel-Tabelle formatiert (wie Strg+T). Tabellennamen: Uebersicht, TED,
oeffentlichevergabe_de, Status.
"""
import os
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import Workbook, load_workbook

from agent.bericht.blaetter import PlattformBlatt, StatusBlatt
from agent.bericht.uebersicht import UebersichtAbgleich


class DateiGeoeffnetFehler(PermissionError):
    """Die Excel-Datei ist in Excel geöffnet und kann nicht geschrieben werden."""


class ExcelBericht:
    DATEINAME = "ausschreibungen.xlsx"
    SICHERUNGEN_ORDNER = "sicherungen"
    SICHERUNGEN_BEHALTEN = 10

    def __init__(self, einstellungen):
        self.einstellungen = einstellungen
        self.ordner = Path(einstellungen.ausgabe_ordner)
        self.pfad = self.ordner / self.DATEINAME

    def pruefen_ob_offen(self):
        """Vor dem Lauf aufrufen: Ist die Datei in Excel geöffnet, gleich abbrechen
        (und nicht erst nach mehreren Minuten Abruf)."""
        if self.pfad.exists():
            try:
                with open(self.pfad, "r+b"):
                    pass
            except PermissionError:
                raise DateiGeoeffnetFehler(self._meldung_geoeffnet())

    def schreiben(self, ergebnis):
        """Schreibt einen Lauf (agent.modell.LaufErgebnis) in die Excel-Datei. Gibt den Pfad zurück."""
        self.ordner.mkdir(parents=True, exist_ok=True)
        self.pruefen_ob_offen()
        heute = pd.Timestamp.today().normalize()
        wb = self._oeffnen()

        zahlen = UebersichtAbgleich(heute).aktualisieren(wb, ergebnis.gesamt)
        position = 1
        for plattform in ergebnis.status:   # gleiche Reihenfolge wie die Quellen, auch wenn eine ausgefallen ist
            PlattformBlatt(plattform, ergebnis.gesamt).schreiben(wb, position)
            position += 1
        StatusBlatt(ergebnis.status, ergebnis.gesamt, zahlen, self.einstellungen.seit_datum).schreiben(wb, position)
        wb.active = 0

        self._sichern()
        self._speichern(wb)
        return self.pfad

    def _oeffnen(self):
        if self.pfad.exists():
            return load_workbook(self.pfad)
        wb = Workbook()
        wb.remove(wb.active)
        return wb

    def _sichern(self):
        """Kopie des alten Stands nach sicherungen/, die letzten SICHERUNGEN_BEHALTEN bleiben."""
        if not self.pfad.exists():
            return
        ordner = self.ordner / self.SICHERUNGEN_ORDNER
        ordner.mkdir(exist_ok=True)
        shutil.copy2(self.pfad, ordner / f"ausschreibungen_{datetime.now():%Y-%m-%d_%H%M%S}.xlsx")
        alte = sorted(f for f in os.listdir(ordner) if f.startswith("ausschreibungen_") and f.endswith(".xlsx"))
        for datei in alte[:-self.SICHERUNGEN_BEHALTEN]:
            os.remove(ordner / datei)

    def _speichern(self, wb):
        """Erst in eine Zwischendatei schreiben, dann austauschen: bricht etwas ab, bleibt die alte Datei heil."""
        zwischen = self.pfad.with_name(self.pfad.name + ".neu")
        wb.save(zwischen)
        try:
            os.replace(zwischen, self.pfad)
        except PermissionError:
            os.remove(zwischen)
            raise DateiGeoeffnetFehler(self._meldung_geoeffnet())

    def _meldung_geoeffnet(self):
        return f"{self.pfad} ist gerade geöffnet (z. B. in Excel). Bitte schließen und neu starten."
