"""Die fachlichen Kriterien von ZUFALL: CPV-Codes, Produkte, Region, Ausschlüsse, Suchworte.

Sie stehen als CSV-Dateien in kriterien/ und können in Excel bearbeitet werden (kriterien/README.md).
Diese Datei liest sie ein, prüft sie und stellt sie als ein Objekt `Kriterien` bereit:

    kriterien = Kriterien.laden(Path("kriterien"))
    kriterien.cpv_codes                       # alle aktiven Codes
    kriterien.produkte_ermitteln(["60161000"])  # -> ["NSE"]

Quellen und Prüfungen bekommen dieses Objekt übergeben, statt selbst Dateien zu lesen.
"""
import csv
import re
from dataclasses import dataclass, field
from pathlib import Path


class KriterienFehler(ValueError):
    """Fehler in einer Kriterien-Datei, mit Dateiname und Zeile in der Meldung."""


def cpv_passt(code, ziel):
    """CPV-Codes sind ein Baum: 60100000 umfasst alle Codes, die mit 601 beginnen.
    Die oberste Ebene sind 2 Ziffern (Abteilung): 60000000 umfasst alles mit 60,
    nicht alles mit 6 (sonst fielen z. B. 66000000 Finanzdienste darunter)."""
    stamm = ziel.rstrip("0")
    stamm = ziel[:max(len(stamm), 2)]
    return str(code).startswith(stamm)


@dataclass
class Kriterien:
    """Eingelesene Kriterien. Für Tests kann man das Objekt auch direkt erzeugen,
    z. B. Kriterien(produkte={"Landverkehr": ["60100000"]})."""

    # CPV-Codes nach ZUFALL-Produkt gruppiert, nur aktive Codes: {"Landverkehr": ["60100000", ...]}
    produkte: dict = field(default_factory=dict)
    # Je aktivem Code: Code, Bezeichnung, Zufall Produkt, Segment
    cpv_tabelle: list = field(default_factory=list)
    # Produkte mit örtlicher Eingrenzung (aktuell nur Landverkehr)
    region_produkte: list = field(default_factory=list)
    # Landkreise im Radius: {"DE732": "Fulda (Fulda)", ...}
    region_kreise: dict = field(default_factory=dict)
    # Hauptcode in dieser Liste (inkl. Unterkategorien) -> aussortiert: {"60112000": "Personenverkehr"}
    ausschluss_codes: dict = field(default_factory=dict)
    # Wort im Titel -> aussortiert (klein geschrieben)
    ausschluss_woerter: list = field(default_factory=list)
    # Suchworte von ZUFALL. Werden noch NICHT zum Filtern verwendet (Rolle mit ZUFALL klären)
    suchworte: list = field(default_factory=list)

    @property
    def cpv_codes(self):
        """Alle aktiven Codes als eine Liste, für Abfragen und Filter."""
        return [code for codes in self.produkte.values() for code in codes]

    def produkte_ermitteln(self, codes):
        """Ordnet CPV-Codes ZUFALL-Produkten zu. Pro Code zählt der GENAUESTE passende
        ZUFALL-Code. Sonst fiele 60161000 (Paket, NSE) auch unter 60100000 (Straße, Landverkehr),
        weil es im CPV-Baum darunter liegt."""
        gefunden = set()
        for code in codes:
            kandidaten = [(len(ziel.rstrip("0")), produkt)
                          for produkt, ziele in self.produkte.items()
                          for ziel in ziele if cpv_passt(code, ziel)]
            if kandidaten:
                gefunden.add(max(kandidaten)[1])   # längster Präfix = genauester Code
        return sorted(gefunden)

    def ausschlussgrund(self, hauptcode):
        """Grund aus ausschluss_codes.csv, wenn der Hauptcode darunter fällt, sonst None."""
        for code, grund in self.ausschluss_codes.items():
            if cpv_passt(hauptcode, code):
                return grund
        return None

    @classmethod
    def laden(cls, ordner):
        """Liest alle CSV-Dateien aus `ordner` und prüft sie. Fehler nennen Datei und Zeile."""
        leser = _CsvLeser(Path(ordner))
        regional = leser.produkte()
        produkte, cpv_tabelle = leser.cpv_codes(regional)
        return cls(
            produkte=produkte,
            cpv_tabelle=cpv_tabelle,
            region_produkte=[p for p, ist_regional in regional.items() if ist_regional],
            region_kreise=leser.region_kreise(),
            ausschluss_codes=leser.ausschluss_codes(),
            ausschluss_woerter=[w.lower() for w in leser.woerter("ausschluss_woerter.csv", "Wort")],
            suchworte=leser.woerter("suchworte.csv", "Begriff"),
        )


class _CsvLeser:
    """Liest die einzelnen CSV-Dateien aus einem Ordner. Nur intern von Kriterien.laden() benutzt."""

    def __init__(self, ordner):
        self.ordner = ordner

    def lesen(self, name, pflichtspalten):
        """Liest eine CSV-Datei als Liste von Zeilen (dict pro Zeile).

        Verträgt, wie Excel CSV-Dateien speichert: UTF-8 (mit/ohne BOM) oder Windows-Zeichensatz,
        Trennzeichen Semikolon oder Komma. Leere Zeilen werden übersprungen."""
        pfad = self.ordner / name
        if not pfad.exists():
            raise KriterienFehler(f"Datei fehlt: kriterien/{name}")

        rohdaten = pfad.read_bytes()
        try:
            text = rohdaten.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = rohdaten.decode("cp1252")   # "CSV (Trennzeichen-getrennt)" aus deutschem Excel

        erste_zeile = text.splitlines()[0] if text.strip() else ""
        trennzeichen = ";" if erste_zeile.count(";") >= erste_zeile.count(",") else ","

        leser = csv.DictReader(text.splitlines(), delimiter=trennzeichen)
        spalten = [s.strip() for s in (leser.fieldnames or [])]
        fehlend = [s for s in pflichtspalten if s not in spalten]
        if fehlend:
            raise KriterienFehler(f"kriterien/{name}: Spalte(n) fehlen: {fehlend}. Gefunden: {spalten}")

        zeilen = []
        for nr, zeile in enumerate(leser, start=2):   # Zeile 1 = Überschrift
            zeile = {(k or "").strip(): (v or "").strip() for k, v in zeile.items()}
            if not any(zeile.values()):
                continue
            zeile["_zeile"] = nr
            zeilen.append(zeile)
        return zeilen

    def produkte(self):
        """produkte.csv -> {Produktname: regional begrenzt (True/False)}"""
        produkte = {}
        for z in self.lesen("produkte.csv", ["Zufall Produkt", "Regional begrenzt"]):
            name = z["Zufall Produkt"]
            if name in produkte:
                raise KriterienFehler(f"kriterien/produkte.csv, Zeile {z['_zeile']}: Produkt '{name}' doppelt")
            produkte[name] = ja_nein(z["Regional begrenzt"], "produkte.csv", z["_zeile"], "Regional begrenzt")
        return produkte

    def cpv_codes(self, bekannte_produkte):
        """cpv_codes.csv -> ({Produkt: [Codes]}, [dict je aktivem Code])"""
        produkte, tabelle, gesehen = {}, [], set()
        for z in self.lesen("cpv_codes.csv", ["Code", "Bezeichnung", "Zufall Produkt", "Aktiv"]):
            nr = z["_zeile"]
            code = cpv_normalisieren(z["Code"], "cpv_codes.csv", nr)
            if code in gesehen:
                raise KriterienFehler(f"kriterien/cpv_codes.csv, Zeile {nr}: Code {code} steht doppelt in der Liste")
            gesehen.add(code)
            if not ja_nein(z["Aktiv"], "cpv_codes.csv", nr, "Aktiv"):
                continue
            produkt = z["Zufall Produkt"]
            if produkt not in bekannte_produkte:
                raise KriterienFehler(
                    f"kriterien/cpv_codes.csv, Zeile {nr}: Produkt '{produkt}' gibt es nicht in kriterien/produkte.csv. "
                    f"Erlaubt: {', '.join(bekannte_produkte)}")
            produkte.setdefault(produkt, []).append(code)
            tabelle.append({"Code": code, "Bezeichnung": z["Bezeichnung"], "Zufall Produkt": produkt,
                            "Segment": z.get("Segment", "")})
        if not tabelle:
            raise KriterienFehler("kriterien/cpv_codes.csv: kein aktiver CPV-Code")
        return produkte, tabelle

    def region_kreise(self):
        """region_kreise.csv -> {NUTS-Code: 'Landkreis (Standort)'}"""
        kreise = {}
        for z in self.lesen("region_kreise.csv", ["NUTS-Code", "Landkreis"]):
            nuts = z["NUTS-Code"].upper()
            if not re.fullmatch(r"DE[0-9A-Z]{3}", nuts):
                raise KriterienFehler(f"kriterien/region_kreise.csv, Zeile {z['_zeile']}: "
                                      f"'{z['NUTS-Code']}' ist kein Landkreis-Code (z. B. DE732)")
            standort = z.get("Standort", "")
            kreise[nuts] = f"{z['Landkreis']} ({standort})" if standort else z["Landkreis"]
        return kreise

    def ausschluss_codes(self):
        """ausschluss_codes.csv -> {Code: Grund}"""
        return {cpv_normalisieren(z["Code"], "ausschluss_codes.csv", z["_zeile"]): z.get("Grund") or "Ausschluss-Code"
                for z in self.lesen("ausschluss_codes.csv", ["Code"])}

    def woerter(self, name, spalte):
        return [z[spalte] for z in self.lesen(name, [spalte]) if z[spalte]]


def cpv_normalisieren(wert, datei, zeile):
    """'60100000-9' -> '60100000'. Ergänzt führende Nullen, die Excel bei Zahlen weglässt."""
    code = wert.split("-")[0].strip()
    if code.endswith(".0"):            # Excel speichert Zahlen manchmal als 60100000.0
        code = code[:-2]
    if not code.isdigit() or len(code) > 8:
        raise KriterienFehler(f"kriterien/{datei}, Zeile {zeile}: '{wert}' ist kein CPV-Code (8 Ziffern)")
    return code.zfill(8)


def ja_nein(wert, datei, zeile, spalte):
    w = wert.lower()
    if w in ("ja", "j", "x", "yes", "1", "wahr", "true"):
        return True
    if w in ("nein", "n", "", "no", "0", "falsch", "false"):
        return False
    raise KriterienFehler(f"kriterien/{datei}, Zeile {zeile}: Spalte '{spalte}' muss 'ja' oder 'nein' sein, nicht '{wert}'")
