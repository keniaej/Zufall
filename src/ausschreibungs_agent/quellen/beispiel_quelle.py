"""Vorlage für eine Ausschreibungsquelle.

Für jedes Portal wird eine Kopie dieser Datei angelegt. Jede Quelle liefert
eine Liste von Dictionaries mit denselben Feldern zurück, damit der
Excel-Export für alle Quellen gleich funktioniert.
"""

FELDER = ["titel", "auftraggeber", "frist", "ort", "link", "quelle"]


def hole_ausschreibungen(api_key: str, suchbegriffe: list[str]) -> list[dict]:
    """Holt Ausschreibungen von diesem Portal.

    TODO: Echten API-Aufruf einbauen, z. B. mit requests.get(...).
    Bis dahin werden Beispieldaten zurückgegeben, damit der Rest testbar ist.
    """
    return [
        {
            "titel": "Beispiel: Entwicklung einer Webanwendung",
            "auftraggeber": "Musterstadt",
            "frist": "2026-12-01",
            "ort": "Berlin",
            "link": "https://example.com/ausschreibung/1",
            "quelle": "Beispielquelle",
        }
    ]
