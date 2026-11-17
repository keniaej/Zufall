"""Anbindung an die TED Search API v3 (Tenders Electronic Daily, EU).

Die API ist anonym nutzbar (kein API-Key)::

    POST https://api.ted.europa.eu/v3/notices/search

Dokumentation: https://docs.ted.europa.eu/api/latest/search.html
"""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from branchen_codes import Ausschreibung, Vergabeplattform, land_name

log = logging.getLogger(__name__)

Json = dict[str, Any]
PFLICHTFELDER = [
    "publication-number", "publication-date", "notice-title", "buyer-name",
    "buyer-country", "classification-cpv", "deadline-receipt-tender-date-lot",
]
ZUSATZFELDER = ["buyer-city", "procedure-type"]  # werden bei HTTP 400 weggelassen
SPRACHEN = ("DEU", "ENG")  # Reihenfolge für mehrsprachige Felder


class Ted(Vergabeplattform):
    """Ruft Ausschreibungen (Wettbewerbsbekanntmachungen) von TED ab."""

    name = "ted.europa.eu"
    URL = "https://api.ted.europa.eu/v3/notices/search"
    DETAIL_URL = "https://ted.europa.eu/de/notice/-/detail/{}"
    SEITENGROESSE = 250

    def __init__(self, cpv_praefixe: list[str], timeout: int = 60) -> None:
        self.cpv_praefixe = cpv_praefixe
        self.timeout = timeout

    def abrufen(self, von: date, bis: date) -> list[Ausschreibung]:
        """Alle Ausschreibungen im Zeitraum, die zu den CPV-Präfixen passen."""
        cpv = " OR ".join(f"classification-cpv={p}*" for p in self.cpv_praefixe)
        query = (
            f"publication-date>={von:%Y%m%d} AND publication-date<={bis:%Y%m%d} "
            f"AND form-type=competition AND ({cpv})"
        )
        felder = PFLICHTFELDER + ZUSATZFELDER
        try:
            notices = list(self._suche(query, felder))
        except HTTPError as fehler:
            if fehler.code != 400:
                raise
            log.warning("%s: Zusatzfelder nicht verfügbar, wiederhole ohne sie", self.name)
            notices = list(self._suche(query, PFLICHTFELDER))
        return [self._umwandeln(n) for n in notices]

    def _suche(self, query: str, felder: list[str]) -> Any:
        """Blättert per Iterations-Token durch alle Treffer."""
        body: Json = {
            "query": query, "fields": felder, "scope": "ALL",
            "limit": self.SEITENGROESSE, "paginationMode": "ITERATION",
        }
        while True:
            antwort = self._post(body)
            yield from antwort.get("notices", [])
            token = antwort.get("iterationNextToken")
            if not token or not antwort.get("notices"):
                return
            body["iterationNextToken"] = token

    def _post(self, body: Json) -> Json:
        anfrage = Request(
            self.URL, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "User-Agent": "ausschreibungs-import/1.0"},
        )
        with urlopen(anfrage, timeout=self.timeout) as antwort:
            return json.load(antwort)

    def _umwandeln(self, n: Json) -> Ausschreibung:
        nummer = n["publication-number"]
        laender = n.get("buyer-country") or [""]
        return Ausschreibung(
            plattform=self.name,
            plattform_id=nummer,
            titel=_mehrsprachig(n.get("notice-title")),
            cpv_codes=dict.fromkeys(n.get("classification-cpv") or [], ""),
            auftraggeber=_mehrsprachig(n.get("buyer-name")),
            stadt=_mehrsprachig(n.get("buyer-city")),
            land=land_name(laender[0]),
            vergabeart=_mehrsprachig(n.get("procedure-type")),
            publikation=_datum(n.get("publication-date")),
            angebotsfrist=_fruehestes(n.get("deadline-receipt-tender-date-lot")),
            link=self._link(n, nummer),
        )

    def _link(self, n: Json, nummer: str) -> str:
        """Bevorzugt die deutsche HTML-Ansicht der Bekanntmachung."""
        links: Json = n.get("links") or {}
        url = _mehrsprachig(links.get("htmlDirect") or links.get("html"))
        return url or self.DETAIL_URL.format(nummer)


def _mehrsprachig(wert: Any) -> str:
    """Wählt aus ``{'deu': [...], 'eng': ...}`` Deutsch, dann Englisch, dann irgendeine Sprache."""
    if not isinstance(wert, dict):
        return str(wert[0] if isinstance(wert, list) and wert else wert or "")
    sprachen = {k.upper(): v for k, v in wert.items()}
    reihenfolge = [*SPRACHEN, *sprachen]
    auswahl = next((sprachen[s] for s in reihenfolge if s in sprachen), "")
    return _mehrsprachig(auswahl) if isinstance(auswahl, list) else str(auswahl or "").strip()


def _fruehestes(daten: list[str] | None) -> date | None:
    """Früheste Frist aus den losbezogenen Fristen."""
    return min(filter(None, map(_datum, daten or [])), default=None)


def _datum(text: str | None) -> date | None:
    """Liest ``'2026-12-08+01:00'`` bzw. ``'2026-12-08T10:00:00+01:00'`` als Datum."""
    try:
        return date.fromisoformat(str(text)[:10])
    except ValueError:
        return None
