"""SCHRITT 3: EXCEL-EXPORT

Schreibt das Ergebnis in eine Excel-Datei mit drei Blättern:
- Relevant:     Ausschreibungen, die alle Prüfungen bestanden haben
- Aussortiert:  alles andere, mit Ausschlussgrund
- Status:       welche Quelle wie viele Bekanntmachungen geliefert hat (oder einen Fehler)

Einfache erste Version. OFFEN: Formatierung, Spaltenbreiten, Filter, klickbare Links ...
"""
import os
from datetime import datetime

import pandas as pd

from agent.konfiguration import OUTPUT_ORDNER


def excel_schreiben(relevant, aussortiert, status):
    os.makedirs(OUTPUT_ORDNER, exist_ok=True)
    pfad = os.path.join(OUTPUT_ORDNER, f"ausschreibungen_{datetime.now():%Y-%m-%d_%H%M}.xlsx")

    status_tabelle = pd.DataFrame(list(status.items()), columns=["Quelle", "Status"])
    with pd.ExcelWriter(pfad) as excel:
        relevant.to_excel(excel, sheet_name="Relevant", index=False)
        aussortiert.to_excel(excel, sheet_name="Aussortiert", index=False)
        status_tabelle.to_excel(excel, sheet_name="Status", index=False)
    return pfad
