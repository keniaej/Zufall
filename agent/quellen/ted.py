"""Quelle: TED (Tenders Electronic Daily, EU-Ausschreibungsportal)

Braucht keinen API-Key. Die Search API filtert schon auf dem Server (CPV, Land, Datum, Art).
"""
import pandas as pd
import requests

from agent.modell import SPALTEN
from agent.quellen.basis import Quelle
from agent.werte import datum, erster, fristart_waehlen, land, laufzeit, vergabeart


def sprachtext(feld):
    """TED liefert Texte pro Sprache, z. B. {"deu": [...], "eng": [...]}. Nicht jede Bekanntmachung
    hat eine deutsche Fassung (z. B. auf Englisch veröffentlicht, GIZ). Reihenfolge: Deutsch,
    Englisch, sonst die erste vorhandene Sprache."""
    if not isinstance(feld, dict) or not feld:
        return erster(feld) if feld else None
    for sprache in ("deu", "eng"):
        if feld.get(sprache):
            return erster(feld[sprache])
    return erster(next(iter(feld.values())))


class TedQuelle(Quelle):
    name = "TED"

    URL = "https://api.ted.europa.eu/v3/notices/search"

    FELDER = [
        "publication-number", "procedure-identifier", "publication-date", "notice-type",
        "notice-title", "main-classification-proc", "classification-cpv",
        "organisation-name-buyer", "organisation-city-buyer", "organisation-email-buyer",
        "organisation-street-buyer", "organisation-post-code-buyer", "organisation-country-buyer",
        "procedure-type", "duration-period-value-lot", "duration-period-unit-lot",
        "contract-duration-start-date-lot", "contract-duration-end-date-lot",
        "deadline-receipt-tender-date-lot", "deadline-receipt-request-date-lot",
        "place-of-performance",   # Leistungsort
    ]

    def anfrage_bauen(self):
        """Suchausdruck in TEDs "Expert Search"-Syntax. Die CPV-Prüfung des Agenten läuft
        trotzdem, damit alle Quellen gleich behandelt werden."""
        e, k = self.einstellungen, self.kriterien
        teile = [
            f"classification-cpv IN ({' '.join(k.cpv_codes)})",
            f"buyer-country IN ({' '.join(e.laender)})",
            f"publication-date>={e.seit_datum}",
            f"notice-type IN ({' '.join(e.notice_typen)})",
        ]
        if k.ausschluss_codes:   # leere Liste in ausschluss_codes.csv -> kein Ausschluss
            teile.append(f"NOT main-classification-proc IN ({' '.join(k.ausschluss_codes)})")
        return {
            "query": " AND ".join(teile),
            "fields": self.FELDER,
            "limit": 250,
            "scope": "ACTIVE",
            "paginationMode": "ITERATION",   # Blätter-Modus
        }

    def abrufen(self):
        """Alle passenden Bekanntmachungen als Liste (Seite für Seite)."""
        anfrage = self.anfrage_bauen()
        alle_notices = []
        while True:
            antwort = requests.post(self.URL, json=anfrage, timeout=60)
            antwort.raise_for_status()   # bei Fehler abbrechen, der Agent fängt das ab
            daten = antwort.json()
            alle_notices.extend(daten["notices"])

            # TED schickt auch nach der letzten Seite noch ein Lesezeichen
            # und fängt dann von vorne an. Deshalb auch bei leerer Seite abbrechen.
            token = daten.get("iterationNextToken")
            if not token or len(daten["notices"]) == 0:
                break
            anfrage["iterationNextToken"] = token
        return alle_notices

    def umwandeln(self, roh):
        return pd.DataFrame([self.zeile(n) for n in roh], columns=SPALTEN)

    def zeile(self, notice):
        """Eine TED-Bekanntmachung -> eine Zeile im gemeinsamen Format."""
        frist, fristart = fristart_waehlen(erster(notice.get("deadline-receipt-tender-date-lot")),
                                           erster(notice.get("deadline-receipt-request-date-lot")))
        monate, beginn, ende = laufzeit(
            notice.get("duration-period-value-lot") or [], notice.get("duration-period-unit-lot") or [],
            notice.get("contract-duration-start-date-lot") or [], notice.get("contract-duration-end-date-lot") or [])
        # TED führt CPV-Codes pro Los auf, daher doppelte entfernen
        alle_cpv = sorted(set(notice.get("classification-cpv") or []))

        return {
            "Ausschreibungs ID Platform": notice.get("publication-number"),
            "Verfahrens ID": notice.get("procedure-identifier"),
            "Publikation": datum(notice.get("publication-date")),
            "Art": notice.get("notice-type"),
            "Titel": sprachtext(notice.get("notice-title")),
            "Vergabe Branchen Code": erster(notice.get("main-classification-proc")),
            "Alle CPV": ", ".join(alle_cpv),
            "Auftraggeber": sprachtext(notice.get("organisation-name-buyer")),
            "Email": erster(notice.get("organisation-email-buyer")),
            "Stadt": erster(notice.get("organisation-city-buyer")),
            "Straße": erster(notice.get("organisation-street-buyer")),
            "PLZ": erster(notice.get("organisation-post-code-buyer")),
            "Land": land(erster(notice.get("organisation-country-buyer"))),
            "Vergabeart": vergabeart(erster(notice.get("procedure-type"))),
            "Vertragsdauer in Monaten": monate,
            "Vertragsbeginn": beginn,
            "Vertragsende": ende,
            "Leistungsort NUTS": ", ".join(sorted(set(notice.get("place-of-performance") or []))),
            "Angebotsfrist": datum(frist),
            "Fristart": fristart,
            "Plattform": self.name,
            "Link zur Plattform": notice["links"]["html"]["DEU"],
        }
