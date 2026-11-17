"""TEIL 5: ABLAUF (main)

Hier läuft alles zusammen. Starten aus dem Hauptordner des Repos mit:
    python -m agent.main
"""
import pandas as pd

from agent.excel_export import datei_pruefen, excel_schreiben
from agent.format import SPALTEN, spalten_pruefen
from agent.pruefungen import PRUEFUNGEN, dubletten_entfernen, produkte_ermitteln
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
    # ignore_index: jede Zeile bekommt eine eindeutige Nummer. Über diese Nummer wird am Ende
    # für JEDE abgerufene Bekanntmachung festgehalten, was mit ihr passiert ist.
    return pd.concat(tabellen, ignore_index=True), status


def ergebnis_je_bekanntmachung(alle, behalten, relevant, aussortiert):
    """Ergänzt die komplette Abruf-Tabelle um die Spalte 'Ergebnis' und die berechneten Spalten.
    Ergebnis ist 'relevant', 'aussortiert: <Grund>' oder 'Dublette: ...'."""
    gesamt = alle.copy()
    gesamt["Ergebnis"] = None

    # Region aus den Prüfungen übernehmen (Produkt und "Gefunden auf" siehe unten)
    for tabelle in (relevant, aussortiert):
        for spalte in ("Region Landverkehr",):
            if spalte in tabelle.columns:
                gesamt.loc[tabelle.index, spalte] = tabelle[spalte]

    gesamt.loc[relevant.index, "Ergebnis"] = "relevant"
    if len(aussortiert):
        gesamt.loc[aussortiert.index, "Ergebnis"] = "aussortiert: " + aussortiert["Ausschlussgrund"]

    # Produkt und "Gefunden auf" auch für Dubletten, damit die Spalten überall befüllt sind
    gesamt["Zufall Produkt"] = [", ".join(produkte_ermitteln([c.strip() for c in str(cpv).split(",") if c.strip()]))
                                or None for cpv in gesamt["Alle CPV"]]
    verfahren = gesamt["Verfahrens ID"].fillna(gesamt["Ausschreibungs ID Platform"])
    gesamt["Gefunden auf"] = verfahren.map(behalten.set_index("Verfahrens ID")["Gefunden auf"])

    # Dubletten: abgerufen, aber bei der Dubletten-Prüfung weggefallen
    behalten_je_verfahren = {z["Verfahrens ID"]: f"{z['Plattform']} {z['Ausschreibungs ID Platform']}"
                             for _, z in behalten.iterrows()}
    for nr in gesamt.index.difference(behalten.index):
        verfahren = gesamt.at[nr, "Verfahrens ID"]
        if pd.isna(verfahren):
            verfahren = gesamt.at[nr, "Ausschreibungs ID Platform"]
        gesamt.at[nr, "Ergebnis"] = f"Dublette, behalten wurde {behalten_je_verfahren.get(verfahren, '?')}"
    return gesamt


def main():
    # 0. Ist die Excel-Datei noch geöffnet? Dann gleich abbrechen, nicht erst nach dem Abruf
    datei_pruefen()

    # 1. Alle Quellen abrufen und zusammenführen
    alle, status = alle_quellen_abrufen()
    print()
    for name, text in status.items():
        print(f"{name}: {text}")

    # 2. Dubletten zuerst, damit danach die neueste Frist geprüft wird
    tabelle = dubletten_entfernen(alle)
    behalten = tabelle
    print("Nach Dubletten:", len(tabelle))

    # 3. Prüfungen der Reihe nach, Aussortiertes mit Grund sammeln
    aussortiert = []
    for pruefung in PRUEFUNGEN:
        tabelle, raus = pruefung(tabelle)
        aussortiert.append(raus)
        print(f"{pruefung.__name__}: {len(raus)} aussortiert, {len(tabelle)} übrig")

    aussortiert = pd.concat(aussortiert)   # Zeilennummern behalten (siehe oben)
    relevant = tabelle

    print("\nRelevant:", len(relevant))
    print(relevant["Zufall Produkt"].value_counts().to_string())
    print("\nAussortiert nach Grund:")
    print(aussortiert["Ausschlussgrund"].value_counts().to_string())

    # 4. Excel schreiben (die Datei ist später auch die Datenquelle fürs Dashboard)
    gesamt = ergebnis_je_bekanntmachung(alle, behalten, relevant, aussortiert)
    pfad = excel_schreiben(relevant, gesamt, status)
    print(f"\nExcel gespeichert: {pfad}")

    return relevant, gesamt, status


if __name__ == "__main__":
    main()
