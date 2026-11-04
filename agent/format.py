"""TEIL 2: GEMEINSAMES FORMAT

Der "Vertrag" zwischen den Quellen und dem Rest des Programms.
Jede umwandeln-Funktion muss eine Tabelle mit genau diesen Spalten liefern.
"""
import pandas as pd

SPALTEN = [
    "Ausschreibungs ID Platform",  # ID auf der jeweiligen Plattform
    "Verfahrens ID",               # ID des Vergabeverfahrens, für Dubletten
    "Publikation",                 # Datum (datetime)
    "Art",                         # Art der Bekanntmachung
    "Titel",
    "Vergabe Branchen Code",       # Haupt-CPV-Code
    "Alle CPV",                    # alle CPV-Codes, kommagetrennt
    "Auftraggeber",
    "Stadt",
    "Leistungsort NUTS",           # Regionscodes des Leistungsorts, kommagetrennt
    "Angebotsfrist",               # Datum (datetime) oder leer
    "Fristart",                    # "Angebot", "Teilnahmeantrag" oder "keine Angabe"
    "Plattform",
    "Link zur Plattform",
]


def datum(text):
    """Macht aus '2026-09-08+02:00' oder '2026-12-01Z' ein echtes Datum. Leer bleibt leer."""
    if not text or pd.isna(text):
        return None
    return pd.to_datetime(str(text)[:10])


def erster(wert):
    """Gibt das erste Element zurück, wenn wert eine Liste ist."""
    if isinstance(wert, list) and len(wert) > 0:
        return wert[0]
    return wert


def cpv_passt(code, ziel):
    """CPV-Codes sind ein Baum: 60100000 umfasst alle Codes, die mit 601 beginnen."""
    return str(code).startswith(ziel.rstrip("0"))


def spalten_pruefen(tabelle, quelle):
    """Bricht mit klarer Meldung ab, wenn eine Quelle sich nicht an das Format hält."""
    fehlend = [s for s in SPALTEN if s not in tabelle.columns]
    if fehlend:
        raise ValueError(f"Quelle '{quelle}' liefert diese Spalten nicht: {fehlend}")
    return tabelle[SPALTEN]
