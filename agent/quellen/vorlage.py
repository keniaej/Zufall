"""VORLAGE für eine neue Quelle (wird nicht ausgeführt)

So fügt ihr ein neues Ausschreibungsportal hinzu:
1. Diese Datei kopieren und umbenennen, z. B. in `service_bund.py`.
2. Klasse umbenennen (z. B. ServiceBundQuelle), `name` setzen, `abrufen` und `umwandeln` ausfüllen.
3. Die Klasse in agent/quellen/__init__.py in QUELLEN_KLASSEN eintragen.

Alles andere (Dubletten, Prüfungen, Excel mit eigenem Blatt) funktioniert dann automatisch,
solange `umwandeln` genau die Spalten aus agent/modell.py (SPALTEN) liefert.
Braucht das Portal einen API-Key, kommt er in die `.env`-Datei (siehe `.env.example`).

Zur Verfügung stehen:
    self.kriterien      z. B. self.kriterien.cpv_codes, self.kriterien.ausschluss_codes
    self.einstellungen  z. B. self.einstellungen.seit_datum, self.einstellungen.laender
"""
import pandas as pd

from agent.modell import SPALTEN
from agent.quellen.basis import Quelle


class VorlageQuelle(Quelle):
    name = "Vorlage"

    def abrufen(self):
        """Holt die Rohdaten vom Portal, egal in welcher Form (JSON, CSV, XML ...)."""
        raise NotImplementedError("Noch nicht gebaut")

    def umwandeln(self, roh):
        """Übersetzt die Rohdaten in das gemeinsame Format (eine Zeile pro Bekanntmachung)."""
        zeilen = []
        # for eintrag in roh:
        #     zeilen.append({"Ausschreibungs ID Platform": ..., "Titel": ..., "Plattform": self.name, ...})
        return pd.DataFrame(zeilen, columns=SPALTEN)
