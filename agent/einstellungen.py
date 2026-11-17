"""Technische Einstellungen des Agenten.

Die fachlichen Kriterien (CPV-Codes, Region, Ausschlüsse ...) stehen NICHT hier, sondern als
CSV-Dateien in kriterien/ (siehe agent/kriterien.py und kriterien/README.md).
"""
from dataclasses import dataclass, field
from pathlib import Path

REPO_ORDNER = Path(__file__).resolve().parent.parent


@dataclass
class Einstellungen:
    """Alles, was nicht fachliches Kriterium ist. Für Tests einfach mit anderen Werten erzeugen,
    z. B. Einstellungen(ausgabe_ordner=tmp_path)."""

    # Bekanntmachungen ab diesem Datum (JJJJMMTT)
    seit_datum: str = "20260801"

    # Land des Auftraggebers (eForms-Kürzel)
    laender: list = field(default_factory=lambda: ["DEU"])

    # Arten von Bekanntmachungen (TED und öffentlichevergabe.de verwenden dieselben Kürzel)
    notice_typen: list = field(default_factory=lambda: [
        "cn-standard",       # Ausschreibung (auch Änderungsbekanntmachungen)
        "cn-social",         # Ausschreibung soziale Dienstleistungen
        "cn-desg",           # Planungswettbewerb
        "pin-cfc-standard",  # Vorinformation als Aufruf zum Wettbewerb
        "qu-sy",             # Qualifizierungssystem, mit Eike klären
    ])

    # Wo die Kriterien-CSVs liegen und wohin die Excel-Datei geschrieben wird
    kriterien_ordner: Path = REPO_ORDNER / "kriterien"
    ausgabe_ordner: Path = Path("output")
