"""Quelle: TED (Tenders Electronic Daily, EU-Ausschreibungsportal)

Braucht keinen API-Key.
"""
import pandas as pd
import requests

from agent.format import SPALTEN, datum, erster, land, laufzeit, vergabeart
from agent.konfiguration import CPV_CODES, LAENDER, NOTICE_TYPEN, AUSSCHLUSS_CODES, SEIT_DATUM

TED_URL = "https://api.ted.europa.eu/v3/notices/search"

TED_FELDER = [
    "publication-number", "procedure-identifier", "publication-date", "notice-type",
    "notice-title", "main-classification-proc", "classification-cpv",
    "organisation-name-buyer", "organisation-city-buyer", "organisation-email-buyer",
    "organisation-street-buyer", "organisation-post-code-buyer", "organisation-country-buyer",
    "procedure-type", "duration-period-value-lot", "duration-period-unit-lot",
    "contract-duration-start-date-lot", "contract-duration-end-date-lot",
    "deadline-receipt-tender-date-lot", "deadline-receipt-request-date-lot",
    "place-of-performance",   # Leistungsort
]


def ted_anfrage_bauen():
    """TED kann schon serverseitig filtern. Das spart Datenmenge.
    Die CPV-Prüfung in pruefungen.py läuft trotzdem, damit alle Quellen gleich behandelt werden."""
    teile = [
        f"classification-cpv IN ({' '.join(CPV_CODES)})",
        f"buyer-country IN ({' '.join(LAENDER)})",
        f"publication-date>={SEIT_DATUM}",
        f"notice-type IN ({' '.join(NOTICE_TYPEN)})",
    ]
    if AUSSCHLUSS_CODES:   # leere Liste in ausschluss_codes.csv -> kein Ausschluss
        teile.append(f"NOT main-classification-proc IN ({' '.join(AUSSCHLUSS_CODES)})")
    query = " AND ".join(teile)
    return {
        "query": query,
        "fields": TED_FELDER,
        "limit": 250,
        "scope": "ACTIVE",
        "paginationMode": "ITERATION",   # Blätter-Modus
    }


def ted_abrufen():
    """Holt alle passenden Bekanntmachungen von TED als Liste."""
    anfrage = ted_anfrage_bauen()
    alle_notices = []

    while True:
        antwort = requests.post(TED_URL, json=anfrage, timeout=60)
        antwort.raise_for_status()   # bei Fehler abbrechen, main() fängt das ab

        daten = antwort.json()
        alle_notices = alle_notices + daten["notices"]

        # TED schickt auch nach der letzten Seite noch ein Lesezeichen
        # und fängt dann von vorne an. Deshalb auch bei leerer Seite abbrechen.
        token = daten.get("iterationNextToken")
        if not token or len(daten["notices"]) == 0:
            break
        anfrage["iterationNextToken"] = token

    return alle_notices


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


def ted_zeile(notice):
    """Übersetzt eine TED-Bekanntmachung in eine Zeile im gemeinsamen Format."""
    angebot = erster(notice.get("deadline-receipt-tender-date-lot"))
    teilnahme = erster(notice.get("deadline-receipt-request-date-lot"))

    if angebot:
        frist, fristart = angebot, "Angebot"
    elif teilnahme:
        frist, fristart = teilnahme, "Teilnahmeantrag"
    else:
        frist, fristart = None, "keine Angabe"

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
        "Plattform": "TED",
        "Link zur Plattform": notice["links"]["html"]["DEU"],
    }


def ted_umwandeln(notices):
    return pd.DataFrame([ted_zeile(n) for n in notices], columns=SPALTEN)
