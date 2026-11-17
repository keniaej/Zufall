"""Einstiegspunkt: Lädt die Ausschreibungen der letzten 7 Tage.

Ergebnis: Ausschreibungen.xlsx, ein Blatt je Plattform.

Aufruf: ``python main.py``
"""

from __future__ import annotations

import logging
import sys
from datetime import date, timedelta
from pathlib import Path

from branchen_codes import KRITERIEN, KriterienKatalog, Vergabeplattform
from excel_manager import ExcelManager
from oeffentliche_vergabe import OeffentlicheVergabe
from ted import Ted

EXCEL_DATEI = Path(__file__).with_name("Ausschreibungen.xlsx")
TAGE = 7

log = logging.getLogger("import")


def plattformen(katalog: KriterienKatalog) -> list[Vergabeplattform]:
    """Alle angebundenen Vergabeplattformen. Neue Module hier ergänzen."""
    return [OeffentlicheVergabe(), Ted(katalog.cpv_praefixe)]


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    bis = date.today() - timedelta(days=1)  # Tagesexporte gibt es nur für abgeschlossene Tage
    von = bis - timedelta(days=TAGE - 1)

    katalog = KriterienKatalog.aus_zeilen(KRITERIEN)

    treffer = []
    for plattform in plattformen(katalog):
        log.info("%s: Abruf %s bis %s …", plattform.name, von, bis)
        try:
            relevant = katalog.filtern(plattform.abrufen(von, bis))
        except Exception:  # eine fehlerhafte Plattform soll die anderen nicht blockieren
            log.exception("%s: Abruf fehlgeschlagen", plattform.name)
            continue
        log.info("%s: %d relevante Ausschreibungen", plattform.name, len(relevant))
        treffer += relevant

    try:
        neu, aktualisiert = ExcelManager(EXCEL_DATEI).speichern(treffer)
    except PermissionError:
        log.error("%s ist gesperrt – bitte schließen und neu starten.", EXCEL_DATEI.name)
        return 1
    log.info("Fertig: %d neu, %d aktualisiert", neu, aktualisiert)
    return 0


if __name__ == "__main__":
    sys.exit(main())
