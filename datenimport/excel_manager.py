"""Schreiben der Ergebnisse nach ``Ausschreibungen.xlsx`` (ein Blatt je Plattform).

Jedes Blatt besteht nur aus Kopfzeile (Zeile 1) und den Datensätzen. Fehlt die Datei
oder das Blatt einer Plattform, wird es automatisch angelegt. Vorhandene Daten bleiben erhalten.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date, datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from branchen_codes import Ausschreibung

ID_INTERN = "Ausschreibungs ID Intern"
ID_PLATTFORM = "Ausschreibungs ID Platform"
# Excel-Überschrift -> Attribut von Ausschreibung
SPALTEN = {
    ID_PLATTFORM: "plattform_id",
    "Vergabe Branchen Code": "branchen_code",
    "Zufall Produkt": "produkt",
    "Auftraggeber": "auftraggeber",
    "Email": "email",
    "Stadt": "stadt",
    "Straße": "strasse",
    "PLZ": "plz",
    "Land": "land",
    "Vergabeart": "vergabeart",
    "Publikation": "publikation",
    "Angebotsfrist": "angebotsfrist",
    "Vertragsdauer in Monaten": "vertragsdauer_monate",
    "Plattform": "plattform",
    "Link zur Plattform": "link",
    "Beschreibung": "titel",
}
LINK_PRAEFIX = {"link": "", "email": "mailto:"}
BREITEN = {"Vergabe Branchen Code": 40, "Auftraggeber": 35, "Email": 30,
           "Link zur Plattform": 45, "Beschreibung": 70}


class ExcelManager:
    """Schreibt Ausschreibungen in die Arbeitsmappe, ein Blatt je Plattform."""

    def __init__(self, pfad: Path | str) -> None:
        self.pfad = Path(pfad)
        if self.pfad.exists():
            self.mappe = load_workbook(self.pfad)
        else:
            self.mappe = Workbook()
            self.mappe.remove(self.mappe.active)

    def speichern(self, ausschreibungen: Iterable[Ausschreibung]) -> tuple[int, int]:
        """Ergänzt neue und aktualisiert geänderte Ausschreibungen.

        Returns:
            Anzahl (neu, aktualisiert) über alle Plattformen.
        """
        je_plattform: dict[str, list[Ausschreibung]] = defaultdict(list)
        for a in ausschreibungen:
            je_plattform[a.plattform].append(a)
        neu = aktualisiert = 0
        for plattform, liste in je_plattform.items():
            n, u = _Tabelle(self.blatt(plattform)).importieren(liste)
            neu, aktualisiert = neu + n, aktualisiert + u
        if self.mappe.worksheets:
            self.mappe.save(self.pfad)
        return neu, aktualisiert

    def blatt(self, name: str) -> Worksheet:
        """Blatt der Plattform; fehlt es, wird es mit Kopfzeile angelegt."""
        if name in self.mappe.sheetnames:
            return self.mappe[name]
        blatt = self.mappe.create_sheet(name)
        blatt.append([ID_INTERN, *SPALTEN])
        for spalte, zelle in enumerate(blatt[1], start=1):
            zelle.font = Font(bold=True)
            zelle.fill = PatternFill("solid", fgColor="D9E1F2")
            breite = BREITEN.get(zelle.value, 16)
            blatt.column_dimensions[get_column_letter(spalte)].width = breite
        blatt.freeze_panes = "A2"
        return blatt


class _Tabelle:
    """Ein Plattform-Blatt. Die Ausschreibungs-ID ist innerhalb des Blatts eindeutig."""

    def __init__(self, blatt: Worksheet) -> None:
        self.blatt = blatt
        self.spalten = {str(c.value).strip(): c.column for c in blatt[1] if c.value}

    def importieren(self, ausschreibungen: Iterable[Ausschreibung]) -> tuple[int, int]:
        """Legt neue Zeilen an, aktualisiert vorhandene. Returns: (neu, aktualisiert)."""
        zeilen = self._vorhandene_zeilen()
        naechste_id = self._hoechste_id() + 1
        neu = aktualisiert = 0
        for a in ausschreibungen:
            schluessel = str(a.plattform_id)
            if schluessel in zeilen:
                aktualisiert += self._schreiben(zeilen[schluessel], a)
                continue
            zeile = zeilen[schluessel] = max(zeilen.values(), default=1) + 1
            self.blatt.cell(zeile, self.spalten[ID_INTERN], naechste_id)
            self._schreiben(zeile, a)
            naechste_id += 1
            neu += 1
        self.blatt.auto_filter.ref = self.blatt.dimensions
        return neu, aktualisiert

    def _schreiben(self, zeile: int, a: Ausschreibung) -> bool:
        """Schreibt geänderte Werte (leere überschreiben nichts); ``True`` bei Änderung."""
        geaendert = False
        for ueberschrift, attribut in SPALTEN.items():
            wert = _normalisieren(getattr(a, attribut))
            zelle = self.blatt.cell(zeile, self.spalten[ueberschrift])
            if wert in (None, "") or _normalisieren(zelle.value) == wert:
                continue
            zelle.value = wert
            if isinstance(wert, datetime):
                zelle.number_format = "DD.MM.YYYY"
            if attribut in LINK_PRAEFIX:
                zelle.hyperlink = LINK_PRAEFIX[attribut] + str(wert)
                zelle.style = "Hyperlink"
            geaendert = True
        return geaendert

    def _datenzeilen(self) -> range:
        return range(2, self.blatt.max_row + 1)

    def _wert(self, zeile: int, ueberschrift: str) -> Any:
        return self.blatt.cell(zeile, self.spalten[ueberschrift]).value

    def _vorhandene_zeilen(self) -> dict[str, int]:
        """Index Plattform-ID -> Zeilennummer."""
        return {
            str(plattform_id).strip(): z
            for z in self._datenzeilen()
            if (plattform_id := self._wert(z, ID_PLATTFORM)) is not None
        }

    def _hoechste_id(self) -> int:
        ids = (self._wert(z, ID_INTERN) for z in self._datenzeilen())
        return max((int(i) for i in ids if isinstance(i, (int, float))), default=0)


def _normalisieren(wert: Any) -> Any:
    """Vereinheitlicht Werte für Vergleich und Speicherung (date -> datetime, Text trimmen)."""
    if isinstance(wert, date):
        return datetime(wert.year, wert.month, wert.day)
    return wert.strip() if isinstance(wert, str) else wert
