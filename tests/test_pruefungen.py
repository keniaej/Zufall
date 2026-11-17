"""Tests ohne Internet: prüfen, ob die Regeln richtig rechnen.
Starten mit:  python -m pytest
"""
import pandas as pd

from agent.format import cpv_passt
from agent.pruefungen import cpv_pruefen, produkte_ermitteln, schlagwoerter_pruefen


def test_cpv_baum():
    assert cpv_passt("60161000", "60100000")
    assert not cpv_passt("60600000", "60100000")


def test_oberbegriff_nur_eigene_abteilung():
    # 60000000 umfasst alles mit 60, aber nicht 66000000 (Finanzdienste)
    assert cpv_passt("60112000", "60000000")
    assert not cpv_passt("66000000", "60000000")
    assert not cpv_passt("63120000", "60000000")


def test_genauester_code_gewinnt():
    # 60161000 ist NSE, obwohl es im CPV-Baum unter Landverkehr (60100000) liegt
    assert produkte_ermitteln(["60161000"]) == ["NSE"]
    assert produkte_ermitteln(["60100000"]) == ["Landverkehr"]
    # 60183000 Lieferwagen ist NSE, 60181000 Lkw ist Landverkehr (beide unter 60180000)
    assert produkte_ermitteln(["60183000"]) == ["NSE"]
    assert produkte_ermitteln(["60181000"]) == ["Landverkehr"]
    # Oberbegriff nur, wenn kein genauerer Code passt
    assert produkte_ermitteln(["60300000"]) == ["Transport allgemein"]
    assert produkte_ermitteln(["66000000"]) == []


def test_ausschluss_code_sortiert_aus():
    tabelle = pd.DataFrame({
        "Alle CPV": ["60112000, 60100000", "60100000"],
        "Vergabe Branchen Code": ["60112000", "60100000"],
    })
    behalten, raus = cpv_pruefen(tabelle)
    assert list(raus["Ausschlussgrund"]) == ["Personenverkehr (Hauptcode)"]
    assert len(behalten) == 1


def test_schlagwort_sortiert_aus():
    tabelle = pd.DataFrame({"Titel": ["Schülerbeförderung Kassel", "Lagerlogistik"]})
    behalten, raus = schlagwoerter_pruefen(tabelle)
    assert list(behalten["Titel"]) == ["Lagerlogistik"]
    assert len(raus) == 1


def test_laufzeit():
    from agent.format import laufzeit
    # Dauer mit Einheit hat Vorrang
    assert laufzeit(["2"], ["YEAR"], [], [])[0] == 24
    # Nur Start und Ende (so bei ca. 60 % der TED-Treffer)
    monate, beginn, ende = laufzeit([], [], ["2027-02-01+01:00"], ["2031-01-31+01:00"])
    assert monate == 48
    assert str(beginn.date()) == "2027-02-01" and str(ende.date()) == "2031-01-31"
    # Mehrere Lose: frühester Beginn, spätestes Ende
    monate, beginn, ende = laufzeit([], [], ["2027-01-01", "2027-03-01"], ["2027-12-31", "2028-12-31"])
    assert monate == 24 and str(beginn.date()) == "2027-01-01" and str(ende.date()) == "2028-12-31"
    # Sehr kurzer Auftrag -> mindestens 1 Monat; nichts angegeben -> leer
    assert laufzeit([], [], ["2027-03-15"], ["2027-03-20"])[0] == 1
    assert laufzeit([], [], [], []) == (None, None, None)
    # Nur Beginn bekannt -> keine Dauer, aber Beginn
    monate, beginn, ende = laufzeit([], [], ["2027-01-01"], [])
    assert monate is None and ende is None and beginn is not None


def test_sprachtext_ted():
    from agent.quellen.ted import sprachtext
    assert sprachtext({"deu": ["Polizei Köln"], "eng": ["Police Cologne"]}) == "Polizei Köln"
    assert sprachtext({"eng": ["Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ) GmbH"]}) \
        == "Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ) GmbH"
    assert sprachtext({"dan": ["Ørsted A/S"]}) == "Ørsted A/S"
    assert sprachtext(None) is None


def test_text_bereinigen():
    from agent.format import text_bereinigen
    assert text_bereinigen("Postdienst\r\nfür  Stadt\tX ") == "Postdienst für Stadt X"
    assert text_bereinigen("   ") is None
    assert text_bereinigen(None) is None


def test_xml_dateien_zuordnen():
    from agent.quellen.oeffentlichevergabe import xml_dateien_je_bekanntmachung, version_nr
    dateien = xml_dateien_je_bekanntmachung([
        "420293de-31e0-4847-8778-5844d4bd6263-1.xml",
        "420293de-31e0-4847-8778-5844d4bd6263-2.xml",
        "99c52282-6627-4a2b-94d2-bf204fabec13-01.xml",
    ])
    # CSV schreibt die Version mal "1", mal "01": beides muss die richtige Datei finden
    assert dateien[("420293de-31e0-4847-8778-5844d4bd6263", version_nr("01"))].endswith("-1.xml")
    assert dateien[("420293de-31e0-4847-8778-5844d4bd6263", version_nr("2"))].endswith("-2.xml")
    assert ("99c52282-6627-4a2b-94d2-bf204fabec13", 1) in dateien
