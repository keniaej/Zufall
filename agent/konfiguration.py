"""TEIL 1: KONFIGURATION

Die fachlichen Kriterien (CPV-Codes, Produkte, Region, Ausschlüsse, Suchworte) stehen
NICHT hier, sondern als CSV-Dateien im Ordner `kriterien/`. ZUFALL kann sie in Excel
bearbeiten, ohne den Code anzufassen. Anleitung: kriterien/README.md

Hier stehen nur technische Einstellungen und das Einlesen der CSV-Dateien.
"""
import csv
import re
from pathlib import Path

SEIT_DATUM = "20260801"   # Bekanntmachungen ab diesem Datum (JJJJMMTT)
LAENDER = ["DEU"]         # Land des Auftraggebers

# Arten von Bekanntmachungen (TED und öffentlichevergabe.de verwenden dieselben Kürzel)
NOTICE_TYPEN = [
    "cn-standard",       # Ausschreibung (auch Änderungsbekanntmachungen)
    "cn-social",         # Ausschreibung soziale Dienstleistungen
    "cn-desg",           # Planungswettbewerb
    "pin-cfc-standard",  # Vorinformation als Aufruf zum Wettbewerb
    "qu-sy",             # Qualifizierungssystem, mit Eike klären
]

# Wohin die Excel-Datei geschrieben wird
OUTPUT_ORDNER = "output"

KRITERIEN_ORDNER = Path(__file__).resolve().parent.parent / "kriterien"


# ---------------------------------------------------------------------------
# Einlesen der CSV-Dateien
# ---------------------------------------------------------------------------

class KriterienFehler(ValueError):
    """Fehler in einer Kriterien-Datei, mit Dateiname und Zeile in der Meldung."""


def csv_lesen(name, pflichtspalten):
    """Liest eine CSV-Datei aus kriterien/ als Liste von Zeilen (dict pro Zeile).

    Verträgt, wie Excel CSV-Dateien speichert: UTF-8 (mit/ohne BOM) oder Windows-Zeichensatz,
    Trennzeichen Semikolon oder Komma. Leere Zeilen werden übersprungen."""
    pfad = KRITERIEN_ORDNER / name
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


def produkte_laden():
    """produkte.csv -> {Produktname: regional begrenzt (True/False)}"""
    produkte = {}
    for z in csv_lesen("produkte.csv", ["Zufall Produkt", "Regional begrenzt"]):
        name = z["Zufall Produkt"]
        if name in produkte:
            raise KriterienFehler(f"kriterien/produkte.csv, Zeile {z['_zeile']}: Produkt '{name}' doppelt")
        produkte[name] = ja_nein(z["Regional begrenzt"], "produkte.csv", z["_zeile"], "Regional begrenzt")
    return produkte


def cpv_codes_laden(bekannte_produkte):
    """cpv_codes.csv -> (PRODUKTE {Produkt: [Codes]}, CPV_TABELLE [dict je aktivem Code])"""
    produkte, tabelle, gesehen = {}, [], set()
    for z in csv_lesen("cpv_codes.csv", ["Code", "Bezeichnung", "Zufall Produkt", "Aktiv"]):
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


def region_laden():
    """region_kreise.csv -> {NUTS-Code: 'Landkreis (Standort)'}"""
    kreise = {}
    for z in csv_lesen("region_kreise.csv", ["NUTS-Code", "Landkreis"]):
        nuts = z["NUTS-Code"].upper()
        if not re.fullmatch(r"DE[0-9A-Z]{3}", nuts):
            raise KriterienFehler(
                f"kriterien/region_kreise.csv, Zeile {z['_zeile']}: '{z['NUTS-Code']}' ist kein Landkreis-Code (z. B. DE732)")
        standort = z.get("Standort", "")
        kreise[nuts] = f"{z['Landkreis']} ({standort})" if standort else z["Landkreis"]
    return kreise


def ausschluss_codes_laden():
    """ausschluss_codes.csv -> {Code: Grund}"""
    return {cpv_normalisieren(z["Code"], "ausschluss_codes.csv", z["_zeile"]): z.get("Grund") or "Ausschluss-Code"
            for z in csv_lesen("ausschluss_codes.csv", ["Code"])}


def woerter_laden(name, spalte):
    return [z[spalte] for z in csv_lesen(name, [spalte]) if z[spalte]]


_PRODUKT_REGIONAL = produkte_laden()

# CPV-Codes nach ZUFALL-Produkt gruppiert, nur aktive Codes
PRODUKTE, CPV_TABELLE = cpv_codes_laden(_PRODUKT_REGIONAL)

# Alle Codes als eine Liste, für Abfragen und Filter
CPV_CODES = [code for codes in PRODUKTE.values() for code in codes]

# Örtliche Eingrenzung (Entscheidung 14.11./17.11.2026):
#   - 70 km Luftlinie um die Ortsmitte jedes Standorts (kriterien/standorte.csv)
#   - Region = alle Landkreise, die ganz oder teilweise im Radius liegen (kriterien/region_kreise.csv,
#     berechnet mit werkzeuge/region_berechnen.py)
#   - Es zählt der LEISTUNGSORT (wo gefahren wird), nicht der Sitz des Auftraggebers (Annahme)
REGION_PRODUKTE = [p for p, regional in _PRODUKT_REGIONAL.items() if regional]
REGION_KREISE = region_laden()

# Hauptcode einer Ausschreibung in dieser Liste (inkl. Unterkategorien) -> aussortiert
AUSSCHLUSS_CODES = ausschluss_codes_laden()

# Wort im Titel -> aussortiert (Groß-/Kleinschreibung egal, passt auch auf Wortanfänge)
AUSSCHLUSS_WOERTER = [w.lower() for w in woerter_laden("ausschluss_woerter.csv", "Wort")]

# Suchworte von ZUFALL. Werden noch NICHT zum Filtern verwendet (Rolle mit ZUFALL klären)
SUCHWORTE = woerter_laden("suchworte.csv", "Begriff")
