"""Anbindung an die Open-Data-Schnittstelle von oeffentlichevergabe.de.

Der Bekanntmachungsservice des Bundes stellt pro Kalendertag ein ZIP-Archiv mit
allen Bekanntmachungen im OCDS-Format bereit::

    GET https://oeffentlichevergabe.de/api/notice-exports?pubDay=YYYY-MM-DD&format=ocds.zip

Dokumentation:
https://oeffentlichevergabe.de/documentation/swagger-ui/opendata/index.html
"""

from __future__ import annotations

import io
import json
import logging
import zipfile
from collections.abc import Iterator
from datetime import date, datetime, timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from branchen_codes import Ausschreibung, CpvCode, Vergabeplattform, land_name

log = logging.getLogger(__name__)

Json = dict[str, Any]


class OeffentlicheVergabe(Vergabeplattform):
    """Ruft Bekanntmachungen von oeffentlichevergabe.de ab und vereinheitlicht sie."""

    name = "oeffentlichevergabe.de"
    EXPORT_URL = "https://oeffentlichevergabe.de/api/notice-exports"
    DETAIL_URL = "https://oeffentlichevergabe.de/ui/de/search/details?noticeId={}"
    OCID_PRAEFIX = "ocds-mnwr74-"
    VERGABEARTEN = {
        "open": "öffentlich",
        "selective": "beschränkt",
        "limited": "Verhandlungsverfahren",
        "direct": "Direktvergabe",
    }

    def __init__(self, timeout: int = 120) -> None:
        self.timeout = timeout

    # ------------------------------------------------------------------ #
    # Öffentliche Schnittstelle
    # ------------------------------------------------------------------ #
    def abrufen(self, von: date, bis: date) -> list[Ausschreibung]:
        """Lädt alle Tagesexporte im Zeitraum; je Verfahren gilt die neueste Bekanntmachung."""
        neueste: dict[str, Json] = {}
        tag = von
        while tag <= bis:
            try:
                for release in self._tagesexport(tag):
                    ocid = release.get("ocid") or release.get("id", "")
                    if self._ist_ausschreibung(release) and (
                        ocid not in neueste
                        or release.get("date", "") >= neueste[ocid].get("date", "")
                    ):
                        neueste[ocid] = release
            except (URLError, zipfile.BadZipFile, ValueError) as fehler:
                log.warning("%s: Export vom %s übersprungen (%s)", self.name, tag, fehler)
            tag += timedelta(days=1)
        return [self._umwandeln(release) for release in neueste.values()]

    # ------------------------------------------------------------------ #
    # API-Kommunikation
    # ------------------------------------------------------------------ #
    def _herunterladen(self, tag: date) -> bytes:
        """Lädt das ZIP eines Tages; leere Bytes, wenn es keine Daten gibt."""
        parameter = urlencode({"pubDay": tag.isoformat(), "format": "ocds.zip"})
        anfrage = Request(
            f"{self.EXPORT_URL}?{parameter}",
            headers={"Accept": "application/zip", "User-Agent": "ausschreibungs-import/1.0"},
        )
        try:
            with urlopen(anfrage, timeout=self.timeout) as antwort:
                return antwort.read()
        except HTTPError as fehler:
            if fehler.code in (204, 404):
                return b""
            raise

    def _tagesexport(self, tag: date) -> Iterator[Json]:
        inhalt = self._herunterladen(tag)
        if not inhalt:
            log.info("%s: keine Bekanntmachungen am %s", self.name, tag)
            return
        with zipfile.ZipFile(io.BytesIO(inhalt)) as archiv:
            for dateiname in archiv.namelist():
                if dateiname.lower().endswith(".json"):
                    yield from self._releases(json.loads(archiv.read(dateiname)))

    @classmethod
    def _releases(cls, daten: Any) -> Iterator[Json]:
        """Entpackt Release-Packages, Record-Packages, Listen und Einzel-Releases."""
        if isinstance(daten, list):
            for eintrag in daten:
                yield from cls._releases(eintrag)
        elif isinstance(daten, dict):
            if "releases" in daten:
                yield from cls._releases(daten["releases"])
            elif "records" in daten:
                for record in daten["records"]:
                    yield from cls._releases(record.get("compiledRelease", {}))
            elif "ocid" in daten:
                yield daten

    # ------------------------------------------------------------------ #
    # Umwandlung OCDS -> Ausschreibung
    # ------------------------------------------------------------------ #
    @staticmethod
    def _ist_ausschreibung(release: Json) -> bool:
        """Verwirft reine Zuschlags- und Vertragsbekanntmachungen."""
        tags = release.get("tag") or []
        return not tags or any(t.startswith(("tender", "planning")) for t in tags)

    def _umwandeln(self, release: Json) -> Ausschreibung:
        tender: Json = release.get("tender") or {}
        kaeufer = self._auftraggeber(release)
        adresse: Json = kaeufer.get("address") or {}
        return Ausschreibung(
            plattform=self.name,
            plattform_id=str(release.get("ocid", "")).removeprefix(self.OCID_PRAEFIX),
            titel=(tender.get("title") or tender.get("description") or "").strip(),
            cpv_codes=self._cpv_codes(tender),
            auftraggeber=kaeufer.get("name") or (release.get("buyer") or {}).get("name", ""),
            email=(kaeufer.get("contactPoint") or {}).get("email", ""),
            stadt=adresse.get("locality", ""),
            strasse=adresse.get("streetAddress", ""),
            plz=str(adresse.get("postalCode", "")),
            land=land_name(adresse.get("countryName") or adresse.get("country", "")),
            leistungsorte=self._leistungsorte(tender),
            vergabeart=self.VERGABEARTEN.get(tender.get("procurementMethod", ""))
            or tender.get("procurementMethodDetails", ""),
            publikation=_datum(tender.get("datePublished") or release.get("date")),
            angebotsfrist=_datum((tender.get("tenderPeriod") or {}).get("endDate")),
            vertragsdauer_monate=self._vertragsdauer(tender),
            link=self._link(release, tender),
        )

    @staticmethod
    def _auftraggeber(release: Json) -> Json:
        parteien: list[Json] = release.get("parties") or []
        kaeufer_id = (release.get("buyer") or {}).get("id")
        for partei in parteien:
            if partei.get("id") == kaeufer_id or "buyer" in (partei.get("roles") or []):
                return partei
        return {}

    @staticmethod
    def _cpv_codes(tender: Json) -> dict[str, str]:
        klassifikationen: list[Json] = [tender.get("classification") or {}]
        for position in tender.get("items") or []:
            klassifikationen.append(position.get("classification") or {})
            klassifikationen.extend(position.get("additionalClassifications") or [])
        codes: dict[str, str] = {}
        for k in klassifikationen:
            nummer = CpvCode.normalisieren(k.get("id", ""))
            if nummer and str(k.get("scheme", "CPV")).upper() == "CPV":
                codes.setdefault(nummer, k.get("description", ""))
        return codes

    def _leistungsorte(self, tender: Json) -> list[str]:
        orte: list[str] = []
        for position in tender.get("items") or []:
            adressen = position.get("deliveryAddresses") or [position.get("deliveryAddress") or {}]
            for a in adressen:
                orte += [a.get("locality", ""), a.get("postalCode", ""), a.get("region", "")]
                orte.append(land_name(a.get("countryName") or a.get("country", "")))
            orte.append((position.get("deliveryLocation") or {}).get("description", ""))
        return [str(ort) for ort in orte if ort]

    @staticmethod
    def _vertragsdauer(tender: Json) -> int | None:
        """Längste Vertragslaufzeit (Gesamtverfahren oder Lose) in Monaten."""
        zeitraeume = [tender.get("contractPeriod") or {}]
        zeitraeume += [los.get("contractPeriod") or {} for los in tender.get("lots") or []]
        monate: list[int] = []
        for z in zeitraeume:
            if z.get("durationInDays"):
                monate.append(round(int(z["durationInDays"]) / 30.4375))
            elif (start := _datum(z.get("startDate"))) and (ende := _datum(z.get("endDate"))):
                monate.append(round((ende - start).days / 30.4375))
        return max(monate) if monate else None

    def _link(self, release: Json, tender: Json) -> str:
        """Bevorzugt den Link zur Vergabeunterlage, sonst die Detailseite des Portals."""
        for dokument in tender.get("documents") or []:
            if str(dokument.get("url", "")).startswith("http"):
                return dokument["url"]
        return self.DETAIL_URL.format(release.get("id", ""))


def _datum(text: str | None) -> date | None:
    """Wandelt einen ISO-Zeitstempel in ein Datum um."""
    if not text:
        return None
    try:
        return datetime.fromisoformat(str(text).replace("Z", "+00:00")).date()
    except ValueError:
        return None
