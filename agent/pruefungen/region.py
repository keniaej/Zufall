from agent.pruefungen.basis import Pruefung


class RegionPruefung(Pruefung):
    """Regional begrenzte Produkte (Landverkehr) nur im Gebiet der Standorte (70 km, siehe
    kriterien/region_kreise.csv). Neue Spalte "Region Landverkehr".

    Fliegt nur raus, wenn ALLE Produkte regional begrenzt sind. Landverkehr + Kontraktlogistik
    bleibt also drin, weil Kontraktlogistik keine örtliche Eingrenzung hat.
    Ohne Landkreis-Angabe bleibt die Ausschreibung drin (lieber mehr als zu wenig)."""

    name = "Region"

    def gruende(self, tabelle):
        region_produkte = self.kriterien.region_produkte
        kreise_im_gebiet = self.kriterien.region_kreise
        gruende, region = [], []

        for _, zeile in tabelle.iterrows():
            produkte = [p.strip() for p in zeile["Zufall Produkt"].split(",") if p.strip()]
            if not any(p in region_produkte for p in produkte):
                region.append("")
                gruende.append(None)
                continue

            nuts = [c.strip() for c in str(zeile["Leistungsort NUTS"]).split(",") if c.strip()]
            kreise = [c for c in nuts if len(c) == 5]          # NUTS-3 = Landkreis = 5 Zeichen
            im_gebiet = [kreise_im_gebiet[c] for c in kreise if c in kreise_im_gebiet]
            nur_regional = all(p in region_produkte for p in produkte)

            if im_gebiet:
                region.append("ja: " + ", ".join(im_gebiet))
                gruende.append(None)
            elif not kreise:
                region.append("unklar (kein Landkreis angegeben)")   # lieber drin lassen
                gruende.append(None)
            else:
                region.append("nein: " + ", ".join(kreise))
                gruende.append(f"{', '.join(produkte)} außerhalb der Region" if nur_regional else None)

        tabelle = tabelle.copy()
        tabelle["Region Landverkehr"] = region
        return tabelle, gruende
