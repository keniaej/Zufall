"""Blätter, die bei jedem Lauf komplett neu aufgebaut werden: je Plattform eines und "Status".

Gemeinsame Basisklasse `NeuesBlatt`: Unterklassen liefern nur `name` und `tabelle()`,
das Schreiben und Formatieren übernimmt `schreiben()`.
"""
from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd
from openpyxl.styles import Alignment

from agent.bericht.excel_hilfen import als_tabelle, blattname, spaltenbreite, zelle_formatieren, zellwert


class NeuesBlatt(ABC):
    """Ein Blatt, das bei jedem Lauf gelöscht und neu geschrieben wird."""

    @property
    @abstractmethod
    def name(self):
        """Blattname im Excel"""

    @abstractmethod
    def tabelle(self):
        """Inhalt als pandas-Tabelle"""

    def schreiben(self, wb, position):
        name = blattname(self.name)
        if name in wb.sheetnames:
            wb.remove(wb[name])
        ws = wb.create_sheet(name, position)
        tabelle = self.tabelle()
        spalten = list(tabelle.columns)
        ws.append(spalten)
        for zeile in tabelle.itertuples(index=False):
            ws.append([zellwert(w) for w in zeile])
        for nr, spalte in enumerate(spalten, start=1):
            for (zelle,) in ws.iter_rows(min_row=2, min_col=nr, max_col=nr):
                zelle_formatieren(zelle, spalte, neu_angelegt=True)
            spaltenbreite(ws, nr, str(spalte))
        for zelle in ws[1]:
            zelle.alignment = Alignment(vertical="center")
        ws.freeze_panes = "A2"
        als_tabelle(ws)
        return ws


class PlattformBlatt(NeuesBlatt):
    """Alles, was von einer Plattform abgerufen wurde, mit Spalte "Ergebnis" vorne zum Filtern."""

    def __init__(self, plattform, gesamt):
        self.plattform = plattform
        self.gesamt = gesamt

    @property
    def name(self):
        return self.plattform

    def tabelle(self):
        t = self.gesamt[self.gesamt["Plattform"] == self.plattform].sort_values("Publikation", ascending=False)
        vorne = ["Ergebnis", "Zufall Produkt"]
        return t[[s for s in vorne if s in t.columns] + [s for s in t.columns if s not in vorne]]


class StatusBlatt(NeuesBlatt):
    """Wann der Lauf war, was jede Plattform geliefert hat, was in der Übersicht passiert ist."""

    name = "Status"

    def __init__(self, status, gesamt, zahlen_uebersicht, seit_datum):
        self.status = status
        self.gesamt = gesamt
        self.zahlen = zahlen_uebersicht
        self.seit_datum = seit_datum

    def tabelle(self):
        zeilen = [("Letzter Lauf", f"{datetime.now():%d.%m.%Y %H:%M}"),
                  ("Bekanntmachungen ab", pd.Timestamp(self.seit_datum).strftime("%d.%m.%Y"))]
        zeilen += [(f"Abruf {name}", text) for name, text in self.status.items()]
        ergebnis = self.gesamt["Ergebnis"].fillna("").str.replace(r"^Dublette.*", "Dublette", regex=True)
        zeilen += [(f"Abgerufen: {wert}", anzahl) for wert, anzahl in ergebnis.value_counts().items()]
        zeilen += [(f"Übersicht: {wert}", anzahl) for wert, anzahl in self.zahlen.items()]
        return pd.DataFrame(zeilen, columns=["Punkt", "Wert"])
