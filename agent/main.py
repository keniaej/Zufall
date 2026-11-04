"""TEIL 5: ABLAUF (main)

Hier läuft alles zusammen. Starten aus dem Hauptordner des Repos mit:
    python -m agent.main
"""
import pandas as pd

from agent.excel_export import excel_schreiben
from agent.format import SPALTEN, spalten_pruefen
from agent.ki_bewertung import ki_bewerten
from agent.pruefungen import PRUEFUNGEN, dubletten_entfernen
from agent.quellen import QUELLEN


def alle_quellen_abrufen():
    """Ruft jede Quelle einzeln ab. Fällt eine aus, laufen die anderen weiter."""
    tabellen = []
    status = {}

    for quelle in QUELLEN:
        name = quelle["name"]
        print(f"Rufe {name} ab ...")
        try:
            roh = quelle["abrufen"]()
            tabelle = spalten_pruefen(quelle["umwandeln"](roh), name)
            tabellen.append(tabelle)
            status[name] = f"ok, {len(tabelle)} Bekanntmachungen"
        except Exception as fehler:
            status[name] = f"FEHLER: {fehler}"

    if not tabellen:
        return pd.DataFrame(columns=SPALTEN), status
    return pd.concat(tabellen, ignore_index=True), status


def main():
    # 1. Alle Quellen abrufen und zusammenführen
    tabelle, status = alle_quellen_abrufen()
    print()
    for name, text in status.items():
        print(f"{name}: {text}")

    # 2. Dubletten zuerst, damit danach die neueste Frist geprüft wird
    tabelle = dubletten_entfernen(tabelle)
    print("Nach Dubletten:", len(tabelle))

    # 3. Prüfungen der Reihe nach, Aussortiertes mit Grund sammeln
    aussortiert = []
    for pruefung in PRUEFUNGEN:
        tabelle, raus = pruefung(tabelle)
        aussortiert.append(raus)
        print(f"{pruefung.__name__}: {len(raus)} aussortiert, {len(tabelle)} übrig")

    aussortiert = pd.concat(aussortiert, ignore_index=True)
    relevant = tabelle

    print("\nRelevant:", len(relevant))
    print(relevant["Zufall Produkt"].value_counts().to_string())
    print("\nAussortiert nach Grund:")
    print(aussortiert["Ausschlussgrund"].value_counts().to_string())

    # 4. KI-Bewertung (OFFEN)
    relevant = ki_bewerten(relevant)

    # 5. Excel schreiben (die Datei ist später auch die Datenquelle fürs Dashboard)
    pfad = excel_schreiben(relevant, aussortiert, status)
    print(f"\nExcel gespeichert: {pfad}")

    return relevant, aussortiert, status


if __name__ == "__main__":
    main()
