"""Quelle: öffentlichevergabe.de (Bekanntmachungsservice des Bundes)

Braucht keinen API-Key. Es gibt keine Suche, nur Gesamtexporte pro Monat oder Tag:
1. Monats-CSV laden und selbst filtern (CPV, Land, Art)
2. Für die Treffer die eForms-XML aus dem Monatsexport laden (Frist, E-Mail, Straße, Link)
"""
import io
import time
import xml.etree.ElementTree as ET
import zipfile

import pandas as pd
import requests

from agent.kriterien import cpv_passt
from agent.modell import SPALTEN
from agent.quellen.basis import Quelle
from agent.werte import datum, fristart_waehlen, land, laufzeit, vergabeart


def version_nr(version):
    """'01' und '1' sind dieselbe Version (CSV und XML-Dateinamen schreiben sie unterschiedlich)."""
    try:
        return int(str(version))
    except ValueError:
        return str(version)


def xml_dateien_je_bekanntmachung(namen):
    """Dateinamen im eForms-ZIP: '<noticeIdentifier>-<Version>.xml' -> {(ID, Version): Dateiname}"""
    dateien = {}
    for name in namen:
        if not name.endswith(".xml"):
            continue
        basis = name.rsplit("/", 1)[-1][:-4]
        nid, _, version = basis.rpartition("-")
        dateien[(nid, version_nr(version))] = name
    return dateien


def xml_auslesen(xml_inhalt):
    """Holt Frist, Link, E-Mail und Straße des Auftraggebers aus einer eForms-XML-Datei.
    {*} heißt: Namensraum egal. eForms verwendet mehrere Namensräume (cbc, cac, efac ...)."""
    wurzel = ET.fromstring(xml_inhalt)

    def fruehestes_datum(pfad):
        werte = [e.text for e in wurzel.findall(pfad) if e.text]
        return min(werte) if werte else None   # mehrere Lose -> früheste Frist zählt

    link = wurzel.find(".//{*}CallForTendersDocumentReference//{*}URI")

    # Auftraggeber: ContractingParty verweist auf eine Organisation (z. B. ORG-0001),
    # deren Adresse und E-Mail stehen unter efac:Organization/efac:Company
    kaeufer_id = wurzel.findtext(".//{*}ContractingParty/{*}Party/{*}PartyIdentification/{*}ID")
    kaeufer = None
    for firma in wurzel.findall(".//{*}Organization/{*}Company"):
        if firma.findtext("{*}PartyIdentification/{*}ID") == kaeufer_id:
            kaeufer = firma
            break

    def kaeufer_feld(pfad):
        return kaeufer.findtext(pfad) if kaeufer is not None else None

    return {
        "email": kaeufer_feld("{*}Contact/{*}ElectronicMail"),
        "strasse": kaeufer_feld("{*}PostalAddress/{*}StreetName"),
        "angebot": fruehestes_datum(".//{*}TenderSubmissionDeadlinePeriod/{*}EndDate"),
        "teilnahme": fruehestes_datum(".//{*}ParticipationRequestReceptionPeriod/{*}EndDate"),
        "link": link.text if link is not None else None,
    }


class OeffentlicheVergabeQuelle(Quelle):
    name = "oeffentlichevergabe.de"

    URL = "https://oeffentlichevergabe.de/api/notice-exports"
    SCHLUESSEL = ["noticeIdentifier", "noticeVersion"]   # verbindet alle CSV-Tabellen

    # ------------------------------------------------------------------ Abruf

    def abrufen(self):
        """1. Monats-CSVs laden und filtern  2. Für die Treffer die XML laden und Details ergänzen."""
        teile = []
        for monat in self.monate():
            teil = self.treffer_aus_csv(self.download({"pubMonth": monat, "format": "csv.zip"}))
            print(f"  {self.name} {monat}: {len(teil)} Treffer im CSV")
            teile.append(teil)
        treffer = pd.concat(teile, ignore_index=True)
        treffer["tag"] = treffer["publicationDate"].str[:10]
        treffer = treffer[treffer["tag"] >= pd.Timestamp(self.einstellungen.seit_datum).strftime("%Y-%m-%d")]
        return self.details_ergaenzen(treffer)

    def download(self, parameter):
        """Lädt ein ZIP. Bis zu 3 Versuche, die Seite bricht gelegentlich ab."""
        for versuch in range(3):
            try:
                antwort = requests.get(self.URL, params=parameter, timeout=600)   # Monats-ZIPs: bis ca. 100 MB
                antwort.raise_for_status()
                return zipfile.ZipFile(io.BytesIO(antwort.content))
            except requests.RequestException:
                if versuch == 2:
                    raise
                time.sleep(10)

    def monate(self):
        """Alle Monate vom Startdatum bis heute, z. B. ['2026-08', '2026-09', ...]."""
        return [p.strftime("%Y-%m") for p in
                pd.period_range(pd.Timestamp(self.einstellungen.seit_datum), pd.Timestamp.today(), freq="M")]

    @staticmethod
    def csv_lesen(zip_datei, name):
        """Liest eine der 19 CSV-Tabellen aus dem ZIP (z. B. 'notice', 'classification')."""
        datei = [d for d in zip_datei.namelist() if d.endswith(name + ".csv")][0]
        return pd.read_csv(zip_datei.open(datei), dtype=str)

    def treffer_aus_csv(self, zip_datei):
        """Führt die benötigten CSV-Tabellen zusammen und filtert grob vor.
        Ziel: möglichst wenige Bekanntmachungen im XML-Schritt."""
        schluessel = self.SCHLUESSEL

        # Bekanntmachungen: nur die Arten, die wir wollen
        notice = self.csv_lesen(zip_datei, "notice")
        notice = notice[notice["noticeType"].isin(self.einstellungen.notice_typen)]

        # CPV-Codes: Hauptcode + Zusatzcodes aller Lose einsammeln
        klass = self.csv_lesen(zip_datei, "classification")
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
        org = self.csv_lesen(zip_datei, "organisation")
        org = (org[org["organisationRole"] == "buyer"]
               .groupby(schluessel)[["organisationName", "organisationCity", "organisationPostCode",
                                     "organisationCountryCode"]].first())

        # Verfahrensart (open, restricted ...)
        verfahren = self.csv_lesen(zip_datei, "procedure").groupby(schluessel)["procedureType"].first()

        # Vertragslaufzeit pro Los -> Monate, frühester Beginn, spätestes Ende (siehe werte.laufzeit)
        dauer = self.csv_lesen(zip_datei, "duration")
        dauer = pd.DataFrame(
            [(*schl, *laufzeit(d["durationPeriod"].tolist(), d["durationPeriodUnit"].tolist(),
                               d["durationStartDate"].tolist(), d["durationEndDate"].tolist()))
             for schl, d in dauer.groupby(schluessel)],
            columns=schluessel + ["dauer_monate", "vertragsbeginn", "vertragsende"],
        ).set_index(schluessel)

        # Titel: Zeile ohne Los = Titel des ganzen Verfahrens
        zweck = self.csv_lesen(zip_datei, "purpose")
        titel = zweck[zweck["lotIdentifier"].isna()].groupby(schluessel)["title"].first()

        # Leistungsort, alle NUTS-Codes über alle Lose
        ort = self.csv_lesen(zip_datei, "placeOfPerformance")
        nuts = (ort.dropna(subset=["placePerformanceCountrySubdivision"])
                .groupby(schluessel)["placePerformanceCountrySubdivision"]
                .apply(lambda s: ", ".join(sorted(set(s)))).rename("nuts"))

        treffer = (notice.set_index(schluessel)
                   .join(alle_cpv).join(haupt_cpv).join(org).join(titel).join(nuts)
                   .join(verfahren).join(dauer)
                   .reset_index())
        if treffer.empty:
            return treffer
        return treffer[treffer.apply(self.passt_grob, axis=1)]

    def passt_grob(self, zeile):
        """Grobfilter: Land, ZUFALL-CPV irgendwo, Hauptcode nicht ausgeschlossen.
        (Bekanntmachungen ohne CPV-Code fallen hier raus, siehe offene Frage an ZUFALL)"""
        codes = zeile["alle_cpv"] if isinstance(zeile["alle_cpv"], list) else []
        if zeile["organisationCountryCode"] not in self.einstellungen.laender:
            return False
        if any(cpv_passt(zeile["haupt_cpv"], p) for p in self.kriterien.ausschluss_codes):
            return False
        return any(cpv_passt(c, z) for c in codes for z in self.kriterien.cpv_codes)

    def details_ergaenzen(self, treffer):
        """Details aus dem XML, ein Download pro MONAT.
        Der Tagesexport (pubDay) liefert höchstens 1.000 XML-Dateien, an vollen Tagen fehlen also welche
        (getestet 14.11.2026: 05.11. hatte 1.170 Bekanntmachungen, aber nur 1.000 XML-Dateien).
        Der Monatsexport ist vollständig und braucht weniger Downloads."""
        details = {}
        monate = sorted(treffer["tag"].str[:7].unique())
        print(f"  {self.name}: lade XML für {len(monate)} Monate ...")
        for monat in monate:
            zip_datei = self.download({"pubMonth": monat, "format": "eforms.zip"})
            dateien = xml_dateien_je_bekanntmachung(zip_datei.namelist())
            for _, t in treffer[treffer["tag"].str[:7] == monat].iterrows():
                datei = dateien.get((t["noticeIdentifier"], version_nr(t["noticeVersion"])))
                if datei:
                    details[(t["noticeIdentifier"], t["noticeVersion"])] = xml_auslesen(zip_datei.read(datei))

        schluessel = list(zip(treffer["noticeIdentifier"], treffer["noticeVersion"]))
        treffer["details"] = [details.get(k) for k in schluessel]
        fehlend = sum(k not in details for k in schluessel)
        if fehlend:
            print(f"  WARNUNG {self.name}: für {fehlend} Bekanntmachungen keine XML gefunden "
                  f"(Frist, E-Mail, Straße, Link fehlen dort)")
        return treffer

    # ------------------------------------------------------------------ Umwandeln

    def umwandeln(self, roh):
        return pd.DataFrame([self.zeile(t) for _, t in roh.iterrows()], columns=SPALTEN)

    def zeile(self, t):
        """Ein Treffer (CSV + XML-Details) -> eine Zeile im gemeinsamen Format."""
        d = t["details"] if isinstance(t["details"], dict) else {}
        frist, fristart = fristart_waehlen(d.get("angebot"), d.get("teilnahme"))
        if not d:
            fristart = "unbekannt (XML fehlt im Export)"

        return {
            "Ausschreibungs ID Platform": f"{t['noticeIdentifier']}-{t['noticeVersion']}",
            "Verfahrens ID": t["procedureIdentifier"],
            "Publikation": datum(t["publicationDate"]),
            "Art": t["noticeType"],
            "Titel": t["title"],
            "Vergabe Branchen Code": t["haupt_cpv"],
            "Alle CPV": ", ".join(t["alle_cpv"]) if isinstance(t["alle_cpv"], list) else "",
            "Auftraggeber": t["organisationName"],
            "Email": d.get("email"),
            "Stadt": t["organisationCity"],
            "Straße": d.get("strasse"),
            "PLZ": t["organisationPostCode"],
            "Land": land(t["organisationCountryCode"]),
            "Vergabeart": vergabeart(t["procedureType"]),
            "Vertragsdauer in Monaten": t["dauer_monate"],
            "Vertragsbeginn": t["vertragsbeginn"],
            "Vertragsende": t["vertragsende"],
            "Leistungsort NUTS": t["nuts"] if isinstance(t["nuts"], str) else "",
            "Angebotsfrist": datum(frist),
            "Fristart": fristart,
            "Plattform": self.name,
            "Link zur Plattform": d.get("link"),   # zeigt auf die Ursprungsplattform (dtvp, evergabe ...)
        }
