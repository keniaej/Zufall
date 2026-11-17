"""Basisklasse für alle Prüfungen (feste Filter-Regeln).

Jede Prüfung ist eine eigene Klasse, die von `Pruefung` erbt und eine Methode ausfüllt:

    gruende(tabelle) -> (tabelle, gruende)
        gibt pro Zeile einen Ausschlussgrund zurück (Text) oder None, wenn die Zeile bleiben darf.
        Die Tabelle darf dabei um eigene Spalten ergänzt werden (z. B. "Zufall Produkt").

Den Rest erledigt `pruefen()` für alle Prüfungen gleich: Zeilen mit Grund kommen nach
"aussortiert" (mit Spalte "Ausschlussgrund"), die anderen bleiben.

Neue Prüfung: Klasse von Pruefung ableiten, `gruende` ausfüllen, in pruefungen/__init__.py eintragen.
"""
from abc import ABC, abstractmethod


class Pruefung(ABC):
    """Eine feste Regel, die Ausschreibungen aussortiert."""

    # Anzeigename im Protokoll
    name = "Prüfung"

    def __init__(self, kriterien):
        self.kriterien = kriterien   # agent.kriterien.Kriterien

    @abstractmethod
    def gruende(self, tabelle):
        """-> (tabelle, Liste mit Grund oder None je Zeile)"""

    def pruefen(self, tabelle):
        """-> (behalten, aussortiert). Das ruft der Agent auf."""
        tabelle, gruende = self.gruende(tabelle)
        return aufteilen(tabelle, gruende)

    def __repr__(self):
        return f"{type(self).__name__}()"


def aufteilen(tabelle, gruende):
    """Trennt Zeilen mit Grund (aussortiert) von Zeilen ohne (behalten)."""
    tabelle = tabelle.copy()
    tabelle["Ausschlussgrund"] = gruende
    raus = tabelle["Ausschlussgrund"].notna()
    behalten = tabelle[~raus].drop(columns="Ausschlussgrund")
    return behalten, tabelle[raus]
