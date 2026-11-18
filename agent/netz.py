"""Abrufe aus dem Internet, nur mit der Python-Standardbibliothek (urllib), ohne Zusatzpaket.

    daten = json_abrufen(url, json_daten={...})                 # POST mit JSON, Antwort als dict
    inhalt = abrufen(url, parameter={"pubMonth": "2026-10"})    # GET, Antwort als Bytes

Unter Windows nutzt urllib die Zertifikate und Proxy-Einstellungen von Windows. Das ist in
Firmennetzen oft zuverlässiger als die eigene Zertifikatsliste von Paketen wie requests.
"""
import http.client
import json
import time
import urllib.error
import urllib.parse
import urllib.request

# Allgemeiner Name statt "Python-urllib", den manche Server abweisen
KENNUNG = "ZUFALL-Ausschreibungsagent"


class NetzFehler(ConnectionError):
    """Abruf fehlgeschlagen. Die Meldung sagt, welche Adresse und warum."""


def abrufen(url, parameter=None, json_daten=None, timeout=60, versuche=1, pause=10):
    """Lädt eine Adresse und gibt den Inhalt als Bytes zurück.

    parameter   werden an die Adresse gehängt (?pubMonth=2026-10&format=csv.zip)
    json_daten  wenn angegeben: POST mit diesem Inhalt als JSON, sonst GET
    versuche    so oft wird es bei Verbindungs- oder Serverfehlern probiert, mit `pause` Sekunden dazwischen
    """
    if parameter:
        url = f"{url}?{urllib.parse.urlencode(parameter)}"
    kopf = {"User-Agent": KENNUNG}
    daten = None
    if json_daten is not None:
        daten = json.dumps(json_daten).encode("utf-8")
        kopf.update({"Content-Type": "application/json", "Accept": "application/json"})
    anfrage = urllib.request.Request(url, data=daten, headers=kopf)

    for versuch in range(1, versuche + 1):
        try:
            with urllib.request.urlopen(anfrage, timeout=timeout) as antwort:
                return antwort.read()
        except urllib.error.HTTPError as f:
            text = f.read()[:300].decode("utf-8", "replace").strip()
            fehler = NetzFehler(f"{url}: HTTP {f.code} {f.reason}" + (f" ({text})" if text else ""))
            if f.code < 500 and f.code != 429:   # Fehler in der Anfrage: nochmal versuchen bringt nichts
                raise fehler from None
        except (urllib.error.URLError, http.client.HTTPException, OSError) as f:
            fehler = NetzFehler(f"{url} nicht erreichbar: {getattr(f, 'reason', f)}")
        if versuch < versuche:
            time.sleep(pause)
    raise fehler


def json_abrufen(url, **optionen):
    """Wie abrufen(), Antwort als JSON gelesen."""
    return json.loads(abrufen(url, **optionen))
