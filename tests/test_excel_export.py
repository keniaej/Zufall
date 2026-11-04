from openpyxl import load_workbook

from src.ausschreibungs_agent.excel_export import schreibe_excel
from src.ausschreibungs_agent.quellen.beispiel_quelle import hole_ausschreibungen


def test_excel_wird_erstellt(tmp_path):
    daten = hole_ausschreibungen("", [])
    pfad = schreibe_excel(daten, str(tmp_path))
    ws = load_workbook(pfad).active
    assert ws.cell(1, 1).value == "Titel"
    assert ws.max_row == len(daten) + 1
