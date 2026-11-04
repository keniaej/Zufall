"""SCHRITT 3: EXCEL-EXPORT

Schreibt das Ergebnis immer in DIESELBE Datei: output/ausschreibungen.xlsx
Bei jedem Lauf wird sie mit dem aktuellen Stand überschrieben. So kann Power BI
fest mit dieser einen Datei verbunden bleiben und muss nur aktualisiert werden.

Drei Blätter:
- Relevant:     Ausschreibungen, die alle Prüfungen bestanden haben
- Aussortiert:  alles andere, mit Ausschlussgrund
- Status:       wann der Lauf war und welche Quelle wie viele Bekanntmachungen geliefert hat

OFFEN: Formatierung, Spaltenbreiten, Filter, klickbare Links ...
"""
import os
from datetime import datetime

import pandas as pd

from agent.konfiguration import OUTPUT_ORDNER

DATEINAME = "ausschreibungen.xlsx"


def excel_schreiben(relevant, aussortiert, status):
    os.makedirs(OUTPUT_ORDNER, exist_ok=True)
    pfad = os.path.join(OUTPUT_ORDNER, DATEINAME)

    status_tabelle = pd.DataFrame(
        [("Letzter Lauf", f"{datetime.now():%d.%m.%Y %H:%M}")] + list(status.items()),
        columns=["Quelle", "Status"],
    )
    try:
        with pd.ExcelWriter(pfad) as excel:
            relevant.to_excel(excel, sheet_name="Relevant", index=False)
            aussortiert.to_excel(excel, sheet_name="Aussortiert", index=False)
            status_tabelle.to_excel(excel, sheet_name="Status", index=False)
    except PermissionError:
        raise PermissionError(f"{pfad} ist gerade geöffnet (z. B. in Excel). Bitte schließen und neu starten.")
    return pfad
