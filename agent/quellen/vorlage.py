"""VORLAGE für eine neue Quelle

So fügt ihr ein neues Ausschreibungsportal hinzu:
1. Diese Datei kopieren und umbenennen, z. B. in `dtvp.py`.
2. Die beiden Funktionen unten ausfüllen.
3. Die Quelle in `agent/quellen/__init__.py` in die Liste QUELLEN eintragen.

Alles andere (Prüfungen, Dubletten, Excel) funktioniert dann automatisch,
solange `..._umwandeln` genau die Spalten aus `agent/format.py` liefert.
Braucht das Portal einen API-Key, kommt er in die `.env`-Datei (siehe `.env.example`).
"""
import pandas as pd

from agent.format import SPALTEN


def vorlage_abrufen():
    """Holt die Rohdaten vom Portal, egal in welcher Form (JSON, CSV, XML ...)."""
    raise NotImplementedError("Noch nicht gebaut")


def vorlage_umwandeln(roh):
    """Übersetzt die Rohdaten in das gemeinsame Format (eine Zeile pro Bekanntmachung)."""
    zeilen = []
    # for eintrag in roh:
    #     zeilen.append({"Ausschreibungs ID Platform": ..., "Titel": ..., ...})
    return pd.DataFrame(zeilen, columns=SPALTEN)
