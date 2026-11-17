"""TEIL 2: GEMEINSAMES FORMAT

Der "Vertrag" zwischen den Quellen und dem Rest des Programms.
Jede umwandeln-Funktion muss eine Tabelle mit genau diesen Spalten liefern.
"""
import pandas as pd

SPALTEN = [
    "Ausschreibungs ID Platform",  # ID auf der jeweiligen Plattform
    "Verfahrens ID",               # ID des Vergabeverfahrens, für Dubletten
    "Publikation",                 # Datum (datetime)
    "Art",                         # Art der Bekanntmachung
    "Titel",
    "Vergabe Branchen Code",       # Haupt-CPV-Code
    "Alle CPV",                    # alle CPV-Codes, kommagetrennt
    "Auftraggeber",
    "Email",                       # E-Mail des Auftraggebers
    "Stadt",
    "Straße",
    "PLZ",                         # als Text, sonst verschwindet die 0 in 02625
    "Land",                        # ausgeschrieben, z. B. "Deutschland"
    "Vergabeart",                  # ausgeschrieben, siehe VERGABEARTEN
    "Vertragsdauer in Monaten",    # Zahl oder leer, siehe laufzeit()
    "Vertragsbeginn",              # Datum (datetime) oder leer, frühester Beginn aller Lose
    "Vertragsende",                # Datum (datetime) oder leer, spätestes Ende aller Lose (ohne Verlängerungen)
    "Leistungsort NUTS",           # Regionscodes des Leistungsorts, kommagetrennt
    "Angebotsfrist",               # Datum (datetime) oder leer
    "Fristart",                    # "Angebot", "Teilnahmeantrag" oder "keine Angabe"
    "Plattform",
    "Link zur Plattform",
]

# eForms-Kürzel der Verfahrensart (TED und öffentlichevergabe.de gleich) -> Klartext
VERGABEARTEN = {
    "open": "Offenes Verfahren",
    "restricted": "Nicht offenes Verfahren",
    "neg-w-call": "Verhandlungsverfahren mit Teilnahmewettbewerb",
    "neg-wo-call": "Verhandlungsverfahren ohne Teilnahmewettbewerb",
    "comp-dial": "Wettbewerblicher Dialog",
    "innovation": "Innovationspartnerschaft",
    "comp-tend": "Wettbewerb (Rahmenvereinbarung)",
    "oth-single": "Sonstiges einstufiges Verfahren",
    "oth-mult": "Sonstiges mehrstufiges Verfahren",
}

LAENDER_NAMEN = {
    "DEU": "Deutschland", "AUT": "Österreich", "CHE": "Schweiz", "NLD": "Niederlande",
    "BEL": "Belgien", "LUX": "Luxemburg", "FRA": "Frankreich", "POL": "Polen",
    "CZE": "Tschechien", "DNK": "Dänemark",
}


def vergabeart(kuerzel):
    if not kuerzel or pd.isna(kuerzel):
        return None
    return VERGABEARTEN.get(str(kuerzel), str(kuerzel))


def land(kuerzel):
    if not kuerzel or pd.isna(kuerzel):
        return None
    return LAENDER_NAMEN.get(str(kuerzel), str(kuerzel))


def dauer_in_monaten(werte, einheiten):
    """Vertragsdauer pro Los -> längste Dauer in Monaten (gerundet). Leer, wenn nichts angegeben.
    Einheiten wie in eForms: DAY, WEEK, MONTH, YEAR."""
    faktor = {"DAY": 1 / 30.44, "WEEK": 7 / 30.44, "MONTH": 1, "YEAR": 12}
    monate = []
    for wert, einheit in zip(werte, einheiten):
        try:
            monate.append(float(wert) * faktor[str(einheit).upper()])
        except (KeyError, TypeError, ValueError):
            continue
    return round(max(monate)) if monate else None


def laufzeit(werte, einheiten, beginne, enden):
    """Vertragslaufzeit aus den Angaben pro Los (Grundlaufzeit, ohne Verlängerungsoptionen).

    Bekanntmachungen geben die Laufzeit unterschiedlich an:
    - als Dauer mit Einheit (z. B. 24 MONTH)  -> wird direkt genommen
    - nur als Start- und Enddatum             -> Dauer = Ende - Beginn, in Monaten
    Gibt (Monate, frühester Beginn, spätestes Ende) zurück, jeweils leer, wenn nicht angegeben."""
    beginne = [datum(b) for b in beginne if b and not pd.isna(b)]
    enden = [datum(e) for e in enden if e and not pd.isna(e)]
    beginn = min(beginne) if beginne else None
    ende = max(enden) if enden else None

    monate = dauer_in_monaten(werte, einheiten)
    if monate is None and beginn is not None and ende is not None and ende >= beginn:
        tage = (ende - beginn).days + 1             # 01.02.2027 bis 31.01.2031 = 48 Monate
        monate = max(round(tage / 30.44), 1)       # sehr kurze Aufträge nicht als 0 Monate
    return monate, beginn, ende


def datum(text):
    """Macht aus '2026-09-08+02:00' oder '2026-12-01Z' ein echtes Datum. Leer bleibt leer."""
    if not text or pd.isna(text):
        return None
    return pd.to_datetime(str(text)[:10])


def erster(wert):
    """Gibt das erste Element zurück, wenn wert eine Liste ist."""
    if isinstance(wert, list) and len(wert) > 0:
        return wert[0]
    return wert


def cpv_passt(code, ziel):
    """CPV-Codes sind ein Baum: 60100000 umfasst alle Codes, die mit 601 beginnen.
    Die oberste Ebene sind 2 Ziffern (Abteilung): 60000000 umfasst alles mit 60,
    nicht alles mit 6 (sonst fielen z. B. 66000000 Finanzdienste darunter)."""
    stamm = ziel.rstrip("0")
    stamm = ziel[:max(len(stamm), 2)]
    return str(code).startswith(stamm)


def text_bereinigen(wert):
    """Zeilenumbrüche und Tabs -> Leerzeichen, mehrfache Leerzeichen -> eins, Rand weg.
    Leerer Text wird zu None, damit "leer" überall gleich aussieht (wichtig für Power BI)."""
    if not isinstance(wert, str):
        return wert
    wert = " ".join(wert.split())
    return wert or None


def spalten_pruefen(tabelle, quelle):
    """Bricht mit klarer Meldung ab, wenn eine Quelle sich nicht an das Format hält.
    Bereinigt außerdem alle Texte, damit jede Quelle gleich sauber ankommt."""
    fehlend = [s for s in SPALTEN if s not in tabelle.columns]
    if fehlend:
        raise ValueError(f"Quelle '{quelle}' liefert diese Spalten nicht: {fehlend}")
    tabelle = tabelle[SPALTEN].copy()
    for spalte in SPALTEN:
        if tabelle[spalte].dtype == object or str(tabelle[spalte].dtype).startswith("str"):
            tabelle[spalte] = tabelle[spalte].map(text_bereinigen)
    return tabelle
