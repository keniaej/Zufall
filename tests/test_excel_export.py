"""Tests für Ablauf und Excel-Export mit erfundenen Daten (ohne Internet).

Wichtigster Test: test_zweiter_lauf_behaelt_eintraege_von_zufall
Die Übersicht wird abgeglichen, nicht neu aufgebaut. Was ZUFALL einträgt, muss erhalten bleiben.
"""
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

from agent import excel_export
from agent.format import SPALTEN
from agent.main import ergebnis_je_bekanntmachung
from agent.pruefungen import PRUEFUNGEN, dubletten_entfernen

IN_ZUKUNFT = pd.Timestamp.today().normalize() + pd.Timedelta(days=30)
VORBEI = pd.Timestamp.today().normalize() - pd.Timedelta(days=3)


def zeile(**werte):
    basis = {s: None for s in SPALTEN}
    basis.update(werte)
    return basis


def lager(frist=IN_ZUKUNFT):
    """Lager-Ausschreibung, auf beiden Plattformen -> 1x relevant, 1x Dublette"""
    return [
        zeile(**{"Ausschreibungs ID Platform": "111-2026", "Verfahrens ID": "v1", "Plattform": "TED",
                 "Publikation": pd.Timestamp("2026-10-01"), "Titel": "Deutschland – Lagerung – Lager für Akten",
                 "Vergabe Branchen Code": "63120000", "Alle CPV": "63120000", "Angebotsfrist": frist,
                 "PLZ": "02625", "Email": "a@b.de", "Link zur Plattform": "https://ted.europa.eu/x",
                 "Fristart": "Angebot"}),
        zeile(**{"Ausschreibungs ID Platform": "abc-01", "Verfahrens ID": "v1", "Plattform": "oeffentlichevergabe.de",
                 "Publikation": pd.Timestamp("2026-09-30"), "Titel": "Lager für Akten",
                 "Vergabe Branchen Code": "63120000", "Alle CPV": "63120000", "Angebotsfrist": frist}),
    ]


def bus():
    return [zeile(**{"Ausschreibungs ID Platform": "222-2026", "Verfahrens ID": "v2", "Plattform": "TED",
                     "Publikation": pd.Timestamp("2026-10-02"), "Titel": "Busse",
                     "Vergabe Branchen Code": "60112000", "Alle CPV": "60112000", "Angebotsfrist": IN_ZUKUNFT})]


def paket():
    return [zeile(**{"Ausschreibungs ID Platform": "333-2026", "Verfahrens ID": "v3", "Plattform": "TED",
                     "Publikation": pd.Timestamp("2026-11-01"), "Titel": "Paketversand",
                     "Vergabe Branchen Code": "64121200", "Alle CPV": "64121200", "Angebotsfrist": IN_ZUKUNFT})]


def lauf(zeilen):
    """Ein Durchlauf wie in main(), nur ohne Abruf."""
    alle = pd.DataFrame(zeilen)
    behalten = tabelle = dubletten_entfernen(alle)
    raus = []
    for pruefung in PRUEFUNGEN:
        tabelle, r = pruefung(tabelle)
        raus.append(r)
    gesamt = ergebnis_je_bekanntmachung(alle, behalten, tabelle, pd.concat(raus))
    status = {"TED": "ok", "oeffentlichevergabe.de": "ok"}
    return excel_export.excel_schreiben(tabelle, gesamt, status)


def test_excel_struktur(tmp_path, monkeypatch):
    monkeypatch.setattr(excel_export, "OUTPUT_ORDNER", str(tmp_path))
    pfad = lauf(lager() + bus())
    blaetter = pd.read_excel(pfad, sheet_name=None, dtype=str)

    assert list(blaetter) == ["Übersicht", "TED", "oeffentlichevergabe.de", "Status"]
    ueb = blaetter["Übersicht"]
    assert list(ueb.columns) == excel_export.UEBERSICHT_SPALTEN
    assert list(ueb.columns[:17]) == excel_export.ZUFALL_SPALTEN
    assert len(ueb) == 1
    assert ueb.loc[0, "PLZ"] == "02625"                       # führende 0 bleibt
    assert ueb.loc[0, "Beschreibung"] == "Lager für Akten"     # TED-Vorspann entfernt
    assert ueb.loc[0, "Vergabe Branchen Code"] == "63120000"   # nur der Code, ohne Text
    assert ueb.loc[0, "Neu"] == "ja"

    ted = blaetter["TED"].set_index("Ausschreibungs ID Platform")["Ergebnis"]
    assert ted["111-2026"] == "relevant"
    assert ted["222-2026"].startswith("aussortiert: Personenverkehr")
    assert blaetter["oeffentlichevergabe.de"].loc[0, "Ergebnis"] == "Dublette, behalten wurde TED 111-2026"

    wb = load_workbook(pfad)
    link = wb["Übersicht"].cell(row=2, column=excel_export.ZUFALL_SPALTEN.index("Link zur Plattform") + 1)
    assert link.hyperlink.target == "https://ted.europa.eu/x"
    # Jedes Blatt ist eine Excel-Tabelle (Strg+T) über den ganzen Bereich
    namen = {ws.title: list(ws.tables) for ws in wb.worksheets}
    assert namen == {"Übersicht": ["Uebersicht"], "TED": ["TED"],
                     "oeffentlichevergabe.de": ["oeffentlichevergabe_de"], "Status": ["Status"]}
    assert wb["TED"].tables["TED"].ref == wb["TED"].dimensions


def test_zweiter_lauf_behaelt_eintraege_von_zufall(tmp_path, monkeypatch):
    monkeypatch.setattr(excel_export, "OUTPUT_ORDNER", str(tmp_path))
    pfad = lauf(lager() + bus())

    # ZUFALL trägt etwas ein: Entscheidung, Kommentar, eigene Spalte, Zellfarbe
    wb = load_workbook(pfad)
    ws = wb["Übersicht"]
    kopf = {c.value: c.column for c in ws[1]}
    ws.cell(row=2, column=kopf["Entscheidung"], value="teilnehmen")
    ws.cell(row=2, column=kopf["Kommentar"], value="Eike fragt nach")
    ws.cell(row=1, column=ws.max_column + 1, value="Ansprechpartner ZUFALL")
    ws.cell(row=2, column=ws.max_column, value="Frau Muster")
    ws.cell(row=2, column=kopf["Auftraggeber"]).fill = PatternFill("solid", fgColor="FFFF00")
    wb.save(pfad)

    # Zweiter Lauf: Lager-Frist inzwischen abgelaufen, Paket neu dazugekommen
    lauf(lager(frist=VORBEI) + bus() + paket())

    wb = load_workbook(pfad)
    ws = wb["Übersicht"]
    ueb = pd.read_excel(pfad, sheet_name="Übersicht", dtype=str).set_index("Verfahrens ID")

    # Einträge von ZUFALL sind noch da
    assert ueb.loc["v1", "Entscheidung"] == "teilnehmen"
    assert ueb.loc["v1", "Kommentar"] == "Eike fragt nach"
    assert ueb.loc["v1", "Ansprechpartner ZUFALL"] == "Frau Muster"
    kopf = {c.value: c.column for c in ws[1]}
    assert ws.cell(row=2, column=kopf["Auftraggeber"]).fill.fgColor.rgb.endswith("FFFF00")

    # Lager bleibt stehen, mit Grund; Paket kommt neu dazu mit der nächsten festen ID
    assert ueb.loc["v1", "Status Agent"] == "nicht mehr relevant: Frist abgelaufen"
    assert ueb.loc["v1", "Neu"] == "nein"
    assert ueb.loc["v1", "Ausschreibungs ID Intern"] == "1"
    assert ueb.loc["v3", "Neu"] == "ja"
    assert ueb.loc["v3", "Ausschreibungs ID Intern"] == "2"
    assert len(ueb) == 2

    # Tabelle umfasst auch die neue Zeile und die eigene Spalte von ZUFALL
    assert ws.tables["Uebersicht"].ref == f"A1:{ws.cell(row=1, column=ws.max_column).column_letter}3"
    # Alter Stand wurde gesichert
    assert len(list((tmp_path / "sicherungen").glob("ausschreibungen_*.xlsx"))) == 1


def test_dritter_lauf_ohne_treffer_laesst_zeile_stehen(tmp_path, monkeypatch):
    monkeypatch.setattr(excel_export, "OUTPUT_ORDNER", str(tmp_path))
    pfad = lauf(lager())
    lauf(bus())   # Lager taucht im Abruf gar nicht mehr auf
    ueb = pd.read_excel(pfad, sheet_name="Übersicht", dtype=str).set_index("Verfahrens ID")
    assert ueb.loc["v1", "Status Agent"] == "nicht mehr gefunden"
    assert ueb.loc["v1", "Beschreibung"] == "Lager für Akten"   # Inhalte bleiben stehen


def test_dublette_hat_produkt_und_fundstellen(tmp_path, monkeypatch):
    monkeypatch.setattr(excel_export, "OUTPUT_ORDNER", str(tmp_path))
    pfad = lauf(lager())
    oev = pd.read_excel(pfad, sheet_name="oeffentlichevergabe.de", dtype=str)
    assert oev.loc[0, "Ergebnis"].startswith("Dublette")
    assert oev.loc[0, "Zufall Produkt"] == "Kontraktlogistik"
    assert oev.loc[0, "Gefunden auf"] == "TED, oeffentlichevergabe.de"


def test_neue_spalte_wird_in_bestehender_uebersicht_ergaenzt(tmp_path, monkeypatch):
    """Kommt eine neue Agent-Spalte dazu (wie 'Fristart'), wird sie hinten angefügt und befüllt.
    Der Abgleich sucht Spalten über die Überschrift, ZUFALL darf Spalten also verschieben."""
    monkeypatch.setattr(excel_export, "OUTPUT_ORDNER", str(tmp_path))
    pfad = lauf(lager())
    wb = load_workbook(pfad)
    ws = wb["Übersicht"]
    spalte = [c.column for c in ws[1] if c.value == "Fristart"][0]
    ws.delete_cols(spalte)
    for name in list(ws.tables):
        del ws.tables[name]
    wb.save(pfad)

    lauf(lager())
    ueb = pd.read_excel(pfad, sheet_name="Übersicht", dtype=str)
    assert ueb.columns[-1] == "Fristart"
    assert ueb.loc[0, "Fristart"] == "Angebot"
