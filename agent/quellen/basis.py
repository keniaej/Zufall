"""Basisklasse für alle Ausschreibungsportale (Quellen).

Jede Plattform ist eine eigene Klasse, die von `Quelle` erbt und genau zwei Methoden ausfüllt:

    abrufen()      holt die Rohdaten vom Portal, egal in welcher Form (JSON, CSV, XML ...)
    umwandeln(roh) übersetzt sie in eine Tabelle mit den Spalten aus agent/modell.py (SPALTEN)

Den Rest erledigt `holen()` für alle Quellen gleich: Spalten prüfen und Texte bereinigen.
Weil `abrufen` und `umwandeln` als @abstractmethod markiert sind, meldet Python sofort einen
Fehler, wenn eine neue Quelle eine der beiden vergisst.

Neue Quelle anbinden: siehe agent/quellen/vorlage.py
"""
from abc import ABC, abstractmethod

from agent.modell import SPALTEN
from agent.werte import text_bereinigen


class Quelle(ABC):
    """Ein Ausschreibungsportal."""

    # Anzeigename. Erscheint in der Spalte "Plattform", als Blattname im Excel und im Status.
    name = "unbenannt"

    def __init__(self, kriterien, einstellungen):
        self.kriterien = kriterien          # agent.kriterien.Kriterien
        self.einstellungen = einstellungen  # agent.einstellungen.Einstellungen

    @abstractmethod
    def abrufen(self):
        """Rohdaten vom Portal holen."""

    @abstractmethod
    def umwandeln(self, roh):
        """Rohdaten -> pandas-Tabelle mit den Spalten aus SPALTEN, eine Zeile pro Bekanntmachung."""

    def holen(self):
        """abrufen + umwandeln + prüfen. Das ruft der Agent auf."""
        return self.tabelle_pruefen(self.umwandeln(self.abrufen()))

    def tabelle_pruefen(self, tabelle):
        """Bricht mit klarer Meldung ab, wenn die Quelle sich nicht an das Format hält.
        Bereinigt außerdem alle Texte, damit jede Quelle gleich sauber ankommt."""
        fehlend = [s for s in SPALTEN if s not in tabelle.columns]
        if fehlend:
            raise ValueError(f"Quelle '{self.name}' liefert diese Spalten nicht: {fehlend}")
        tabelle = tabelle[SPALTEN].copy()
        for spalte in SPALTEN:
            if tabelle[spalte].dtype == object or str(tabelle[spalte].dtype).startswith("str"):
                tabelle[spalte] = tabelle[spalte].map(text_bereinigen)
        return tabelle

    def __repr__(self):
        return f"{type(self).__name__}(name={self.name!r})"
