"""Startpunkt des Agenten."""
from . import config
from .excel_export import schreibe_excel
from .quellen import beispiel_quelle


def main() -> None:
    ausschreibungen = []
    # Neue Quellen hier ergänzen:
    ausschreibungen += beispiel_quelle.hole_ausschreibungen(
        config.BEISPIEL_QUELLE_API_KEY, config.SUCHBEGRIFFE
    )

    pfad = schreibe_excel(ausschreibungen, config.OUTPUT_ORDNER)
    print(f"{len(ausschreibungen)} Ausschreibungen gespeichert in {pfad}")


if __name__ == "__main__":
    main()
