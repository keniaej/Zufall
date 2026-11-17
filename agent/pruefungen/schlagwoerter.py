import re

from agent.pruefungen.basis import Pruefung


class SchlagwortPruefung(Pruefung):
    """Wort aus kriterien/ausschluss_woerter.csv im Titel -> raus.
    Groß-/Kleinschreibung egal, passt auch auf Wortanfänge ("pax" trifft "PAX-Flüge")."""

    name = "Schlagwörter"

    def gruende(self, tabelle):
        woerter = self.kriterien.ausschluss_woerter
        if not woerter:
            return tabelle, [None] * len(tabelle)
        # re.escape: Sonderzeichen in der CSV (z. B. Klammern) sollen nichts kaputt machen
        muster = r"\b(?:" + "|".join(re.escape(w) for w in woerter) + ")"
        treffer = tabelle["Titel"].str.extract(f"({muster})", flags=re.IGNORECASE)[0]
        return tabelle, [f"Schlagwort im Titel: {w.lower()}" if isinstance(w, str) else None for w in treffer]
