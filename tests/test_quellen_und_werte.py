"""Tests für Quellen (ohne Internet) und die Hilfsfunktionen in agent/werte.py."""
import pandas as pd
import pytest

from agent.quellen import QUELLEN_KLASSEN, Quelle
from agent.quellen.oeffentlichevergabe import version_nr, xml_dateien_je_bekanntmachung
from agent.quellen.ted import TedQuelle, sprachtext
from agent.werte import fristart_waehlen, laufzeit, text_bereinigen
from conftest import FesteQuelle, zeile


def test_neue_quelle_muss_abrufen_und_umwandeln_haben():
    class Unfertig(Quelle):
        name = "Unfertig"
        def abrufen(self):
            return []
    with pytest.raises(TypeError):
        Unfertig(None, None)


def test_quelle_meldet_fehlende_spalten():
    class Kaputt(FesteQuelle):
        def umwandeln(self, roh):
            return pd.DataFrame({"Titel": ["x"]})
    with pytest.raises(ValueError, match="Kaputt.*liefert diese Spalten nicht"):
        Kaputt("Kaputt", []).holen()


def test_quelle_bereinigt_texte():
    tabelle = FesteQuelle("Test", [zeile(Titel="Post\r\ndienst  X ", Auftraggeber="   ")]).holen()
    assert tabelle.loc[0, "Titel"] == "Post dienst X"
    assert tabelle.loc[0, "Auftraggeber"] is None


def test_alle_quellen_haben_eindeutige_namen():
    namen = [k.name for k in QUELLEN_KLASSEN]
    assert len(set(namen)) == len(namen)


def test_ted_anfrage(kriterien, einstellungen):
    anfrage = TedQuelle(kriterien, einstellungen).anfrage_bauen()
    assert "60100000" in anfrage["query"]
    assert f"publication-date>={einstellungen.seit_datum}" in anfrage["query"]
    assert "NOT main-classification-proc IN (60112000" in anfrage["query"]


def test_sprachtext_ted():
    assert sprachtext({"deu": ["Polizei Köln"], "eng": ["Police Cologne"]}) == "Polizei Köln"
    assert sprachtext({"eng": ["Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ) GmbH"]}) \
        == "Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ) GmbH"
    assert sprachtext({"dan": ["Ørsted A/S"]}) == "Ørsted A/S"
    assert sprachtext(None) is None


def test_xml_dateien_zuordnen():
    dateien = xml_dateien_je_bekanntmachung([
        "420293de-31e0-4847-8778-5844d4bd6263-1.xml",
        "420293de-31e0-4847-8778-5844d4bd6263-2.xml",
        "99c52282-6627-4a2b-94d2-bf204fabec13-01.xml",
    ])
    # CSV schreibt die Version mal "1", mal "01": beides muss die richtige Datei finden
    assert dateien[("420293de-31e0-4847-8778-5844d4bd6263", version_nr("01"))].endswith("-1.xml")
    assert dateien[("420293de-31e0-4847-8778-5844d4bd6263", version_nr("2"))].endswith("-2.xml")
    assert ("99c52282-6627-4a2b-94d2-bf204fabec13", 1) in dateien


def test_laufzeit():
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


def test_text_bereinigen():
    assert text_bereinigen("Postdienst\r\nfür  Stadt\tX ") == "Postdienst für Stadt X"
    assert text_bereinigen("   ") is None
    assert text_bereinigen(None) is None


def test_fristart():
    assert fristart_waehlen("2026-12-01", "2026-11-20") == ("2026-12-01", "Angebot")
    assert fristart_waehlen(None, "2026-11-20") == ("2026-11-20", "Teilnahmeantrag")
    assert fristart_waehlen(None, None) == (None, "keine Angabe")
