"""Kleine Helfer für openpyxl: Werte in Zellen schreiben, als Tabelle formatieren, Breiten, Links."""
import re

import pandas as pd
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

DATUMS_SPALTEN = {"Publikation", "Angebotsfrist", "Vertragsbeginn", "Vertragsende",
                  "Erstmals gefunden am", "Zuletzt aktualisiert am"}
LINK_SPALTEN = {"Link zur Plattform"}
MAIL_SPALTEN = {"Email"}


def zellwert(wert):
    """pandas-Werte in etwas umwandeln, das openpyxl in eine Zelle schreiben kann."""
    if wert is None:
        return None
    if isinstance(wert, (list, dict)):
        return str(wert)
    try:
        if pd.isna(wert):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(wert, pd.Timestamp):
        return wert.to_pydatetime()
    if hasattr(wert, "item"):            # numpy-Zahlen
        wert = wert.item()
    if isinstance(wert, float) and wert.is_integer():
        return int(wert)
    return wert


def blattname(name):
    """Excel erlaubt max. 31 Zeichen und keine der Zeichen []:*?/\\ im Blattnamen."""
    return re.sub(r"[\[\]:*?/\\]", "_", name)[:31]


def tabellenname(blatt):
    """Name der Excel-Tabelle (wie bei Strg+T). Power BI zeigt die Tabellen unter diesem Namen an.
    Erlaubt sind nur Buchstaben, Ziffern und _, am Anfang ein Buchstabe."""
    for alt, neu in [("Ü", "Ue"), ("ü", "ue"), ("Ö", "Oe"), ("ö", "oe"), ("Ä", "Ae"), ("ä", "ae"), ("ß", "ss")]:
        blatt = blatt.replace(alt, neu)
    name = re.sub(r"[^A-Za-z0-9_]", "_", blatt)
    return name if name[:1].isalpha() else "T_" + name


def letzte_datenzeile(ws):
    """Letzte Zeile mit Inhalt. ws.max_row zählt auch leere, nur formatierte Zeilen mit
    (z. B. wenn ZUFALL eine ganze Spalte eingefärbt hat). Neue Zeilen kämen sonst mit Lücke darunter."""
    for zeile_nr in range(ws.max_row, 1, -1):
        if any(c.value not in (None, "") for c in ws[zeile_nr]):
            return zeile_nr
    return 1


def als_tabelle(ws):
    """Formatiert den ganzen Bereich als Excel-Tabelle. Eine vorhandene Tabelle wird ersetzt,
    damit sie neue Zeilen und Spalten mit umfasst. Ohne Datenzeile braucht Excel trotzdem
    eine (leere) Zeile unter der Überschrift, sonst gilt die Datei als beschädigt."""
    stil = "TableStyleMedium2"
    for name in list(ws.tables):
        alt = ws.tables[name]
        if alt.tableStyleInfo is not None and alt.tableStyleInfo.name:
            stil = alt.tableStyleInfo.name      # Stil behalten, falls ZUFALL ihn geändert hat
        del ws.tables[name]
    ws.auto_filter.ref = None

    # Eine Tabelle braucht eindeutige, nicht leere Überschriften
    gesehen = set()
    for zelle in ws[1]:
        text = str(zelle.value).strip() if zelle.value is not None else ""
        if not text or text in gesehen:
            text = f"{text or 'Spalte'} {zelle.column}"
        zelle.value = text
        gesehen.add(text)

    letzte_zeile = max(letzte_datenzeile(ws), 2)
    tabelle = Table(displayName=tabellenname(ws.title), ref=f"A1:{get_column_letter(ws.max_column)}{letzte_zeile}")
    tabelle.tableStyleInfo = TableStyleInfo(name=stil, showRowStripes=True)
    ws.add_table(tabelle)


def zelle_formatieren(zelle, spalte, neu_angelegt):
    """Datum, Link, E-Mail. Die Link-Formatvorlage nur bei neuen Zeilen setzen, sonst würde
    eine Farbe, die ZUFALL der Zelle gegeben hat, überschrieben."""
    if spalte in DATUMS_SPALTEN:
        zelle.number_format = "DD.MM.YYYY"
    if spalte in LINK_SPALTEN or spalte in MAIL_SPALTEN:
        if isinstance(zelle.value, str) and zelle.value:
            zelle.hyperlink = ("mailto:" + zelle.value) if spalte in MAIL_SPALTEN else zelle.value
            if neu_angelegt:
                zelle.style = "Hyperlink"
        else:
            zelle.hyperlink = None


def spaltenbreite(ws, spalte_nr, ueberschrift):
    werte = [len(str(z[0].value)) for z in ws.iter_rows(min_row=2, min_col=spalte_nr, max_col=spalte_nr)
             if z[0].value is not None]
    ws.column_dimensions[get_column_letter(spalte_nr)].width = min(max([len(ueberschrift)] + werte) + 2, 60)
