"""Tests für das Einlesen der Kriterien-Dateien in kriterien/."""
import pytest

from agent import konfiguration as k


def test_kriterien_stimmig():
    # Prüft nur, ob die Dateien zusammenpassen, nicht die genaue Anzahl.
    # So können die Listen in kriterien/ geändert werden, ohne dass Tests angepasst werden müssen.
    assert k.CPV_CODES
    assert len(set(k.CPV_CODES)) == len(k.CPV_CODES)
    if k.REGION_PRODUKTE:
        assert k.REGION_KREISE, "Es gibt regional begrenzte Produkte, aber keine Landkreise"
    # Ein gesuchter Code darf nicht gleichzeitig ausgeschlossen sein
    assert not set(k.CPV_CODES) & set(k.AUSSCHLUSS_CODES)


def test_cpv_normalisieren():
    assert k.cpv_normalisieren("60100000-9", "x.csv", 2) == "60100000"
    assert k.cpv_normalisieren("3000000", "x.csv", 2) == "03000000"   # Excel hat die 0 verschluckt
    assert k.cpv_normalisieren("60100000.0", "x.csv", 2) == "60100000"
    with pytest.raises(k.KriterienFehler):
        k.cpv_normalisieren("Lagerung", "x.csv", 2)


def test_excel_csv_varianten(tmp_path, monkeypatch):
    # Deutsches Excel speichert "CSV (Trennzeichen-getrennt)" im Windows-Zeichensatz,
    # englisches Excel mit Komma. Beides muss gehen.
    monkeypatch.setattr(k, "KRITERIEN_ORDNER", tmp_path)
    (tmp_path / "a.csv").write_bytes("Wort;Hinweis\nschülerverkehr;\n\n".encode("cp1252"))
    (tmp_path / "b.csv").write_text("Wort,Hinweis\npax,\n", encoding="utf-8")
    assert k.woerter_laden("a.csv", "Wort") == ["schülerverkehr"]
    assert k.woerter_laden("b.csv", "Wort") == ["pax"]


def test_unbekanntes_produkt_gibt_klare_meldung(tmp_path, monkeypatch):
    monkeypatch.setattr(k, "KRITERIEN_ORDNER", tmp_path)
    (tmp_path / "cpv_codes.csv").write_text(
        "Code;Bezeichnung;Zufall Produkt;Aktiv\n60100000;Straße;Landverkehrr;ja\n", encoding="utf-8")
    with pytest.raises(k.KriterienFehler, match="Zeile 2.*Landverkehrr"):
        k.cpv_codes_laden({"Landverkehr": True})


def test_inaktive_codes_werden_ignoriert(tmp_path, monkeypatch):
    monkeypatch.setattr(k, "KRITERIEN_ORDNER", tmp_path)
    (tmp_path / "cpv_codes.csv").write_text(
        "Code;Bezeichnung;Zufall Produkt;Aktiv\n60100000;Straße;Landverkehr;ja\n60200000;Schiene;Landverkehr;nein\n",
        encoding="utf-8")
    produkte, _ = k.cpv_codes_laden({"Landverkehr": True})
    assert produkte == {"Landverkehr": ["60100000"]}
