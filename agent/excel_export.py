"""SCHRITT 5: EXCEL-EXPORT

Schreibt in DIESELBE Datei: output/ausschreibungen.xlsx. So kann Power BI fest mit dieser
einen Datei verbunden bleiben.

Blätter:
1. Übersicht:  die relevanten Ausschreibungen in ZUFALLs Zielstruktur.
               Wird NICHT neu aufgebaut, sondern abgeglichen (siehe uebersicht_aktualisieren):
               - bekannte Ausschreibung  -> nur die Spalten des Agenten werden aktualisiert
               - neue Ausschreibung      -> neue Zeile unten, feste interne ID
               - nicht mehr relevant     -> Zeile bleibt stehen, Spalte "Status Agent" sagt warum
               Alles, was ZUFALL selbst einträgt (eigene Spalten, Notizen, Farben), bleibt erhalten.
2. ein Blatt je Plattform (TED, oeffentlichevergabe.de, ...): ALLES, was von dort abgerufen wurde,
               mit Spalte "Ergebnis". Wird bei jedem Lauf komplett neu aufgebaut.
3. Status:     wann der Lauf war, was jede Plattform geliefert hat. Wird neu aufgebaut.

Jedes Blatt ist als Excel-Tabelle formatiert (wie Strg+T), damit Power BI die Daten sauber
als Tabelle erkennt. Tabellennamen: Uebersicht, TED, oeffentlichevergabe_de, Status.

Vor jedem Speichern wird der alte Stand nach output/sicherungen/ kopiert.
"""
import os
import re
import shutil
from datetime import datetime

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from agent.konfiguration import OUTPUT_ORDNER, SEIT_DATUM

DATEINAME = "ausschreibungen.xlsx"
SICHERUNGEN_ORDNER = "sicherungen"
SICHERUNGEN_BEHALTEN = 10
UEBERSICHT = "Übersicht"

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

# Diese Spalten überschreibt der Agent bei jedem Lauf mit dem aktuellen Stand der Plattform
# (siehe agent_werte). Alle anderen Spalten der Übersicht fasst er nach dem ersten Eintragen nicht mehr an.
# Spalten werden über ihre Überschrift gefunden: ZUFALL darf sie in Excel beliebig verschieben.
AGENT_SPALTEN = [s for s in ZUFALL_SPALTEN if s != "Ausschreibungs ID Intern"] + ZUSATZ_SPALTEN + \
                ["Neu", "Status Agent", "Zuletzt aktualisiert am"]

DATUMS_SPALTEN = {"Publikation", "Angebotsfrist", "Vertragsbeginn", "Vertragsende",
                  "Erstmals gefunden am", "Zuletzt aktualisiert am"}
LINK_SPALTEN = {"Link zur Plattform"}
MAIL_SPALTEN = {"Email"}


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def pfad_excel():
    return os.path.join(OUTPUT_ORDNER, DATEINAME)


def datei_pruefen():
    """Vor dem Lauf aufrufen: Ist die Excel-Datei in Excel geöffnet, gleich abbrechen
    (und nicht erst nach mehreren Minuten Abruf)."""
    pfad = pfad_excel()
    if os.path.exists(pfad):
        try:
            with open(pfad, "r+b"):
                pass
        except PermissionError:
            raise PermissionError(f"{pfad} ist gerade geöffnet (z. B. in Excel). Bitte schließen und neu starten.")


def zellwert(wert):
    """pandas-Werte in etwas umwandeln, das openpyxl in eine Zelle schreiben kann."""
    if wert is None:
        return None
    if isinstance(wert, (list, dict)):
        return str(wert)
    try:
        if pd.isna(wert):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(wert, pd.Timestamp):
        return wert.to_pydatetime()
    if hasattr(wert, "item"):            # numpy-Zahlen
        wert = wert.item()
    if isinstance(wert, float) and wert.is_integer():
        return int(wert)
    return wert


def beschreibung(titel, plattform):
    """TED setzt vor jeden Titel 'Land – CPV-Bezeichnung – '. Das steht schon in anderen Spalten."""
    if not isinstance(titel, str):
        return titel
    teile = titel.split(" – ")
    if plattform == "TED" and len(teile) >= 3:
        return " – ".join(teile[2:])
    return titel


def blattname(name):
    """Excel erlaubt max. 31 Zeichen und keine der Zeichen []:*?/\\ im Blattnamen."""
    return re.sub(r"[\[\]:*?/\\]", "_", name)[:31]


def tabellenname(blatt):
    """Name der Excel-Tabelle (wie bei Strg+T). Power BI zeigt die Tabellen unter diesem Namen an.
    Erlaubt sind nur Buchstaben, Ziffern und _, am Anfang ein Buchstabe."""
    for alt, neu in [("Ü", "Ue"), ("ü", "ue"), ("Ö", "Oe"), ("ö", "oe"), ("Ä", "Ae"), ("ä", "ae"), ("ß", "ss")]:
        blatt = blatt.replace(alt, neu)
    name = re.sub(r"[^A-Za-z0-9_]", "_", blatt)
    return name if name[:1].isalpha() else "T_" + name


def als_tabelle(ws):
    """Formatiert den ganzen Bereich als Excel-Tabelle. Eine vorhandene Tabelle wird ersetzt,
    damit sie neue Zeilen und Spalten mit umfasst. Ohne Datenzeile braucht Excel trotzdem
    eine (leere) Zeile unter der Überschrift, sonst gilt die Datei als beschädigt."""
    stil = "TableStyleMedium2"
    for name in list(ws.tables):
        alt = ws.tables[name]
        if alt.tableStyleInfo is not None and alt.tableStyleInfo.name:
            stil = alt.tableStyleInfo.name      # Stil behalten, falls ZUFALL ihn geändert hat
        del ws.tables[name]
    ws.auto_filter.ref = None

    # Eine Tabelle braucht eindeutige, nicht leere Überschriften
    gesehen = set()
    for zelle in ws[1]:
        text = str(zelle.value).strip() if zelle.value is not None else ""
        if not text or text in gesehen:
            text = f"{text or 'Spalte'} {zelle.column}"
        zelle.value = text
        gesehen.add(text)

    letzte_zeile = max(letzte_datenzeile(ws), 2)
    tabelle = Table(displayName=tabellenname(ws.title), ref=f"A1:{get_column_letter(ws.max_column)}{letzte_zeile}")
    tabelle.tableStyleInfo = TableStyleInfo(name=stil, showRowStripes=True)
    ws.add_table(tabelle)


def zelle_formatieren(zelle, spalte, neu_angelegt):
    """Datum, Link, E-Mail. Die Link-Formatvorlage nur bei neuen Zeilen setzen, sonst würde
    eine Farbe, die ZUFALL der Zelle gegeben hat, überschrieben."""
    if spalte in DATUMS_SPALTEN:
        zelle.number_format = "DD.MM.YYYY"
    if spalte in LINK_SPALTEN or spalte in MAIL_SPALTEN:
        if isinstance(zelle.value, str) and zelle.value:
            zelle.hyperlink = ("mailto:" + zelle.value) if spalte in MAIL_SPALTEN else zelle.value
            if neu_angelegt:
                zelle.style = "Hyperlink"
        else:
            zelle.hyperlink = None


def letzte_datenzeile(ws):
    """Letzte Zeile mit Inhalt. ws.max_row zählt auch leere, nur formatierte Zeilen mit
    (z. B. wenn ZUFALL eine ganze Spalte eingefärbt hat). Neue Zeilen kämen sonst mit Lücke darunter."""
    for zeile_nr in range(ws.max_row, 1, -1):
        if any(c.value not in (None, "") for c in ws[zeile_nr]):
            return zeile_nr
    return 1


def spaltenbreite(ws, spalte_nr, ueberschrift):
    werte = [len(str(z[0].value)) for z in ws.iter_rows(min_row=2, min_col=spalte_nr, max_col=spalte_nr)
             if z[0].value is not None]
    ws.column_dimensions[get_column_letter(spalte_nr)].width = min(max([len(ueberschrift)] + werte) + 2, 60)


# ---------------------------------------------------------------------------
# Übersicht: abgleichen statt neu aufbauen
# ---------------------------------------------------------------------------

def verfahrens_id(zeile):
    """Merkmal für den Abgleich. Ohne Verfahrens-ID (kommt bei TED/öffentlichevergabe.de nicht vor)
    die Plattform-ID, genau wie in pruefungen.dubletten_entfernen."""
    vid = zeile.get("Verfahrens ID")
    if vid is None or pd.isna(vid) or vid == "":
        vid = zeile.get("Ausschreibungs ID Platform")
    return str(vid)


def agent_werte(zeile, heute):
    """Werte der Agent-Spalten für eine Ausschreibung (eine Zeile aus 'gesamt')."""
    ergebnis = zeile.get("Ergebnis") or ""
    if ergebnis == "relevant":
        status = "relevant"
    else:
        status = "nicht mehr relevant: " + ergebnis.removeprefix("aussortiert: ")
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
        "Zuletzt aktualisiert am": heute,
    }


def uebersicht_blatt_holen(wb):
    """Vorhandene Übersicht nehmen. Fehlt sie (oder ist sie aus der Zeit vor dem Abgleich,
    also ohne Spalte 'Verfahrens ID'), wird sie neu angelegt. Der alte Stand liegt dann in der Sicherung."""
    if UEBERSICHT in wb.sheetnames:
        ws = wb[UEBERSICHT]
        if "Verfahrens ID" in [c.value for c in ws[1]]:
            return ws, False
        print(f"Hinweis: '{UEBERSICHT}' hat noch keine Spalte 'Verfahrens ID' und wird neu angelegt "
              f"(alter Stand in output/{SICHERUNGEN_ORDNER}/).")
        wb.remove(ws)
    ws = wb.create_sheet(UEBERSICHT, 0)
    for nr, name in enumerate(UEBERSICHT_SPALTEN, start=1):
        ws.cell(row=1, column=nr, value=name)
    return ws, True


def uebersicht_aktualisieren(wb, gesamt, heute):
    """Gleicht die Übersicht mit dem aktuellen Lauf ab. Gibt Zahlen für das Status-Blatt zurück."""
    ws, neu_angelegt = uebersicht_blatt_holen(wb)

    # Fehlende Spalten hinten anfügen (z. B. wenn ZUFALL eine gelöscht hat)
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
            werte = agent_werte(aktuell[vid], heute)
            zahlen["aktualisiert" if werte["Status Agent"] == "relevant" else "nicht mehr relevant"] += 1
        else:
            # Nicht mehr abgerufen (z. B. älter als das Startdatum): Inhalte stehen lassen
            werte = {"Neu": "nein", "Status Agent": "nicht mehr gefunden"}
            zahlen["nicht mehr gefunden"] += 1
        for spalte, wert in werte.items():
            zelle = ws.cell(row=zeile_nr, column=kopf[spalte], value=zellwert(wert))
            zelle_formatieren(zelle, spalte, neu_angelegt=False)

    # 2. Neue relevante Ausschreibungen unten anfügen, nach Frist sortiert, mit fester interner ID
    ist_neu = [z["Ergebnis"] == "relevant" and verfahrens_id(z) not in vorhanden
               for z in behalten.to_dict("records")]
    neue = behalten[ist_neu] if len(behalten) else behalten
    for z in neue.sort_values("Angebotsfrist", na_position="last").to_dict("records"):
        hoechste_id += 1
        werte = agent_werte(z, heute)
        werte.update({"Ausschreibungs ID Intern": hoechste_id, "Neu": "ja",
                      "Erstmals gefunden am": heute, "Verfahrens ID": verfahrens_id(z)})
        letzte += 1
        zeile_nr = letzte
        for spalte, wert in werte.items():
            zelle = ws.cell(row=zeile_nr, column=kopf[spalte], value=zellwert(wert))
            zelle_formatieren(zelle, spalte, neu_angelegt=True)
        zahlen["neu"] += 1

    # 3. Tabelle über den ganzen Bereich; Breite nur für Spalten, die der Agent gerade angelegt hat
    ws.freeze_panes = "A2"
    als_tabelle(ws)
    for name in (UEBERSICHT_SPALTEN if neu_angelegt else neue_spalten):
        spaltenbreite(ws, kopf[name], name)
    return zahlen


# ---------------------------------------------------------------------------
# Plattform-Blätter und Status: jedes Mal neu
# ---------------------------------------------------------------------------

def plattform_tabelle(gesamt, plattform):
    """Alles, was von einer Plattform abgerufen wurde. 'Ergebnis' steht vorne, damit man filtern kann."""
    t = gesamt[gesamt["Plattform"] == plattform].sort_values("Publikation", ascending=False)
    vorne = ["Ergebnis", "Zufall Produkt"]
    return t[[s for s in vorne if s in t.columns] + [s for s in t.columns if s not in vorne]]


def status_tabelle(status, gesamt, zahlen):
    zeilen = [("Letzter Lauf", f"{datetime.now():%d.%m.%Y %H:%M}"),
              ("Bekanntmachungen ab", pd.Timestamp(SEIT_DATUM).strftime("%d.%m.%Y"))]
    zeilen += [(f"Abruf {name}", text) for name, text in status.items()]
    ergebnis = gesamt["Ergebnis"].fillna("").str.replace(r"^Dublette.*", "Dublette", regex=True)
    zeilen += [(f"Abgerufen: {wert}", anzahl) for wert, anzahl in ergebnis.value_counts().items()]
    zeilen += [(f"Übersicht: {wert}", anzahl) for wert, anzahl in zahlen.items()]
    return pd.DataFrame(zeilen, columns=["Punkt", "Wert"])


def blatt_neu_schreiben(wb, name, tabelle, position):
    if name in wb.sheetnames:
        wb.remove(wb[name])
    ws = wb.create_sheet(name, position)
    spalten = list(tabelle.columns)
    ws.append(spalten)
    for zeile in tabelle.itertuples(index=False):
        ws.append([zellwert(w) for w in zeile])
    for nr, spalte in enumerate(spalten, start=1):
        for (zelle,) in ws.iter_rows(min_row=2, min_col=nr, max_col=nr):
            zelle_formatieren(zelle, spalte, neu_angelegt=True)
        spaltenbreite(ws, nr, str(spalte))
    for zelle in ws[1]:
        zelle.alignment = Alignment(vertical="center")
    ws.freeze_panes = "A2"
    als_tabelle(ws)


# ---------------------------------------------------------------------------
# Speichern
# ---------------------------------------------------------------------------

def sichern(pfad):
    """Kopie des alten Stands nach output/sicherungen/, die letzten SICHERUNGEN_BEHALTEN bleiben."""
    if not os.path.exists(pfad):
        return
    ordner = os.path.join(OUTPUT_ORDNER, SICHERUNGEN_ORDNER)
    os.makedirs(ordner, exist_ok=True)
    shutil.copy2(pfad, os.path.join(ordner, f"ausschreibungen_{datetime.now():%Y-%m-%d_%H%M%S}.xlsx"))
    alte = sorted(f for f in os.listdir(ordner) if f.startswith("ausschreibungen_") and f.endswith(".xlsx"))
    for datei in alte[:-SICHERUNGEN_BEHALTEN]:
        os.remove(os.path.join(ordner, datei))


def excel_schreiben(relevant, gesamt, status):
    """relevant wird aktuell nicht gebraucht (steckt in gesamt)."""
    os.makedirs(OUTPUT_ORDNER, exist_ok=True)
    pfad = pfad_excel()
    datei_pruefen()
    heute = pd.Timestamp.today().normalize()

    if os.path.exists(pfad):
        wb = load_workbook(pfad)
    else:
        wb = Workbook()
        wb.remove(wb.active)

    zahlen = uebersicht_aktualisieren(wb, gesamt, heute)
    position = 1
    for plattform in status:   # gleiche Reihenfolge wie die Quellen, auch wenn eine ausgefallen ist
        blatt_neu_schreiben(wb, blattname(plattform), plattform_tabelle(gesamt, plattform), position)
        position += 1
    blatt_neu_schreiben(wb, "Status", status_tabelle(status, gesamt, zahlen), position)
    wb.active = 0

    # Erst in eine Zwischendatei schreiben, dann austauschen: bricht etwas ab, bleibt die alte Datei heil
    sichern(pfad)
    zwischen = pfad + ".neu"
    wb.save(zwischen)
    try:
        os.replace(zwischen, pfad)
    except PermissionError:
        os.remove(zwischen)
        raise PermissionError(f"{pfad} ist gerade geöffnet (z. B. in Excel). Bitte schließen und neu starten.")
    return pfad
