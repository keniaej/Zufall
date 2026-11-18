"""Berechnet die Landkreise im Umkreis der ZUFALL-Standorte und schreibt kriterien/region_kreise.csv.

Nur ausführen, wenn sich kriterien/standorte.csv ändert (Standort, Koordinaten oder Radius):
    python werkzeuge/region_berechnen.py

Regeln (Entscheidung ZUFALL 14.11.2026, Umsetzung Projektteam 17.11.2026):
- Luftlinie ab Ortsmitte jedes Standorts, Radius aus standorte.csv (70 km)
- Ein Landkreis zählt, sobald IRGENDEIN Teil von ihm im Radius liegt ("lieber mehr als zu wenig").
  Spalte "Lage" sagt, ob sein Mittelpunkt im Radius liegt ("im Radius") oder nur ein Teil ("Randkreis").
  Randkreise kann man einfach aus der CSV löschen, wenn man es enger will.
- Landkreise = NUTS-3-Regionen von Eurostat (GISCO). TED und öffentlichevergabe.de geben den
  Leistungsort als NUTS-3-Code an. Es werden die Codes von 2021 UND 2024 eingetragen, weil
  Bekanntmachungen beide Stände verwenden können.

Braucht Internet (lädt die Kreisgrenzen einmalig, ca. 20 MB). Der Agent selbst braucht das nicht,
er liest nur die fertige region_kreise.csv.
"""
import csv
import io
import json
import math
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # damit agent/ gefunden wird
from agent.netz import json_abrufen  # noqa: E402

ORDNER = Path(__file__).resolve().parent.parent / "kriterien"
GISCO = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson"
JAHRE = ["2021", "2024"]


def km(lat1, lon1, lat2, lon2):
    """Luftlinie in km (Haversine-Formel, Erdradius 6371 km)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(a))


def abstand_zur_linie(lat, lon, a, b):
    """Abstand eines Punkts zu einer Grenzlinie von a nach b (Punkte als (lon, lat)), in km.
    Auf diesen kurzen Strecken reicht eine flache Näherung um den Punkt herum."""
    kx = 111.32 * math.cos(math.radians(lat))   # km pro Längengrad an dieser Breite
    ky = 110.57                                # km pro Breitengrad
    ax, ay = (a[0] - lon) * kx, (a[1] - lat) * ky
    bx, by = (b[0] - lon) * kx, (b[1] - lat) * ky
    dx, dy = bx - ax, by - ay
    laenge2 = dx * dx + dy * dy
    t = 0.0 if laenge2 == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / laenge2))
    return math.hypot(ax + t * dx, ay + t * dy)


def im_polygon(lat, lon, ring):
    """Liegt der Punkt in der Fläche? (Strahl-Methode)"""
    drin = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            drin = not drin
    return drin


def ringe(geometrie):
    """Alle Außenringe einer Fläche (Polygon oder MultiPolygon)."""
    if geometrie["type"] == "Polygon":
        return [geometrie["coordinates"][0]]
    return [poly[0] for poly in geometrie["coordinates"]]


def kleinster_abstand(lat, lon, geometrie):
    """0, wenn der Standort im Kreis liegt, sonst Abstand zur nächsten Kreisgrenze in km."""
    rs = ringe(geometrie)
    if any(im_polygon(lat, lon, r) for r in rs):
        return 0.0
    return min(abstand_zur_linie(lat, lon, a, b) for r in rs for a, b in zip(r, r[1:]))


def laden(datei):
    return json_abrufen(f"{GISCO}/{datei}", timeout=300, versuche=3)["features"]


def standorte_lesen():
    text = (ORDNER / "standorte.csv").read_text(encoding="utf-8-sig")
    zeilen = list(csv.DictReader(io.StringIO(text), delimiter=";"))
    return [(z["Standort"], float(z["Breitengrad"].replace(",", ".")), float(z["Längengrad"].replace(",", ".")),
             float(z["Radius km"].replace(",", "."))) for z in zeilen if z.get("Standort")]


def main():
    standorte = standorte_lesen()
    kreise = {}   # NUTS-Code -> Angaben
    for jahr in JAHRE:
        print(f"Lade Kreisgrenzen {jahr} ...")
        flaechen = laden(f"NUTS_RG_01M_{jahr}_4326_LEVL_3.geojson")
        mittelpunkte = {f["properties"]["NUTS_ID"]: f["geometry"]["coordinates"]
                        for f in laden(f"NUTS_LB_{jahr}_4326_LEVL_3.geojson")}
        for f in flaechen:
            code = f["properties"]["NUTS_ID"]
            if not code.startswith("DE"):
                continue
            mlon, mlat = mittelpunkte[code]
            treffer = []
            for name, lat, lon, radius in standorte:
                rand = kleinster_abstand(lat, lon, f["geometry"])
                if rand <= radius:
                    treffer.append((km(lat, lon, mlat, mlon), rand, name, radius))
            if not treffer:
                continue
            mitte, rand, name, radius = min(treffer)   # nächster Standort (nach Kreismittelpunkt)
            alt = kreise.get(code)
            jahre = (alt["jahre"] if alt else set()) | {jahr}
            if alt is None or mitte < alt["mitte"]:
                kreise[code] = {"name": f["properties"].get("NAME_LATN") or f["properties"].get("NUTS_NAME"),
                                "standort": name, "mitte": mitte, "rand": rand,
                                "lage": "im Radius" if mitte <= radius else "Randkreis"}
            kreise[code]["jahre"] = jahre

    zeilen = sorted(kreise.items(), key=lambda k: (k[1]["standort"], k[1]["mitte"]))
    with open(ORDNER / "region_kreise.csv", "w", newline="", encoding="utf-8-sig") as datei:
        w = csv.writer(datei, delimiter=";")
        w.writerow(["NUTS-Code", "Landkreis", "Standort", "Lage", "Entfernung Mittelpunkt km",
                    "Entfernung Rand km", "NUTS-Stand"])
        for code, k in zeilen:
            w.writerow([code, k["name"], k["standort"], k["lage"], round(k["mitte"]), round(k["rand"]),
                        ", ".join(sorted(k["jahre"]))])

    im = sum(k["lage"] == "im Radius" for k in kreise.values())
    print(f"{len(kreise)} Landkreise geschrieben: {im} im Radius, {len(kreise) - im} Randkreise")
    return 0


if __name__ == "__main__":
    sys.exit(main())
