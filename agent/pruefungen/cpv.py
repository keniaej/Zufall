from agent.pruefungen.basis import Pruefung


def codes_aus_text(text):
    """'60100000, 63120000' -> ['60100000', '63120000']"""
    return [c.strip() for c in str(text).split(",") if c.strip()]


class CpvPruefung(Pruefung):
    """Ordnet das ZUFALL-Produkt zu (neue Spalte "Zufall Produkt") und sortiert aus:
    kein ZUFALL-Code oder Hauptcode aus kriterien/ausschluss_codes.csv (z. B. Personenverkehr)."""

    name = "CPV-Codes"

    def gruende(self, tabelle):
        gruende, produkte = [], []
        for _, zeile in tabelle.iterrows():
            gefunden = self.kriterien.produkte_ermitteln(codes_aus_text(zeile["Alle CPV"]))
            produkte.append(", ".join(gefunden))

            ausschluss = self.kriterien.ausschlussgrund(zeile["Vergabe Branchen Code"])
            if ausschluss:
                gruende.append(f"{ausschluss} (Hauptcode)")
            elif not gefunden:
                gruende.append("kein ZUFALL-CPV-Code")
            else:
                gruende.append(None)

        tabelle = tabelle.copy()
        tabelle["Zufall Produkt"] = produkte
        return tabelle, gruende
