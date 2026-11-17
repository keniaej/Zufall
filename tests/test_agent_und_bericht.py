"""Tests für den ganzen Agenten inklusive Excel, mit Testquellen statt Internet.

Wichtigster Test: test_zweiter_lauf_behaelt_eintraege_von_zufall
Die Übersicht wird abgeglichen, nicht neu aufgebaut. Was ZUFALL einträgt, muss erhalten bleiben.
"""
import pandas as pd
import pytest
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

from agent.ablauf import Agent
from agent.bericht import UEBERSICHT_SPALTEN, ZUFALL_SPALTEN, DateiGeoeffnetFehler, ExcelBericht
from agent.pruefungen import standard_pruefungen
from conftest import FesteQuelle, zeile

IN_ZUKUNFT = pd.Timestamp.today().normalize() + pd.Timedelta(days=30)
VORBEI = pd.Timestamp.today().normalize() - pd.Timedelta(days=3)


def lager(frist=IN_ZUKUNFT):
    """Lager-Ausschreibung, auf beiden Plattformen -> 1x relevant, 1x Dublette"""
    ted = zeile(**{"Ausschreibungs ID Platform": "111-2026", "Verfahrens ID": "v1", "Plattform": "TED",
                   "Publikation": pd.Timestamp("2026-10-01"), "Titel": "Deutschland – Lagerung – Lager für Akten",
                   "Vergabe Branchen Code": "63120000", "Alle CPV": "63120000", "Angebotsfrist": frist,
                   "PLZ": "02625", "Email": "a@b.de", "Link zur Plattform": "https://ted.europa.eu/x",
                   "Fristart": "Angebot"})
    oev = zeile(**{"Ausschreibungs ID Platform": "abc-01", "Verfahrens ID": "v1", "Plattform": "oeffentlichevergabe.de",
                   "Publikation": pd.Timestamp("2026-09-30"), "Titel": "Lager für Akten",
                   "Vergabe Branchen Code": "63120000", "Alle CPV": "63120000", "Angebotsfrist": frist})
    return [ted], [oev]


def bus():
    return [zeile(**{"Ausschreibungs ID Platform": "222-2026", "Verfahrens ID": "v2", "Plattform": "TED",
                     "Publikation": pd.Timestamp("2026-10-02"), "Titel": "Busse",
                     "Vergabe Branchen Code": "60112000", "Alle CPV": "60112000", "Angebotsfrist": IN_ZUKUNFT})]


def paket():
    return [zeile(**{"Ausschreibungs ID Platform": "333-2026", "Verfahrens ID": "v3", "Plattform": "TED",
                     "Publikation": pd.Timestamp("2026-11-01"), "Titel": "Paketversand",
                     "Vergabe Branchen Code": "64121200", "Alle CPV": "64121200", "Angebotsfrist": IN_ZUKUNFT})]


def lauf(kriterien, einstellungen, ted_zeilen, oev_zeilen=()):
    """Ein kompletter Lauf des Agenten mit Testquellen. Gibt den Pfad der Excel-Datei zurück."""
    quellen = [FesteQuelle("TED", list(ted_zeilen)), FesteQuelle("oeffentlichevergabe.de", list(oev_zeilen))]
    agent = Agent(quellen, standard_pruefungen(kriterien), kriterien, bericht=ExcelBericht(einstellungen))
    agent.ausfuehren()
    return agent.bericht.pfad


def test_excel_struktur(kriterien, einstellungen):
    ted, oev = lager()
    pfad = lauf(kriterien, einstellungen, ted + bus(), oev)
    blaetter = pd.read_excel(pfad, sheet_name=None, dtype=str)

    assert list(blaetter) == ["Übersicht", "TED", "oeffentlichevergabe.de", "Status"]
    ueb = blaetter["Übersicht"]
    assert list(ueb.columns) == UEBERSICHT_SPALTEN
    assert list(ueb.columns[:17]) == ZUFALL_SPALTEN
    assert len(ueb) == 1
    assert ueb.loc[0, "PLZ"] == "02625"                       # führende 0 bleibt
    assert ueb.loc[0, "Beschreibung"] == "Lager für Akten"     # TED-Vorspann entfernt
    assert ueb.loc[0, "Vergabe Branchen Code"] == "63120000"   # nur der Code, ohne Text
    assert ueb.loc[0, "Neu"] == "ja"
    assert ueb.loc[0, "Fristart"] == "Angebot"

    ted = blaetter["TED"].set_index("Ausschreibungs ID Platform")["Ergebnis"]
    assert ted["111-2026"] == "relevant"
    assert ted["222-2026"].startswith("aussortiert: Personenverkehr")
    oev_blatt = blaetter["oeffentlichevergabe.de"]
    assert oev_blatt.loc[0, "Ergebnis"] == "Dublette, behalten wurde TED 111-2026"
    assert oev_blatt.loc[0, "Zufall Produkt"] == "Kontraktlogistik"          # auch bei Dubletten
    assert oev_blatt.loc[0, "Gefunden auf"] == "TED, oeffentlichevergabe.de"

    wb = load_workbook(pfad)
    link = wb["Übersicht"].cell(row=2, column=ZUFALL_SPALTEN.index("Link zur Plattform") + 1)
    assert link.hyperlink.target == "https://ted.europa.eu/x"
    # Jedes Blatt ist eine Excel-Tabelle (Strg+T) über den ganzen Bereich
    namen = {ws.title: list(ws.tables) for ws in wb.worksheets}
    assert namen == {"Übersicht": ["Uebersicht"], "TED": ["TED"],
                     "oeffentlichevergabe.de": ["oeffentlichevergabe_de"], "Status": ["Status"]}
    assert wb["TED"].tables["TED"].ref == wb["TED"].dimensions


def test_zweiter_lauf_behaelt_eintraege_von_zufall(kriterien, einstellungen, tmp_path):
    ted, oev = lager()
    pfad = lauf(kriterien, einstellungen, ted + bus(), oev)

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
    ted, oev = lager(frist=VORBEI)
    lauf(kriterien, einstellungen, ted + bus() + paket(), oev)

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


def test_dritter_lauf_ohne_treffer_laesst_zeile_stehen(kriterien, einstellungen):
    ted, oev = lager()
    pfad = lauf(kriterien, einstellungen, ted, oev)
    lauf(kriterien, einstellungen, bus())   # Lager taucht im Abruf gar nicht mehr auf
    ueb = pd.read_excel(pfad, sheet_name="Übersicht", dtype=str).set_index("Verfahrens ID")
    assert ueb.loc["v1", "Status Agent"] == "nicht mehr gefunden"
    assert ueb.loc["v1", "Beschreibung"] == "Lager für Akten"   # Inhalte bleiben stehen


def test_neue_spalte_wird_in_bestehender_uebersicht_ergaenzt(kriterien, einstellungen):
    """Kommt eine neue Agent-Spalte dazu (wie 'Fristart'), wird sie hinten angefügt und befüllt.
    Der Abgleich sucht Spalten über die Überschrift, ZUFALL darf Spalten also verschieben."""
    ted, oev = lager()
    pfad = lauf(kriterien, einstellungen, ted, oev)
    wb = load_workbook(pfad)
    ws = wb["Übersicht"]
    ws.delete_cols([c.column for c in ws[1] if c.value == "Fristart"][0])
    for name in list(ws.tables):
        del ws.tables[name]
    wb.save(pfad)

    lauf(kriterien, einstellungen, ted, oev)
    ueb = pd.read_excel(pfad, sheet_name="Übersicht", dtype=str)
    assert ueb.columns[-1] == "Fristart"
    assert ueb.loc[0, "Fristart"] == "Angebot"


def test_ausgefallene_quelle_stoppt_den_lauf_nicht(kriterien, einstellungen):
    class Kaputt(FesteQuelle):
        def abrufen(self):
            raise ConnectionError("Server nicht erreichbar")

    ted, _ = lager()
    quellen = [FesteQuelle("TED", ted), Kaputt("oeffentlichevergabe.de", [])]
    ergebnis = Agent(quellen, standard_pruefungen(kriterien), kriterien, bericht=ExcelBericht(einstellungen)).ausfuehren()
    assert ergebnis.status["oeffentlichevergabe.de"] == "FEHLER: Server nicht erreichbar"
    assert len(ergebnis.relevant) == 1
    status = pd.read_excel(ExcelBericht(einstellungen).pfad, sheet_name="Status", dtype=str)
    assert "FEHLER: Server nicht erreichbar" in set(status["Wert"])


def test_agent_ohne_bericht_rechnet_nur(kriterien):
    ted, oev = lager()
    ergebnis = Agent([FesteQuelle("TED", ted), FesteQuelle("oeffentlichevergabe.de", oev)],
                     standard_pruefungen(kriterien), kriterien).ausfuehren()
    assert list(ergebnis.gesamt["Ergebnis"]) == ["relevant", "Dublette, behalten wurde TED 111-2026"]


def test_geoeffnete_datei_bricht_frueh_ab(kriterien, einstellungen, monkeypatch):
    ted, oev = lager()
    lauf(kriterien, einstellungen, ted, oev)
    bericht = ExcelBericht(einstellungen)

    def gesperrt(*args, **kwargs):
        raise PermissionError
    monkeypatch.setattr("builtins.open", gesperrt)
    with pytest.raises(DateiGeoeffnetFehler, match="geöffnet"):
        bericht.pruefen_ob_offen()
