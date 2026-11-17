"""Startpunkt. Aus dem Hauptordner des Repos starten mit:
    python -m agent.main
    python -m agent.main --protokoll output/log.txt     (Ausgabe zusätzlich in eine Datei)

Unter Windows einfacher: Doppelklick auf "Agent starten.bat" im Hauptordner.

Hier wird der Agent zusammengebaut: Einstellungen und Kriterien laden, Quellen und Prüfungen
erzeugen, Bericht festlegen. Was der Agent dann tut, steht in agent/ablauf.py.
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

from agent.ablauf import Agent
from agent.bericht import DateiGeoeffnetFehler, ExcelBericht
from agent.einstellungen import Einstellungen
from agent.kriterien import Kriterien, KriterienFehler
from agent.pruefungen import standard_pruefungen
from agent.quellen import alle_quellen


def agent_bauen(einstellungen=None):
    einstellungen = einstellungen or Einstellungen()
    kriterien = Kriterien.laden(einstellungen.kriterien_ordner)
    return Agent(
        quellen=alle_quellen(kriterien, einstellungen),
        pruefungen=standard_pruefungen(kriterien),
        kriterien=kriterien,
        bericht=ExcelBericht(einstellungen),
    )


class Protokoll:
    """Schreibt alles, was auf dem Bildschirm erscheint, zusätzlich in eine Datei (angehängt)."""

    def __init__(self, bildschirm, datei):
        self.bildschirm = bildschirm
        self.datei = datei

    def write(self, text):
        self.bildschirm.write(text)
        self.datei.write(text)
        self.datei.flush()

    def flush(self):
        self.bildschirm.flush()
        self.datei.flush()


def main(argumente=None):
    parser = argparse.ArgumentParser(description="Agent Öffentliche Ausschreibungen (ZUFALL)")
    parser.add_argument("--protokoll", help="Ausgabe zusätzlich an diese Datei anhängen, z. B. output/log.txt")
    args = parser.parse_args(argumente)

    if args.protokoll:
        Path(args.protokoll).parent.mkdir(parents=True, exist_ok=True)
        datei = open(args.protokoll, "a", encoding="utf-8")
        datei.write(f"\n===== Lauf vom {datetime.now():%d.%m.%Y %H:%M} =====\n")
        sys.stdout = Protokoll(sys.__stdout__, datei)
        sys.stderr = Protokoll(sys.__stderr__, datei)

    # Bekannte Probleme mit verständlicher Meldung statt Python-Fehlerseite.
    # Rückgabewert 1 = Fehler (wichtig für "Agent starten.bat" und die Aufgabenplanung).
    try:
        agent_bauen().ausfuehren()
    except DateiGeoeffnetFehler as fehler:
        print(f"\nABBRUCH: {fehler}")
        return 1
    except KriterienFehler as fehler:
        print(f"\nABBRUCH: Fehler in den Kriterien. {fehler}")
        print("Bitte die genannte CSV-Datei im Ordner kriterien/ korrigieren (Anleitung: kriterien/README.md).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
