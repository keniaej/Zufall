"""Plattformunabhängige Branchen- und Filterlogik sowie gemeinsame Schnittstelle.

Dieses Modul ist die einzige Stelle, an der CPV-Codes, Produktkategorien und
geografische Filter ausgewertet werden. Es enthält außerdem das einheitliche
Datenformat (:class:`Ausschreibung`) und die Schnittstelle
(:class:`Vergabeplattform`), die jedes Plattformmodul implementiert.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date

KEINE_EINSCHRAENKUNG = {"", "-", "keine", "alle"}
_CPV_MUSTER = re.compile(r"(\d{8})(?:\s*-\s*(\d))?")
_ORTS_TRENNER = re.compile(r"[,;/\n]")

# ISO-Ländercodes (Alpha-2/Alpha-3) -> deutsche Bezeichnung; unbekannte Codes bleiben unverändert
_LAENDER = {
    "DE": "Deutschland", "AT": "Österreich", "CH": "Schweiz", "NL": "Niederlande",
    "BE": "Belgien", "LU": "Luxemburg", "FR": "Frankreich", "PL": "Polen",
    "CZ": "Tschechien", "DK": "Dänemark",
}
_LAENDER_ALPHA3 = {
    "DEU": "DE", "AUT": "AT", "CHE": "CH", "NLD": "NL", "BEL": "BE",
    "LUX": "LU", "FRA": "FR", "POL": "PL", "CZE": "CZ", "DNK": "DK",
}


def land_name(code: str) -> str:
    """Wandelt einen ISO-Ländercode in den deutschen Namen um (``'DEU'`` -> ``'Deutschland'``)."""
    code = str(code or "").strip()
    schluessel = _LAENDER_ALPHA3.get(code.upper(), code.upper())
    return _LAENDER.get(schluessel, "Deutschland" if schluessel == "GERMANY" else code)

# (CPV-Code mit Bezeichnung, Zufall-Produkt, örtliche Eingrenzung - "Keine" = bundesweit/weltweit)
_LAND_ORTE = "Göttingen, Fulda, Haiger, Grammetal, Eichenzell, Kassel"
KRITERIEN = [
    ("60600000-4 – Transport zu Wasser", "Seefracht", "Keine"),
    ("60640000-6 – Seefrachtverkehr", "Seefracht", "Keine"),
    ("60650000-3 – Binnenschifffahrt", "Seefracht", "Keine"),
    ("60400000-2 – Luftverkehrsdienste", "Luftfracht", "Keine"),
    ("60410000-5 – Linienflugverkehr", "Luftfracht", "Keine"),
    ("60420000-8 – Gelegenheitsflugverkehr", "Luftfracht", "Keine"),
    ("60440000-4 – Luftfracht- und Posttransportdienste", "Luftfracht", "Keine"),
    ("60100000-9 – Straßentransport/-beförderung", "Landverkehr", _LAND_ORTE),
    ("60180000-3 – Vermietung von Lastkraftwagen mit Fahrer", "Landverkehr", _LAND_ORTE),
    ("60160000-7 – Post- und Paketbeförderung auf der Straße", "NSE", "Deutschland"),
    ("60161000-4 – Paketbeförderung", "NSE", "Deutschland"),
    ("64120000-3 – Kurierdienste", "NSE", "Deutschland"),
    ("64121000-0 – Mehrfachzustelldienste", "NSE", "Deutschland"),
    ("64121200-2 – Paketzustellung", "NSE", "Deutschland"),
    ("63120000-6 – Lagerung und Lagerhaltung", "Kontraktlogistik", "Keine"),
    ("63121000-3 – Lagereinrichtungen", "Kontraktlogistik", "Keine"),
    ("63121100-4 – Lagerdienstleistungen", "Kontraktlogistik", "Keine"),
    ("63122000-0 – Lagerhaltung von Waren", "Kontraktlogistik", "Keine"),
]


# --------------------------------------------------------------------------- #
# Einheitliches Datenformat und Plattform-Schnittstelle
# --------------------------------------------------------------------------- #
@dataclass
class Ausschreibung:
    """Eine Bekanntmachung im plattformunabhängigen Format."""

    plattform: str
    plattform_id: str
    titel: str
    cpv_codes: dict[str, str] = field(default_factory=dict)  # Nummer -> Bezeichnung
    auftraggeber: str = ""
    email: str = ""
    stadt: str = ""
    strasse: str = ""
    plz: str = ""
    land: str = ""
    leistungsorte: list[str] = field(default_factory=list)
    vergabeart: str = ""
    publikation: date | None = None
    angebotsfrist: date | None = None
    vertragsdauer_monate: int | None = None
    link: str = ""
    # Wird vom KriterienKatalog gesetzt:
    branchen_code: str = ""
    produkt: str = ""

    def ortsangaben(self) -> list[str]:
        """Alle Texte, gegen die geografische Filter geprüft werden."""
        return [self.stadt, self.plz, self.land, self.titel, *self.leistungsorte]


class Vergabeplattform(ABC):
    """Schnittstelle für alle Plattformmodule.

    Ein Plattformmodul kümmert sich ausschließlich um die API-Kommunikation und
    die Umwandlung in :class:`Ausschreibung`. Filterung und Excel-Export
    erfolgen zentral.
    """

    name: str = ""

    @abstractmethod
    def abrufen(self, von: date, bis: date) -> list[Ausschreibung]:
        """Liefert alle im Zeitraum veröffentlichten Ausschreibungen."""


# --------------------------------------------------------------------------- #
# CPV-Codes und Kriterien
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CpvCode:
    """Normalisierter CPV-Code (8 Ziffern, Prüfziffer optional)."""

    nummer: str
    pruefziffer: str = ""
    bezeichnung: str = ""

    @classmethod
    def parse(cls, text: str) -> CpvCode:
        """Liest Freitext wie ``'60100000-9 – Straßentransport'``.

        Raises:
            ValueError: Wenn kein achtstelliger CPV-Code enthalten ist.
        """
        bereinigt = str(text).replace("\xa0", " ").strip()
        treffer = _CPV_MUSTER.search(bereinigt)
        if not treffer:
            raise ValueError(f"Ungültiger CPV-Code: {text!r}")
        bezeichnung = bereinigt[treffer.end():].strip(" –-:\t")
        return cls(treffer.group(1), treffer.group(2) or "", bezeichnung)

    @staticmethod
    def normalisieren(text: str) -> str | None:
        """Gibt die achtstellige Nummer zurück oder ``None`` bei ungültiger Eingabe."""
        treffer = _CPV_MUSTER.search(str(text or "").replace(" ", ""))
        return treffer.group(1) if treffer else None

    @property
    def praefix(self) -> str:
        """Signifikanter Teil für die hierarchische Suche (z. B. 60100000 -> '601')."""
        return self.nummer.rstrip("0").ljust(2, "0")

    def umfasst(self, nummer: str) -> bool:
        """Prüft, ob ``nummer`` gleich diesem Code oder ein Unterbegriff davon ist."""
        return nummer.startswith(self.praefix)


@dataclass(frozen=True)
class Kriterium:
    """Ein Branchencode mit Produktkategorie und optionalem Ortsfilter."""

    cpv: CpvCode
    produkt: str
    orte: tuple[str, ...] = ()  # leer = keine örtliche Eingrenzung

    def ort_passt(self, ausschreibung: Ausschreibung) -> bool:
        """Prüft den geografischen Filter gegen die Ortsangaben der Ausschreibung."""
        if not self.orte:
            return True
        text = " | ".join(filter(None, ausschreibung.ortsangaben())).casefold()
        return any(ort.casefold() in text for ort in self.orte)


class KriterienKatalog:
    """Ordnet Ausschreibungen anhand ihrer CPV-Codes einer Produktkategorie zu."""

    def __init__(self, kriterien: Iterable[Kriterium]) -> None:
        # Spezifischste Codes zuerst, damit z. B. 60161000 (NSE) vor 60100000 greift.
        self._kriterien = sorted(
            kriterien, key=lambda k: len(k.cpv.praefix), reverse=True
        )

    @classmethod
    def aus_zeilen(cls, zeilen: Iterable[tuple[str, str, str]]) -> KriterienKatalog:
        """Erzeugt den Katalog aus Zeilen (Branchencode, Produkt, Örtliche Eingrenzung)."""
        kriterien = [
            Kriterium(CpvCode.parse(code), str(produkt or "").strip(), cls._orte(ort))
            for code, produkt, ort in zeilen
            if code
        ]
        if not kriterien:
            raise ValueError("Es wurden keine Branchencodes gefunden.")
        return cls(kriterien)

    @staticmethod
    def _orte(text: str | None) -> tuple[str, ...]:
        teile = (teil.strip() for teil in _ORTS_TRENNER.split(str(text or "")))
        return tuple(t for t in teile if t.casefold() not in KEINE_EINSCHRAENKUNG)

    @property
    def cpv_praefixe(self) -> list[str]:
        """Kürzeste CPV-Präfixe (z. B. ``601``, ohne das davon abgedeckte ``6016``)."""
        ergebnis: list[str] = []
        for praefix in sorted({k.cpv.praefix for k in self._kriterien}):
            if not any(praefix.startswith(vorhandenes) for vorhandenes in ergebnis):
                ergebnis.append(praefix)
        return ergebnis

    def zuordnen(self, ausschreibung: Ausschreibung) -> Kriterium | None:
        """Sucht das spezifischste passende Kriterium und trägt es in die Ausschreibung ein."""
        for kriterium in self._kriterien:
            for nummer, bezeichnung in ausschreibung.cpv_codes.items():
                if kriterium.cpv.umfasst(nummer) and kriterium.ort_passt(ausschreibung):
                    ausschreibung.branchen_code = f"{nummer} {bezeichnung}".strip()
                    ausschreibung.produkt = kriterium.produkt
                    return kriterium
        return None

    def filtern(self, ausschreibungen: Iterable[Ausschreibung]) -> list[Ausschreibung]:
        """Gibt nur die Ausschreibungen zurück, die einem Kriterium entsprechen."""
        return [a for a in ausschreibungen if self.zuordnen(a)]
