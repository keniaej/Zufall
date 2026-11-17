"""Startpunkt. Aus dem Hauptordner des Repos starten mit:
    python -m agent.main

Hier wird der Agent zusammengebaut: Einstellungen und Kriterien laden, Quellen und Prüfungen
erzeugen, Bericht festlegen. Was der Agent dann tut, steht in agent/ablauf.py.
"""
from agent.ablauf import Agent
from agent.bericht import ExcelBericht
from agent.einstellungen import Einstellungen
from agent.kriterien import Kriterien
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


def main():
    return agent_bauen().ausfuehren()


if __name__ == "__main__":
    main()
