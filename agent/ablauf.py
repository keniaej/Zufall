"""Der Agent: führt Quellen, Dubletten-Erkennung, Prüfungen und Bericht zusammen.

    agent = Agent(quellen, pruefungen, bericht)
    ergebnis = agent.ausfuehren()

Der Agent kennt keine konkrete Plattform und keine konkrete Regel. Er arbeitet nur mit den
Basisklassen Quelle und Pruefung. Neue Quellen und Prüfungen brauchen hier also keine Änderung.
"""
import pandas as pd

from agent.modell import LaufErgebnis, leere_tabelle, verfahrens_ids
from agent.pruefungen.dubletten import DublettenErkennung


class Agent:
    def __init__(self, quellen, pruefungen, kriterien, bericht=None, dubletten=None):
        self.quellen = quellen                          # Liste von Quelle-Objekten
        self.pruefungen = pruefungen                    # Liste von Pruefung-Objekten, in Reihenfolge
        self.kriterien = kriterien                      # für das Produkt bei Dubletten
        self.bericht = bericht                          # z. B. ExcelBericht, oder None (nur rechnen)
        self.dubletten = dubletten or DublettenErkennung()

    def ausfuehren(self):
        """Ein kompletter Lauf. Gibt ein LaufErgebnis zurück."""
        # 0. Ist die Excel-Datei noch geöffnet? Dann gleich abbrechen, nicht erst nach dem Abruf
        if self.bericht:
            self.bericht.pruefen_ob_offen()

        # 1. Alle Quellen abrufen und zusammenführen
        alle, status = self.abrufen()
        print()
        for name, text in status.items():
            print(f"{name}: {text}")

        # 2. Für ALLE Zeilen (auch spätere Dubletten): ZUFALL-Produkt und auf welchen Plattformen
        alle["Zufall Produkt"] = alle["Alle CPV"].map(self.kriterien.produkt_text)
        alle["Gefunden auf"] = self.dubletten.gefunden_auf(alle)

        # 3. Dubletten zuerst, damit danach die neueste Frist geprüft wird
        behalten = self.dubletten.entfernen(alle)
        print("Nach Dubletten:", len(behalten))

        # 4. Prüfungen der Reihe nach, Aussortiertes mit Grund sammeln
        relevant, aussortiert = self.pruefen(behalten)

        ergebnis = LaufErgebnis(
            alle=alle, behalten=behalten, relevant=relevant, aussortiert=aussortiert,
            gesamt=self.ergebnis_je_bekanntmachung(alle, behalten, relevant, aussortiert),
            status=status,
        )
        self.zusammenfassung_ausgeben(ergebnis)

        # 5. Bericht schreiben (die Excel-Datei ist auch die Datenquelle fürs Dashboard)
        if self.bericht:
            pfad = self.bericht.schreiben(ergebnis)
            print(f"\nExcel gespeichert: {pfad}")
        return ergebnis

    def abrufen(self):
        """Ruft jede Quelle einzeln ab. Fällt eine aus, laufen die anderen weiter."""
        tabellen, status = [], {}
        for quelle in self.quellen:
            print(f"Rufe {quelle.name} ab ...")
            try:
                tabelle = quelle.holen()
                tabellen.append(tabelle)
                status[quelle.name] = f"ok, {len(tabelle)} Bekanntmachungen"
            except Exception as fehler:
                status[quelle.name] = f"FEHLER: {fehler}"

        if not tabellen:
            return leere_tabelle(), status
        # ignore_index: jede Zeile bekommt eine eindeutige Nummer. Über diese Nummer wird am Ende
        # für JEDE abgerufene Bekanntmachung festgehalten, was mit ihr passiert ist.
        return pd.concat(tabellen, ignore_index=True), status

    def pruefen(self, tabelle):
        """Wendet alle Prüfungen nacheinander an. -> (relevant, aussortiert)"""
        aussortiert = []
        for pruefung in self.pruefungen:
            tabelle, raus = pruefung.pruefen(tabelle)
            aussortiert.append(raus)
            print(f"{pruefung.name}: {len(raus)} aussortiert, {len(tabelle)} übrig")
        aussortiert = pd.concat(aussortiert) if aussortiert else tabelle.iloc[0:0]   # Zeilennummern behalten
        return tabelle, aussortiert

    def ergebnis_je_bekanntmachung(self, alle, behalten, relevant, aussortiert):
        """Ergänzt die komplette Abruf-Tabelle um die Spalte 'Ergebnis' (und 'Region Landverkehr').
        Ergebnis ist 'relevant', 'aussortiert: <Grund>' oder 'Dublette, behalten wurde ...'.
        Zugeordnet wird über die Zeilennummern, die beim Abruf vergeben wurden."""
        gesamt = alle.copy()
        gesamt["Ergebnis"] = None
        for tabelle in (relevant, aussortiert):
            if "Region Landverkehr" in tabelle.columns:
                gesamt.loc[tabelle.index, "Region Landverkehr"] = tabelle["Region Landverkehr"]

        gesamt.loc[relevant.index, "Ergebnis"] = "relevant"
        if len(aussortiert):
            gesamt.loc[aussortiert.index, "Ergebnis"] = "aussortiert: " + aussortiert["Ausschlussgrund"]

        # Dubletten: abgerufen, aber bei der Dubletten-Erkennung weggefallen
        dubletten = gesamt.index.difference(behalten.index)
        if len(dubletten):
            behalten_als = pd.Series(
                (behalten["Plattform"] + " " + behalten["Ausschreibungs ID Platform"].astype(str)).values,
                index=verfahrens_ids(behalten))
            gesamt.loc[dubletten, "Ergebnis"] = ("Dublette, behalten wurde "
                                                 + verfahrens_ids(gesamt.loc[dubletten]).map(behalten_als))
        return gesamt

    @staticmethod
    def zusammenfassung_ausgeben(ergebnis):
        print("\nRelevant:", len(ergebnis.relevant))
        if len(ergebnis.relevant):
            print(ergebnis.relevant["Zufall Produkt"].value_counts().to_string())
        if len(ergebnis.aussortiert):
            print("\nAussortiert nach Grund:")
            print(ergebnis.aussortiert["Ausschlussgrund"].value_counts().to_string())
