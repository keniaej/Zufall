import pandas as pd

from agent.pruefungen.basis import Pruefung


class FristPruefung(Pruefung):
    """Frist ab heute oder keine Frist angegeben. Abgelaufene Fristen fliegen raus."""

    name = "Frist"

    def __init__(self, kriterien, heute=None):
        super().__init__(kriterien)
        # heute einstellbar, damit Tests nicht vom Datum abhängen
        self.heute = heute

    def gruende(self, tabelle):
        heute = self.heute if self.heute is not None else pd.Timestamp.today().normalize()
        abgelaufen = tabelle["Angebotsfrist"] < heute
        return tabelle, ["Frist abgelaufen" if a else None for a in abgelaufen]
