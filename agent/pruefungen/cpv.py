from agent.pruefungen.basis import Pruefung


class CpvPruefung(Pruefung):
    """Sortiert aus: kein ZUFALL-Code oder Hauptcode aus kriterien/ausschluss_codes.csv (z. B. Personenverkehr).

    Die Spalte "Zufall Produkt" setzt der Agent gleich nach dem Abruf für alle Zeilen (auch Dubletten).
    Fehlt sie, z. B. wenn die Prüfung allein benutzt wird, wird sie hier ergänzt."""

    name = "CPV-Codes"

    def gruende(self, tabelle):
        if "Zufall Produkt" not in tabelle.columns:
            tabelle = tabelle.assign(**{"Zufall Produkt": tabelle["Alle CPV"].map(self.kriterien.produkt_text)})

        gruende = []
        for hauptcode, produkt in zip(tabelle["Vergabe Branchen Code"], tabelle["Zufall Produkt"]):
            ausschluss = self.kriterien.ausschlussgrund(hauptcode)
            if ausschluss:
                gruende.append(f"{ausschluss} (Hauptcode)")
            elif not produkt:
                gruende.append("kein ZUFALL-CPV-Code")
            else:
                gruende.append(None)
        return tabelle, gruende
