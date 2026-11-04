"""Tests ohne Internet: prüfen, ob die Regeln richtig rechnen.
Starten mit:  python -m pytest
"""
import pandas as pd

from agent.format import cpv_passt
from agent.pruefungen import produkte_ermitteln, schlagwoerter_pruefen


def test_cpv_baum():
    assert cpv_passt("60161000", "60100000")
    assert not cpv_passt("60600000", "60100000")


def test_genauester_code_gewinnt():
    # 60160000 ist NSE, obwohl es im CPV-Baum unter Landverkehr (60100000) liegt
    assert produkte_ermitteln(["60160000"]) == ["NSE"]
    assert produkte_ermitteln(["60100000"]) == ["Landverkehr"]


def test_schlagwort_sortiert_aus():
    tabelle = pd.DataFrame({"Titel": ["Schülerbeförderung Kassel", "Lagerlogistik"]})
    behalten, raus = schlagwoerter_pruefen(tabelle)
    assert list(behalten["Titel"]) == ["Lagerlogistik"]
    assert len(raus) == 1
