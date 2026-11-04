"""Quelle: TED (Tenders Electronic Daily, EU-Ausschreibungsportal)

Braucht keinen API-Key.
"""
import pandas as pd
import requests

from agent.format import SPALTEN, datum, erster
from agent.konfiguration import CPV_CODES, LAENDER, NOTICE_TYPEN, PERSONENVERKEHR, SEIT_DATUM

TED_URL = "https://api.ted.europa.eu/v3/notices/search"

TED_FELDER = [
    "publication-number", "procedure-identifier", "publication-date", "notice-type",
    "notice-title", "main-classification-proc", "classification-cpv",
    "organisation-name-buyer", "organisation-city-buyer",
    "deadline-receipt-tender-date-lot", "deadline-receipt-request-date-lot",
    "place-of-performance",   # Leistungsort
]


def ted_anfrage_bauen():
    """TED kann schon serverseitig filtern. Das spart Datenmenge.
    Die CPV-Prüfung in pruefungen.py läuft trotzdem, damit alle Quellen gleich behandelt werden."""
    query = (
        f"classification-cpv IN ({' '.join(CPV_CODES)}) "
        f"AND buyer-country IN ({' '.join(LAENDER)}) "
        f"AND publication-date>={SEIT_DATUM} "
        f"AND NOT main-classification-proc IN ({' '.join(PERSONENVERKEHR)}) "
        f"AND notice-type IN ({' '.join(NOTICE_TYPEN)})"
    )
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

    # TED führt CPV-Codes pro Los auf, daher doppelte entfernen
    alle_cpv = sorted(set(notice.get("classification-cpv") or []))

    return {
        "Ausschreibungs ID Platform": notice.get("publication-number"),
        "Verfahrens ID": notice.get("procedure-identifier"),
        "Publikation": datum(notice.get("publication-date")),
        "Art": notice.get("notice-type"),
        "Titel": notice.get("notice-title", {}).get("deu"),
        "Vergabe Branchen Code": erster(notice.get("main-classification-proc")),
        "Alle CPV": ", ".join(alle_cpv),
        "Auftraggeber": erster(notice.get("organisation-name-buyer", {}).get("deu")),
        "Stadt": erster(notice.get("organisation-city-buyer")),
        "Leistungsort NUTS": ", ".join(sorted(set(notice.get("place-of-performance") or []))),
        "Angebotsfrist": datum(frist),
        "Fristart": fristart,
        "Plattform": "TED",
        "Link zur Plattform": notice["links"]["html"]["DEU"],
    }


def ted_umwandeln(notices):
    return pd.DataFrame([ted_zeile(n) for n in notices], columns=SPALTEN)
