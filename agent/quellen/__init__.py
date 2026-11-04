"""TEIL 3: QUELLEN (ADAPTER)

Jede Quelle hat zwei Funktionen:
1. ..._abrufen()        holt die Rohdaten, egal in welcher Form
2. ..._umwandeln(roh)   übersetzt sie in das gemeinsame Format aus agent/format.py

Eigenheiten einer Plattform bleiben in ihrer eigenen Datei.
Neue Quelle hinzufügen: siehe vorlage.py
"""
from agent.quellen.oeffentlichevergabe import oev_abrufen, oev_umwandeln
from agent.quellen.ted import ted_abrufen, ted_umwandeln

QUELLEN = [
    {"name": "TED", "abrufen": ted_abrufen, "umwandeln": ted_umwandeln},
    {"name": "oeffentlichevergabe.de", "abrufen": oev_abrufen, "umwandeln": oev_umwandeln},
]
