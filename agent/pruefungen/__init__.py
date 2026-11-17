"""Die festen Prüfungen. Jede ist eine Klasse, die von Pruefung erbt (siehe basis.py).

Neue Prüfung: Klasse schreiben und hier in standard_pruefungen() an der richtigen Stelle eintragen.
"""
from agent.pruefungen.basis import Pruefung, aufteilen
from agent.pruefungen.cpv import CpvPruefung
from agent.pruefungen.dubletten import DublettenErkennung
from agent.pruefungen.frist import FristPruefung
from agent.pruefungen.region import RegionPruefung
from agent.pruefungen.schlagwoerter import SchlagwortPruefung


def standard_pruefungen(kriterien):
    """Die Prüfungen in ihrer Reihenfolge. CPV zuerst, weil sie das Produkt ermittelt,
    das die Region-Prüfung braucht."""
    return [
        CpvPruefung(kriterien),
        RegionPruefung(kriterien),
        FristPruefung(kriterien),
        SchlagwortPruefung(kriterien),
    ]


__all__ = ["Pruefung", "aufteilen", "CpvPruefung", "RegionPruefung", "FristPruefung",
           "SchlagwortPruefung", "DublettenErkennung", "standard_pruefungen"]
