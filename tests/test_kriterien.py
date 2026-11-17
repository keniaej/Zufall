"""Tests für das Einlesen der Kriterien-Dateien (agent/kriterien.py)."""
import pytest

from agent.kriterien import Kriterien, KriterienFehler, _CsvLeser, cpv_normalisieren, cpv_passt


def test_kriterien_stimmig(kriterien):
    # Prüft nur, ob die Dateien zusammenpassen, nicht die genaue Anzahl.
    # So können die Listen in kriterien/ geändert werden, ohne dass Tests angepasst werden müssen.
    assert kriterien.cpv_codes
    assert len(set(kriterien.cpv_codes)) == len(kriterien.cpv_codes)
    if kriterien.region_produkte:
        assert kriterien.region_kreise, "Es gibt regional begrenzte Produkte, aber keine Landkreise"
    # Ein gesuchter Code darf nicht gleichzeitig ausgeschlossen sein
    assert not set(kriterien.cpv_codes) & set(kriterien.ausschluss_codes)


def test_cpv_baum():
    assert cpv_passt("60161000", "60100000")
    assert not cpv_passt("60600000", "60100000")
    # 60000000 umfasst alles mit 60, aber nicht 66000000 (Finanzdienste)
    assert cpv_passt("60112000", "60000000")
    assert not cpv_passt("66000000", "60000000")
    assert not cpv_passt("63120000", "60000000")


def test_genauester_code_gewinnt(kriterien):
    # 60161000 ist NSE, obwohl es im CPV-Baum unter Landverkehr (60100000) liegt
    assert kriterien.produkte_ermitteln(["60161000"]) == ["NSE"]
    assert kriterien.produkte_ermitteln(["60100000"]) == ["Landverkehr"]
    # 60183000 Lieferwagen ist NSE, 60181000 Lkw ist Landverkehr (beide unter 60180000)
    assert kriterien.produkte_ermitteln(["60183000"]) == ["NSE"]
    assert kriterien.produkte_ermitteln(["60181000"]) == ["Landverkehr"]
    # Oberbegriff nur, wenn kein genauerer Code passt
    assert kriterien.produkte_ermitteln(["60300000"]) == ["Transport allgemein"]
    assert kriterien.produkte_ermitteln(["66000000"]) == []


def test_kriterien_direkt_erzeugen():
    # Für Tests und Experimente ohne CSV-Dateien
    k = Kriterien(produkte={"Lager": ["63120000"]}, ausschluss_codes={"63121000": "Test"})
    assert k.cpv_codes == ["63120000"]
    assert k.produkte_ermitteln(["63122000"]) == ["Lager"]
    assert k.ausschlussgrund("63121100") == "Test"
    assert k.ausschlussgrund("63122000") is None


def test_cpv_normalisieren():
    assert cpv_normalisieren("60100000-9", "x.csv", 2) == "60100000"
    assert cpv_normalisieren("3000000", "x.csv", 2) == "03000000"   # Excel hat die 0 verschluckt
    assert cpv_normalisieren("60100000.0", "x.csv", 2) == "60100000"
    with pytest.raises(KriterienFehler):
        cpv_normalisieren("Lagerung", "x.csv", 2)


def test_excel_csv_varianten(tmp_path):
    # Deutsches Excel speichert "CSV (Trennzeichen-getrennt)" im Windows-Zeichensatz,
    # englisches Excel mit Komma. Beides muss gehen.
    (tmp_path / "a.csv").write_bytes("Wort;Hinweis\nschülerverkehr;\n\n".encode("cp1252"))
    (tmp_path / "b.csv").write_text("Wort,Hinweis\npax,\n", encoding="utf-8")
    leser = _CsvLeser(tmp_path)
    assert leser.woerter("a.csv", "Wort") == ["schülerverkehr"]
    assert leser.woerter("b.csv", "Wort") == ["pax"]


def test_unbekanntes_produkt_gibt_klare_meldung(tmp_path):
    (tmp_path / "cpv_codes.csv").write_text(
        "Code;Bezeichnung;Zufall Produkt;Aktiv\n60100000;Straße;Landverkehrr;ja\n", encoding="utf-8")
    with pytest.raises(KriterienFehler, match="Zeile 2.*Landverkehrr"):
        _CsvLeser(tmp_path).cpv_codes({"Landverkehr": True})


def test_inaktive_codes_werden_ignoriert(tmp_path):
    (tmp_path / "cpv_codes.csv").write_text(
        "Code;Bezeichnung;Zufall Produkt;Aktiv\n60100000;Straße;Landverkehr;ja\n60200000;Schiene;Landverkehr;nein\n",
        encoding="utf-8")
    produkte, _ = _CsvLeser(tmp_path).cpv_codes({"Landverkehr": True})
    assert produkte == {"Landverkehr": ["60100000"]}


def test_fehlende_datei_gibt_klare_meldung(tmp_path):
    with pytest.raises(KriterienFehler, match="Datei fehlt: kriterien/produkte.csv"):
        Kriterien.laden(tmp_path)
