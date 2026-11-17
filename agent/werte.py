"""Kleine Hilfsfunktionen, um Werte der Plattformen einheitlich zu machen (Datum, Land, Laufzeit ...).

Reine Funktionen ohne Zustand, deshalb keine Klassen. Werden von allen Quellen benutzt.
"""
import pandas as pd

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


def leer(wert):
    """True für None, NaN und leeren Text."""
    if wert is None or (isinstance(wert, str) and wert == ""):
        return True
    try:
        return bool(pd.isna(wert))
    except (TypeError, ValueError):
        return False


def vergabeart(kuerzel):
    if leer(kuerzel):
        return None
    return VERGABEARTEN.get(str(kuerzel), str(kuerzel))


def land(kuerzel):
    if leer(kuerzel):
        return None
    return LAENDER_NAMEN.get(str(kuerzel), str(kuerzel))


def datum(text):
    """Macht aus '2026-09-08+02:00' oder '2026-12-01Z' ein echtes Datum. Leer bleibt leer."""
    if leer(text):
        return None
    return pd.to_datetime(str(text)[:10])


def erster(wert):
    """Gibt das erste Element zurück, wenn wert eine Liste ist."""
    if isinstance(wert, list) and len(wert) > 0:
        return wert[0]
    return wert


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
    beginne = [datum(b) for b in beginne if not leer(b)]
    enden = [datum(e) for e in enden if not leer(e)]
    beginn = min(beginne) if beginne else None
    ende = max(enden) if enden else None

    monate = dauer_in_monaten(werte, einheiten)
    if monate is None and beginn is not None and ende is not None and ende >= beginn:
        tage = (ende - beginn).days + 1             # 01.02.2027 bis 31.01.2031 = 48 Monate
        monate = max(round(tage / 30.44), 1)       # sehr kurze Aufträge nicht als 0 Monate
    return monate, beginn, ende


def text_bereinigen(wert):
    """Zeilenumbrüche und Tabs -> Leerzeichen, mehrfache Leerzeichen -> eins, Rand weg.
    Leerer Text wird zu None, damit "leer" überall gleich aussieht (wichtig für Power BI)."""
    if not isinstance(wert, str):
        return wert
    wert = " ".join(wert.split())
    return wert or None


def fristart_waehlen(angebot, teilnahme):
    """Welche Frist zählt: Angebotsfrist vor Frist für den Teilnahmeantrag. Gibt (Frist, Fristart)."""
    if not leer(angebot):
        return angebot, "Angebot"
    if not leer(teilnahme):
        return teilnahme, "Teilnahmeantrag"
    return None, "keine Angabe"
