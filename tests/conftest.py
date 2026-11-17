"""Gemeinsame Bausteine für die Tests (pytest lädt diese Datei automatisch).

Alle Tests laufen ohne Internet: Statt echter Quellen gibt es FesteQuelle, die vorgegebene
Zeilen liefert. So lässt sich der ganze Agent inklusive Excel prüfen.
"""
import pandas as pd
import pytest

from agent.einstellungen import Einstellungen
from agent.kriterien import Kriterien
from agent.modell import SPALTEN
from agent.quellen.basis import Quelle


@pytest.fixture
def einstellungen(tmp_path):
    """Einstellungen wie im echten Lauf, aber die Excel-Datei landet in einem Testordner."""
    return Einstellungen(ausgabe_ordner=tmp_path)


@pytest.fixture
def kriterien():
    """Die echten Kriterien aus kriterien/."""
    return Kriterien.laden(Einstellungen().kriterien_ordner)


class FesteQuelle(Quelle):
    """Quelle für Tests: liefert die Zeilen, die man ihr gibt, statt etwas abzurufen."""

    def __init__(self, name, zeilen, kriterien=None, einstellungen=None):
        super().__init__(kriterien, einstellungen)
        self.name = name
        self.zeilen = zeilen

    def abrufen(self):
        return self.zeilen

    def umwandeln(self, roh):
        return pd.DataFrame(roh, columns=SPALTEN)


def zeile(**werte):
    """Eine Bekanntmachung im gemeinsamen Format; nicht genannte Spalten sind leer."""
    basis = {s: None for s in SPALTEN}
    basis.update(werte)
    return basis
