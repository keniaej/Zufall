"""Quelle: öffentlichevergabe.de (Bekanntmachungsservice des Bundes)

Braucht keinen API-Key. Liefert Monats-ZIPs mit CSV-Tabellen und Tages-ZIPs mit eForms-XML.
"""
import io
import time
import xml.etree.ElementTree as ET
import zipfile

import pandas as pd
import requests

from agent.format import SPALTEN, cpv_passt, datum
from agent.konfiguration import CPV_CODES, LAENDER, NOTICE_TYPEN, PERSONENVERKEHR, SEIT_DATUM

OEV_URL = "https://oeffentlichevergabe.de/api/notice-exports"


def oev_download(parameter):
    """Lädt ein ZIP von öffentlichevergabe.de. Bis zu 3 Versuche, die Seite bricht gelegentlich ab."""
    for versuch in range(3):
        try:
            antwort = requests.get(OEV_URL, params=parameter, timeout=180)
            antwort.raise_for_status()
            return zipfile.ZipFile(io.BytesIO(antwort.content))
        except requests.RequestException:
            if versuch == 2:
                raise
            time.sleep(10)


def oev_csv_lesen(zip_datei, name):
    """Liest eine der 19 CSV-Tabellen aus dem ZIP (z. B. 'notice', 'classification')."""
    datei = [d for d in zip_datei.namelist() if d.endswith(name + ".csv")][0]
    return pd.read_csv(zip_datei.open(datei), dtype=str)


def oev_treffer_aus_csv(zip_datei):
    """Führt die benötigten CSV-Tabellen zusammen und filtert grob vor.
    Ziel: möglichst wenige XML-Downloads im nächsten Schritt."""
    schluessel = ["noticeIdentifier", "noticeVersion"]   # verbindet alle Tabellen

    # Bekanntmachungen: nur die Arten, die wir wollen
    notice = oev_csv_lesen(zip_datei, "notice")
    notice = notice[notice["noticeType"].isin(NOTICE_TYPEN)]

    # CPV-Codes: Hauptcode + Zusatzcodes aller Lose einsammeln
    klass = oev_csv_lesen(zip_datei, "classification")
    klass = klass[klass["classificationType"] == "cpv"].copy()
    klass["codes"] = klass["mainClassificationCode"].fillna("") + "," + klass["additionalClassificationCodes"].fillna("")
    alle_cpv = (klass.groupby(schluessel)["codes"]
                .apply(lambda s: sorted({c.strip() for text in s for c in text.split(",") if c.strip()}))
                .rename("alle_cpv"))
    # Hauptcode = Zeile ohne Los (gilt fürs ganze Verfahren), sonst erste Zeile
    klass["ohne_los"] = klass["lotIdentifier"].isna()
    haupt_cpv = (klass.sort_values("ohne_los", ascending=False)
                 .groupby(schluessel)["mainClassificationCode"].first().rename("haupt_cpv"))

    # Auftraggeber: erste Organisation mit Rolle "buyer"
    org = oev_csv_lesen(zip_datei, "organisation")
    org = (org[org["organisationRole"] == "buyer"]
           .groupby(schluessel)[["organisationName", "organisationCity", "organisationCountryCode"]].first())

    # Titel: Zeile ohne Los = Titel des ganzen Verfahrens
    zweck = oev_csv_lesen(zip_datei, "purpose")
    titel = zweck[zweck["lotIdentifier"].isna()].groupby(schluessel)["title"].first()

    # Leistungsort, alle NUTS-Codes über alle Lose
    ort = oev_csv_lesen(zip_datei, "placeOfPerformance")
    nuts = (ort.dropna(subset=["placePerformanceCountrySubdivision"])
            .groupby(schluessel)["placePerformanceCountrySubdivision"]
            .apply(lambda s: ", ".join(sorted(set(s)))).rename("nuts"))

    treffer = (notice.set_index(schluessel)
               .join(alle_cpv).join(haupt_cpv).join(org).join(titel).join(nuts)
               .reset_index())

    # Grobfilter: Land, ZUFALL-CPV irgendwo, kein Personenverkehr als Hauptcode
    # (Bekanntmachungen ohne CPV-Code fallen hier raus, siehe offene Frage an ZUFALL)
    def passt(zeile):
        codes = zeile["alle_cpv"] if isinstance(zeile["alle_cpv"], list) else []
        if zeile["organisationCountryCode"] not in LAENDER:
            return False
        if any(cpv_passt(zeile["haupt_cpv"], p) for p in PERSONENVERKEHR):
            return False
        return any(cpv_passt(c, z) for c in codes for z in CPV_CODES)

    if treffer.empty:
        return treffer
    return treffer[treffer.apply(passt, axis=1)]


def oev_xml_auslesen(xml_inhalt):
    """Holt Frist und Link aus einer eForms-XML-Datei.
    {*} heißt: Namensraum egal. eForms verwendet mehrere Namensräume (cbc, cac, efac ...)."""
    wurzel = ET.fromstring(xml_inhalt)

    def fruehestes_datum(pfad):
        werte = [e.text for e in wurzel.findall(pfad) if e.text]
        return min(werte) if werte else None   # mehrere Lose -> früheste Frist zählt

    link = wurzel.find(".//{*}CallForTendersDocumentReference//{*}URI")
    return {
        "angebot": fruehestes_datum(".//{*}TenderSubmissionDeadlinePeriod/{*}EndDate"),
        "teilnahme": fruehestes_datum(".//{*}ParticipationRequestReceptionPeriod/{*}EndDate"),
        "link": link.text if link is not None else None,
    }


def oev_monate():
    """Alle Monate von SEIT_DATUM bis heute, z. B. ['2026-08', '2026-09', ...]."""
    return [p.strftime("%Y-%m") for p in pd.period_range(pd.Timestamp(SEIT_DATUM), pd.Timestamp.today(), freq="M")]


def oev_abrufen():
    """1. Monats-CSVs laden und filtern  2. Für Treffer-Tage das XML laden und Details ergänzen."""
    # Schritt 1: Treffer aus den Monats-CSVs
    teile = []
    for monat in oev_monate():
        teil = oev_treffer_aus_csv(oev_download({"pubMonth": monat, "format": "csv.zip"}))
        print(f"  öffentlichevergabe.de {monat}: {len(teil)} Treffer im CSV")
        teile.append(teil)
    treffer = pd.concat(teile, ignore_index=True)
    treffer["tag"] = treffer["publicationDate"].str[:10]
    treffer = treffer[treffer["tag"] >= pd.Timestamp(SEIT_DATUM).strftime("%Y-%m-%d")]

    # Schritt 2: Details aus dem XML, ein Download pro Veröffentlichungstag
    details = {}
    tage = sorted(treffer["tag"].unique())
    print(f"  öffentlichevergabe.de: lade XML für {len(tage)} Tage ...")
    for tag in tage:
        zip_datei = oev_download({"pubDay": tag, "format": "eforms.zip"})
        dateien = zip_datei.namelist()
        for nid in treffer.loc[treffer["tag"] == tag, "noticeIdentifier"]:
            passend = [d for d in dateien if d.startswith(nid)]
            if passend:
                details[nid] = oev_xml_auslesen(zip_datei.read(passend[-1]))

    treffer["details"] = treffer["noticeIdentifier"].map(details)
    return treffer


def oev_umwandeln(treffer):
    """Übersetzt die öffentlichevergabe.de-Treffer in das gemeinsame Format."""
    zeilen = []
    for _, t in treffer.iterrows():
        d = t["details"] if isinstance(t["details"], dict) else {}

        if d.get("angebot"):
            frist, fristart = d["angebot"], "Angebot"
        elif d.get("teilnahme"):
            frist, fristart = d["teilnahme"], "Teilnahmeantrag"
        else:
            frist, fristart = None, "keine Angabe"

        zeilen.append({
            "Ausschreibungs ID Platform": f"{t['noticeIdentifier']}-{t['noticeVersion']}",
            "Verfahrens ID": t["procedureIdentifier"],
            "Publikation": datum(t["publicationDate"]),
            "Art": t["noticeType"],
            "Titel": t["title"],
            "Vergabe Branchen Code": t["haupt_cpv"],
            "Alle CPV": ", ".join(t["alle_cpv"]) if isinstance(t["alle_cpv"], list) else "",
            "Auftraggeber": t["organisationName"],
            "Stadt": t["organisationCity"],
            "Leistungsort NUTS": t["nuts"] if isinstance(t["nuts"], str) else "",
            "Angebotsfrist": datum(frist),
            "Fristart": fristart,
            "Plattform": "oeffentlichevergabe.de",
            "Link zur Plattform": d.get("link"),   # zeigt auf die Ursprungsplattform (dtvp, evergabe ...)
        })
    return pd.DataFrame(zeilen, columns=SPALTEN)
