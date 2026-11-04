"""TEIL 1: KONFIGURATION

Alles, was ZUFALL oder ihr später anpassen wollt, steht hier und nur hier.
"""

SEIT_DATUM = "20260801"   # Bekanntmachungen ab diesem Datum (JJJJMMTT)
LAENDER = ["DEU"]         # Land des Auftraggebers

# CPV-Codes nach ZUFALL-Produkt gruppiert (aus ZUFALLs Kriterien-Excel)
PRODUKTE = {
    "Seefracht":        ["60600000", "60640000", "60650000"],
    # KLÄREN mit ZUFALL: 60440000 heißt laut ZUFALL "Luftfracht- und Posttransportdienste",
    # in den TED-Daten aber "Dienstleistungen unter Einsatz von Luftfahrzeugen".
    # Bringt Hagelabwehrflüge, Drohnen, Helikopter, Flugzieldarstellung, keine Luftfracht.
    # Ebenso 60410000 (Linienflugverkehr): bringt Passagierflüge ("PAX weltweit").
    "Luftfracht":       ["60400000", "60410000", "60420000", "60440000"],
    "Landverkehr":      ["60100000", "60180000"],
    "NSE":              ["60160000", "60161000", "64120000", "64121000", "64121200"],
    "Kontraktlogistik": ["63120000", "63121000", "63121100", "63122000"],
}

# Alle Codes als eine Liste, für Abfragen und Filter (wird aus PRODUKTE erzeugt)
CPV_CODES = [code for codes in PRODUKTE.values() for code in codes]

# Örtliche Eingrenzung. Nur Landverkehr ist regional begrenzt.
# ANNAHME, mit ZUFALL zu klären:
#   - Es zählt der LEISTUNGSORT (wo gefahren wird), nicht der Sitz des Auftraggebers
#   - Region = Landkreise der Standorte (NUTS-3), ohne Nachbarkreise
# NUTS-Codes am 03.11.2026 an echten Daten von öffentlichevergabe.de geprüft.
REGION_PRODUKTE = ["Landverkehr"]
REGION_KREISE = {
    "DE91C": "LK Göttingen",
    "DE731": "Kassel (Stadt)",
    "DE734": "LK Kassel",
    "DE732": "LK Fulda (Fulda, Eichenzell)",
    "DE722": "Lahn-Dill-Kreis (Haiger)",
    "DEG0G": "Weimarer Land (Grammetal)",
}

PERSONENVERKEHR = ["60112000", "60120000", "60130000", "60140000", "60170000"]

# Arten von Bekanntmachungen (TED und öffentlichevergabe.de verwenden dieselben Kürzel)
NOTICE_TYPEN = [
    "cn-standard",       # Ausschreibung (auch Änderungsbekanntmachungen)
    "cn-social",         # Ausschreibung soziale Dienstleistungen
    "cn-desg",           # Planungswettbewerb
    "pin-cfc-standard",  # Vorinformation als Aufruf zum Wettbewerb
    "qu-sy",             # Qualifizierungssystem, mit Eike klären
]

AUSSCHLUSS_WOERTER = ["pax", "passagier", "fluggast", "personenbeförderung",
                      "schülerbeförderung", "schülerverkehr", "busverkehr", "linienverkehr"]

# Wohin die Excel-Datei geschrieben wird
OUTPUT_ORDNER = "output"
