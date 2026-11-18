from agent.modell import verfahrens_ids


class DublettenErkennung:
    """Erkennt dieselbe Ausschreibung auf mehreren Plattformen oder in mehreren Fassungen.

    Regel: gleiche Verfahrens-ID = gleiche Ausschreibung (TED und öffentlichevergabe.de verwenden
    dieselbe ID, getestet 03.11.2026). Behalten wird die NEUESTE Bekanntmachung, damit z. B. eine
    verlängerte Frist gilt.

    Keine Pruefung-Unterklasse, weil sie nichts mit Grund aussortiert, sondern zusammenfasst.
    """

    @staticmethod
    def gefunden_auf(tabelle):
        """Je Zeile alle Plattformen, auf denen dieses Verfahren vorkommt, z. B. "TED, oeffentlichevergabe.de"."""
        schluessel = verfahrens_ids(tabelle)
        plattformen = tabelle.groupby(schluessel)["Plattform"].agg(lambda s: ", ".join(sorted(set(s))))
        return schluessel.map(plattformen)

    @staticmethod
    def entfernen(tabelle):
        """-> eine Zeile pro Verfahren (die neueste). Die Zeilennummern bleiben erhalten.
        Am selben Tag auf mehreren Plattformen: Es gewinnt die Quelle, die in
        agent/quellen/__init__.py (QUELLEN_KLASSEN) zuerst steht, also TED. So bleibt die Wahl bei jedem Lauf gleich."""
        schluessel = verfahrens_ids(tabelle)
        neueste_zuerst = tabelle["Publikation"].sort_values(ascending=False, kind="stable").index
        return tabelle.loc[schluessel[neueste_zuerst].drop_duplicates(keep="first").index]
