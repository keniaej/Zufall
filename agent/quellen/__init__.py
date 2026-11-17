"""Die Ausschreibungsportale (Quellen). Jede ist eine Klasse, die von Quelle erbt (siehe basis.py).

Neue Quelle: vorlage.py kopieren, ausfüllen und die Klasse hier in QUELLEN_KLASSEN eintragen.
"""
from agent.quellen.basis import Quelle
from agent.quellen.oeffentlichevergabe import OeffentlicheVergabeQuelle
from agent.quellen.ted import TedQuelle

# Reihenfolge = Reihenfolge der Blätter im Excel
QUELLEN_KLASSEN = [TedQuelle, OeffentlicheVergabeQuelle]


def alle_quellen(kriterien, einstellungen):
    """Erzeugt je Klasse ein Quellen-Objekt mit Kriterien und Einstellungen."""
    return [klasse(kriterien, einstellungen) for klasse in QUELLEN_KLASSEN]


__all__ = ["Quelle", "TedQuelle", "OeffentlicheVergabeQuelle", "QUELLEN_KLASSEN", "alle_quellen"]
