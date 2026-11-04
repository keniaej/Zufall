"""Schreibt Ausschreibungen in eine Excel-Datei."""
import os
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font

from .quellen.beispiel_quelle import FELDER


def schreibe_excel(ausschreibungen: list[dict], ordner: str) -> str:
    os.makedirs(ordner, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Ausschreibungen"

    ws.append([f.capitalize() for f in FELDER])
    for zelle in ws[1]:
        zelle.font = Font(bold=True)

    for a in ausschreibungen:
        ws.append([a.get(f, "") for f in FELDER])

    pfad = os.path.join(ordner, f"ausschreibungen_{datetime.now():%Y-%m-%d_%H%M}.xlsx")
    wb.save(pfad)
    return pfad
