"""Blatt "Übersicht": die relevanten Ausschreibungen in ZUFALLs Zielstruktur.

Wird NICHT neu aufgebaut, sondern bei jedem Lauf abgeglichen:
- bekannte Ausschreibung  -> nur die Spalten des Agenten werden aktualisiert
- neue Ausschreibung      -> neue Zeile unten, feste interne ID
- nicht mehr relevant     -> Zeile bleibt stehen, Spalte "Status Agent" sagt warum
Alles, was ZUFALL selbst einträgt (eigene Spalten, Notizen, Farben), bleibt erhalten.
Spalten werden über ihre Überschrift gefunden: ZUFALL darf sie in Excel beliebig verschieben.
"""
from agent.bericht.excel_hilfen import als_tabelle, letzte_datenzeile, spaltenbreite, zelle_formatieren, zellwert
from agent.modell import verfahrens_id

# ZUFALLs Zielstruktur, Reihenfolge wie in "Berichtsstruktur Öffentliche Transportausschreibungen.xlsx"
ZUFALL_SPALTEN = [
    "Ausschreibungs ID Intern", "Ausschreibungs ID Platform", "Vergabe Branchen Code", "Zufall Produkt",
    "Auftraggeber", "Email", "Stadt", "Straße", "PLZ", "Land", "Vergabeart", "Publikation",
    "Angebotsfrist", "Vertragsdauer in Monaten", "Plattform", "Link zur Plattform", "Beschreibung",
]
# Zusätzliche Daten-Spalten des Agenten (nicht in ZUFALLs Zielstruktur).
# Fristart: wofür die Frist gilt (Angebot / Teilnahmeantrag) oder "keine Angabe" in der Bekanntmachung
ZUSATZ_SPALTEN = ["Fristart"]
# Spalten für ZUFALLs eigene Einträge. Der Agent legt sie an, schreibt aber NIE hinein.
ZUFALL_EIGENE_SPALTEN = ["Entscheidung", "Kommentar"]
# Spalten, mit denen der Agent den Abgleich nachvollziehbar macht
ABGLEICH_SPALTEN = ["Neu", "Status Agent", "Erstmals gefunden am", "Zuletzt aktualisiert am", "Verfahrens ID"]

UEBERSICHT_SPALTEN = ZUFALL_SPALTEN + ZUSATZ_SPALTEN + ZUFALL_EIGENE_SPALTEN + ABGLEICH_SPALTEN


def beschreibung(titel, plattform):
    """TED setzt vor jeden Titel 'Land – CPV-Bezeichnung – '. Das steht schon in anderen Spalten."""
    if not isinstance(titel, str):
        return titel
    teile = titel.split(" – ")
    if plattform == "TED" and len(teile) >= 3:
        return " – ".join(teile[2:])
    return titel


class UebersichtAbgleich:
    """Gleicht das Blatt "Übersicht" einer geöffneten Arbeitsmappe mit einem Lauf ab."""

    BLATT = "Übersicht"

    def __init__(self, heute):
        self.heute = heute

    def agent_werte(self, zeile):
        """Werte der Agent-Spalten für eine Ausschreibung (eine Zeile aus 'gesamt').
        Nur diese Spalten überschreibt der Agent bei jedem Lauf."""
        ergebnis = zeile.get("Ergebnis") or ""
        status = "relevant" if ergebnis == "relevant" else "nicht mehr relevant: " + ergebnis.removeprefix("aussortiert: ")
        return {
            "Ausschreibungs ID Platform": zeile.get("Ausschreibungs ID Platform"),
            # Nur der 8-stellige Code, ohne Text, damit man einheitlich danach filtern kann
            "Vergabe Branchen Code": zeile.get("Vergabe Branchen Code"),
            "Zufall Produkt": zeile.get("Zufall Produkt"),
            "Auftraggeber": zeile.get("Auftraggeber"),
            "Email": zeile.get("Email"),
            "Stadt": zeile.get("Stadt"),
            "Straße": zeile.get("Straße"),
            "PLZ": zeile.get("PLZ"),
            "Land": zeile.get("Land"),
            "Vergabeart": zeile.get("Vergabeart"),
            "Publikation": zeile.get("Publikation"),
            "Angebotsfrist": zeile.get("Angebotsfrist"),
            "Fristart": zeile.get("Fristart"),
            "Vertragsdauer in Monaten": zeile.get("Vertragsdauer in Monaten"),
            "Plattform": zeile.get("Gefunden auf"),   # z. B. "TED, oeffentlichevergabe.de", wenn auf beiden
            "Link zur Plattform": zeile.get("Link zur Plattform"),
            "Beschreibung": beschreibung(zeile.get("Titel"), zeile.get("Plattform")),
            "Neu": "nein",
            "Status Agent": status,
            "Zuletzt aktualisiert am": self.heute,
        }

    def blatt_holen(self, wb):
        """Vorhandene Übersicht nehmen. Fehlt sie (oder ist sie aus der Zeit vor dem Abgleich,
        also ohne Spalte 'Verfahrens ID'), wird sie neu angelegt. Der alte Stand liegt dann in der Sicherung."""
        if self.BLATT in wb.sheetnames:
            ws = wb[self.BLATT]
            if "Verfahrens ID" in [c.value for c in ws[1]]:
                return ws, False
            print(f"Hinweis: '{self.BLATT}' hat noch keine Spalte 'Verfahrens ID' und wird neu angelegt "
                  f"(alter Stand in der Sicherung).")
            wb.remove(ws)
        ws = wb.create_sheet(self.BLATT, 0)
        for nr, name in enumerate(UEBERSICHT_SPALTEN, start=1):
            ws.cell(row=1, column=nr, value=name)
        return ws, True

    def aktualisieren(self, wb, gesamt):
        """Gleicht die Übersicht ab. Gibt Zahlen für das Status-Blatt zurück."""
        ws, neu_angelegt = self.blatt_holen(wb)

        # Fehlende Spalten hinten anfügen (z. B. wenn ZUFALL eine gelöscht hat oder eine neue dazukommt)
        kopf = {c.value: c.column for c in ws[1] if c.value is not None}
        neue_spalten = []
        for name in UEBERSICHT_SPALTEN:
            if name not in kopf:
                nr = ws.max_column + 1
                ws.cell(row=1, column=nr, value=name)
                kopf[name] = nr
                neue_spalten.append(name)

        # Pro Verfahren die eine behaltene Zeile (relevant oder aussortiert, keine Dublette)
        behalten = gesamt[~gesamt["Ergebnis"].fillna("").str.startswith("Dublette")]
        aktuell = {verfahrens_id(z): z for z in behalten.to_dict("records")}

        # 1. Vorhandene Zeilen aktualisieren
        vorhanden, hoechste_id = set(), 0
        zahlen = {"neu": 0, "aktualisiert": 0, "nicht mehr relevant": 0, "nicht mehr gefunden": 0}
        letzte = letzte_datenzeile(ws)
        for zeile_nr in range(2, letzte + 1):
            vid = ws.cell(row=zeile_nr, column=kopf["Verfahrens ID"]).value
            intern = ws.cell(row=zeile_nr, column=kopf["Ausschreibungs ID Intern"]).value
            if isinstance(intern, (int, float)):
                hoechste_id = max(hoechste_id, int(intern))
            if vid is None or str(vid).strip() == "":
                continue                                   # z. B. eine Zeile, die ZUFALL selbst angelegt hat
            vid = str(vid)
            vorhanden.add(vid)

            if vid in aktuell:
                werte = self.agent_werte(aktuell[vid])
                zahlen["aktualisiert" if werte["Status Agent"] == "relevant" else "nicht mehr relevant"] += 1
            else:
                # Nicht mehr abgerufen (z. B. älter als das Startdatum): Inhalte stehen lassen
                werte = {"Neu": "nein", "Status Agent": "nicht mehr gefunden"}
                zahlen["nicht mehr gefunden"] += 1
            self._zeile_schreiben(ws, kopf, zeile_nr, werte, neu_angelegt=False)

        # 2. Neue relevante Ausschreibungen unten anfügen, nach Frist sortiert, mit fester interner ID
        ist_neu = [z["Ergebnis"] == "relevant" and verfahrens_id(z) not in vorhanden
                   for z in behalten.to_dict("records")]
        neue = behalten[ist_neu] if len(behalten) else behalten
        for z in neue.sort_values("Angebotsfrist", na_position="last").to_dict("records"):
            hoechste_id += 1
            letzte += 1
            werte = self.agent_werte(z)
            werte.update({"Ausschreibungs ID Intern": hoechste_id, "Neu": "ja",
                          "Erstmals gefunden am": self.heute, "Verfahrens ID": verfahrens_id(z)})
            self._zeile_schreiben(ws, kopf, letzte, werte, neu_angelegt=True)
            zahlen["neu"] += 1

        # 3. Tabelle über den ganzen Bereich; Breite nur für Spalten, die der Agent gerade angelegt hat
        ws.freeze_panes = "A2"
        als_tabelle(ws)
        for name in (UEBERSICHT_SPALTEN if neu_angelegt else neue_spalten):
            spaltenbreite(ws, kopf[name], name)
        return zahlen

    @staticmethod
    def _zeile_schreiben(ws, kopf, zeile_nr, werte, neu_angelegt):
        for spalte, wert in werte.items():
            zelle = ws.cell(row=zeile_nr, column=kopf[spalte], value=zellwert(wert))
            zelle_formatieren(zelle, spalte, neu_angelegt)
