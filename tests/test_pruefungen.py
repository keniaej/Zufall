"""Tests für die Prüfungen (agent/pruefungen/) ohne Internet."""
import pandas as pd
import pytest

from agent.kriterien import Kriterien
from agent.pruefungen import (CpvPruefung, DublettenErkennung, FristPruefung, Pruefung, RegionPruefung,
                              SchlagwortPruefung, standard_pruefungen)


def test_ausschluss_code_sortiert_aus(kriterien):
    tabelle = pd.DataFrame({
        "Alle CPV": ["60112000, 60100000", "60100000"],
        "Vergabe Branchen Code": ["60112000", "60100000"],
    })
    behalten, raus = CpvPruefung(kriterien).pruefen(tabelle)
    assert list(raus["Ausschlussgrund"]) == ["Personenverkehr (Hauptcode)"]
    assert list(behalten["Zufall Produkt"]) == ["Landverkehr"]


def test_schlagwort_sortiert_aus(kriterien):
    tabelle = pd.DataFrame({"Titel": ["Schülerbeförderung Kassel", "Lagerlogistik"]})
    behalten, raus = SchlagwortPruefung(kriterien).pruefen(tabelle)
    assert list(behalten["Titel"]) == ["Lagerlogistik"]
    assert len(raus) == 1


def test_region_nur_fuer_regionale_produkte():
    k = Kriterien(region_produkte=["Landverkehr"], region_kreise={"DE732": "Fulda (Fulda)"})
    tabelle = pd.DataFrame({
        "Zufall Produkt": ["Landverkehr", "Landverkehr", "Kontraktlogistik", "Landverkehr, Kontraktlogistik", "Landverkehr"],
        "Leistungsort NUTS": ["DE732", "DE212", "DE212", "DE212", ""],
    })
    behalten, raus = RegionPruefung(k).pruefen(tabelle)
    assert list(raus.index) == [1]                       # nur Landverkehr in München fliegt raus
    assert behalten.loc[0, "Region Landverkehr"] == "ja: Fulda (Fulda)"
    assert behalten.loc[4, "Region Landverkehr"] == "unklar (kein Landkreis angegeben)"


def test_frist_mit_festem_datum():
    heute = pd.Timestamp("2026-11-17")
    tabelle = pd.DataFrame({"Angebotsfrist": [pd.Timestamp("2026-11-16"), pd.Timestamp("2026-11-17"), pd.NaT]})
    behalten, raus = FristPruefung(Kriterien(), heute=heute).pruefen(tabelle)
    assert list(raus.index) == [0]
    assert len(behalten) == 2                            # heute und "keine Frist" bleiben


def test_dubletten_neueste_fassung_gewinnt():
    tabelle = pd.DataFrame({
        "Verfahrens ID": ["v1", "v1", None],
        "Ausschreibungs ID Platform": ["alt", "neu", "ohne-id"],
        "Plattform": ["TED", "oeffentlichevergabe.de", "TED"],
        "Publikation": pd.to_datetime(["2026-10-01", "2026-10-05", "2026-10-02"]),
    })
    behalten = DublettenErkennung().entfernen(tabelle).set_index("Verfahrens ID")
    assert behalten.loc["v1", "Ausschreibungs ID Platform"] == "neu"
    assert behalten.loc["v1", "Gefunden auf"] == "TED, oeffentlichevergabe.de"
    assert "ohne-id" in behalten.index                   # ohne Verfahrens-ID: eigene Zeile


def test_reihenfolge_der_pruefungen(kriterien):
    namen = [type(p).__name__ for p in standard_pruefungen(kriterien)]
    assert namen[0] == "CpvPruefung"                     # ermittelt das Produkt, das Region braucht
    assert namen.index("CpvPruefung") < namen.index("RegionPruefung")


def test_neue_pruefung_braucht_gruende():
    class Unfertig(Pruefung):
        pass
    with pytest.raises(TypeError):
        Unfertig(Kriterien())

    class NurKurze(Pruefung):
        name = "Lange Titel"
        def gruende(self, tabelle):
            return tabelle, ["zu lang" if len(t) > 5 else None for t in tabelle["Titel"]]
    behalten, raus = NurKurze(Kriterien()).pruefen(pd.DataFrame({"Titel": ["kurz", "sehr lang"]}))
    assert list(behalten["Titel"]) == ["kurz"] and list(raus["Ausschlussgrund"]) == ["zu lang"]
