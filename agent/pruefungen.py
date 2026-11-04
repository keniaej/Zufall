"""TEIL 4: PRÜFUNGEN

Gelten für alle Quellen gleich. Jede Prüfung gibt zwei Tabellen zurück: (behalten, aussortiert).
Aussortiertes bekommt einen Grund, damit die Regeln später im Excel nachvollziehbar sind.
"""
import pandas as pd

from agent.format import cpv_passt
from agent.konfiguration import (AUSSCHLUSS_WOERTER, PERSONENVERKEHR, PRODUKTE,
                                 REGION_KREISE, REGION_PRODUKTE)


def produkte_ermitteln(codes):
    """Ordnet CPV-Codes ZUFALL-Produkten zu. Pro Code zählt der GENAUESTE passende
    ZUFALL-Code. Sonst fiele 60160000 (Post auf der Straße, NSE) auch unter
    60100000 (Straßentransport, Landverkehr), weil es im CPV-Baum darunter liegt."""
    produkte = set()
    for code in codes:
        kandidaten = [(len(ziel.rstrip("0")), produkt)
                      for produkt, ziele in PRODUKTE.items()
                      for ziel in ziele if cpv_passt(code, ziel)]
        if kandidaten:
            produkte.add(max(kandidaten)[1])   # längster Präfix = genauester Code
    return sorted(produkte)


def cpv_pruefen(tabelle):
    """Ordnet das ZUFALL-Produkt zu und sortiert aus: kein ZUFALL-Code
    oder Personenverkehr als Hauptcode."""
    gruende, produkte = [], []
    for _, zeile in tabelle.iterrows():
        codes = [c.strip() for c in str(zeile["Alle CPV"]).split(",") if c.strip()]
        haupt = zeile["Vergabe Branchen Code"]
        gefunden = produkte_ermitteln(codes)
        produkte.append(", ".join(gefunden))

        if any(cpv_passt(haupt, p) for p in PERSONENVERKEHR):
            gruende.append("Personenverkehr (Hauptcode)")
        elif not gefunden:
            gruende.append("kein ZUFALL-CPV-Code")
        else:
            gruende.append(None)

    tabelle = tabelle.copy()
    tabelle["Zufall Produkt"] = produkte
    return aufteilen(tabelle, gruende)


def region_pruefen(tabelle):
    """Regional begrenzte Produkte (Landverkehr) nur im Gebiet der Standorte.
    Fliegt nur raus, wenn ALLE Produkte regional begrenzt sind. Landverkehr + Kontraktlogistik
    bleibt also drin, weil Kontraktlogistik keine örtliche Eingrenzung hat."""
    gruende, region = [], []
    for _, zeile in tabelle.iterrows():
        produkte = [p.strip() for p in zeile["Zufall Produkt"].split(",") if p.strip()]
        if not any(p in REGION_PRODUKTE for p in produkte):
            region.append("")
            gruende.append(None)
            continue

        nuts = [c.strip() for c in str(zeile["Leistungsort NUTS"]).split(",") if c.strip()]
        kreise = [c for c in nuts if len(c) == 5]          # NUTS-3 = Landkreis = 5 Zeichen
        im_gebiet = [REGION_KREISE[c] for c in kreise if c in REGION_KREISE]
        nur_regional = all(p in REGION_PRODUKTE for p in produkte)

        if im_gebiet:
            region.append("ja: " + ", ".join(im_gebiet))
            gruende.append(None)
        elif not kreise:
            region.append("unklar (kein Landkreis angegeben)")   # lieber drin lassen
            gruende.append(None)
        else:
            region.append("nein: " + ", ".join(kreise))
            gruende.append("Landverkehr außerhalb der Region" if nur_regional else None)

    tabelle = tabelle.copy()
    tabelle["Region Landverkehr"] = region
    return aufteilen(tabelle, gruende)


def nur_offene_fristen(tabelle):
    """Frist ab heute oder keine Frist angegeben."""
    heute = pd.Timestamp.today().normalize()
    abgelaufen = tabelle["Angebotsfrist"] < heute
    gruende = ["Frist abgelaufen" if a else None for a in abgelaufen]
    return aufteilen(tabelle, gruende)


def schlagwoerter_pruefen(tabelle):
    muster = r"\b(?:" + "|".join(AUSSCHLUSS_WOERTER) + ")"
    treffer = tabelle["Titel"].str.extract(f"({muster})", flags=2)[0]  # flags=2: Groß/klein egal
    gruende = [f"Schlagwort im Titel: {w.lower()}" if isinstance(w, str) else None for w in treffer]
    return aufteilen(tabelle, gruende)


def aufteilen(tabelle, gruende):
    """Hilfsfunktion: trennt Zeilen mit Grund (aussortiert) von Zeilen ohne (behalten)."""
    tabelle = tabelle.copy()
    tabelle["Ausschlussgrund"] = gruende
    raus = tabelle["Ausschlussgrund"].notna()
    behalten = tabelle[~raus].drop(columns="Ausschlussgrund")
    return behalten, tabelle[raus]


def dubletten_entfernen(tabelle):
    """Pro Verfahren nur die neueste Bekanntmachung behalten, auch über Quellen hinweg.
    Die Verfahrens-ID ist bei TED und öffentlichevergabe.de identisch (getestet 03.11.2026)."""
    tabelle = tabelle.copy()
    # Ohne Verfahrens-ID würden sonst alle leeren Zeilen als eine Dublette gelten
    tabelle["Verfahrens ID"] = tabelle["Verfahrens ID"].fillna(tabelle["Ausschreibungs ID Platform"])

    # Festhalten, auf welchen Plattformen ein Verfahren gefunden wurde
    plattformen = tabelle.groupby("Verfahrens ID")["Plattform"].agg(lambda s: ", ".join(sorted(set(s))))
    tabelle["Gefunden auf"] = tabelle["Verfahrens ID"].map(plattformen)

    tabelle = tabelle.sort_values("Publikation")
    return tabelle.drop_duplicates(subset="Verfahrens ID", keep="last")


# Reihenfolge der Prüfungen. Neue Prüfung = Funktion schreiben + hier eintragen.
PRUEFUNGEN = [cpv_pruefen, region_pruefen, nur_offene_fristen, schlagwoerter_pruefen]
