from agent.modell import verfahrens_ids


class DublettenErkennung:
    """Erkennt dieselbe Ausschreibung auf mehreren Plattformen oder in mehreren Fassungen.

    Regel: gleiche Verfahrens-ID = gleiche Ausschreibung (TED und öffentlichevergabe.de verwenden
    dieselbe ID, getestet 03.11.2026). Behalten wird die NEUESTE Bekanntmachung, damit z. B. eine
    verlängerte Frist gilt. Die Spalte "Gefunden auf" hält alle Plattformen fest.

    Keine Pruefung-Unterklasse, weil sie nichts mit Grund aussortiert, sondern zusammenfasst.
    """

    def entfernen(self, tabelle):
        """-> eine Zeile pro Verfahren"""
        tabelle = tabelle.copy()
        # Ohne Verfahrens-ID würden sonst alle leeren Zeilen als eine Dublette gelten
        tabelle["Verfahrens ID"] = verfahrens_ids(tabelle)

        plattformen = tabelle.groupby("Verfahrens ID")["Plattform"].agg(lambda s: ", ".join(sorted(set(s))))
        tabelle["Gefunden auf"] = tabelle["Verfahrens ID"].map(plattformen)

        tabelle = tabelle.sort_values("Publikation")
        return tabelle.drop_duplicates(subset="Verfahrens ID", keep="last")
