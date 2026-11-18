"""Tests für agent/netz.py mit einem kleinen Server auf dem eigenen Rechner (kein Internet nötig)."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from agent.netz import NetzFehler, abrufen, json_abrufen


class Antworten(BaseHTTPRequestHandler):
    aufrufe = 0

    def log_message(self, *args):
        pass

    def antworten(self, code, inhalt):
        self.send_response(code)
        self.end_headers()
        self.wfile.write(inhalt)

    def do_GET(self):
        type(self).aufrufe += 1
        if self.path.startswith("/datei"):
            self.antworten(200, f"{self.path}|{self.headers['User-Agent']}".encode())
        elif self.path == "/fehlt":
            self.antworten(404, b"nicht da")
        else:
            self.antworten(503, b"")

    def do_POST(self):
        laenge = int(self.headers["Content-Length"])
        anfrage = json.loads(self.rfile.read(laenge))
        self.antworten(200, json.dumps({"echo": anfrage, "typ": self.headers["Content-Type"]}).encode())


@pytest.fixture
def server():
    Antworten.aufrufe = 0
    s = HTTPServer(("127.0.0.1", 0), Antworten)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}"
    s.shutdown()


def test_get_mit_parametern(server):
    inhalt = abrufen(f"{server}/datei", parameter={"pubMonth": "2026-10", "format": "csv.zip"}).decode()
    assert inhalt == "/datei?pubMonth=2026-10&format=csv.zip|ZUFALL-Ausschreibungsagent"


def test_post_mit_json(server):
    antwort = json_abrufen(server, json_daten={"query": "a AND b", "limit": 250})
    assert antwort == {"echo": {"query": "a AND b", "limit": 250}, "typ": "application/json"}


def test_fehler_in_anfrage_ohne_wiederholung(server):
    with pytest.raises(NetzFehler, match="HTTP 404.*nicht da"):
        abrufen(f"{server}/fehlt", versuche=3, pause=0)
    assert Antworten.aufrufe == 1


def test_serverfehler_wird_wiederholt(server):
    with pytest.raises(NetzFehler, match="HTTP 503"):
        abrufen(f"{server}/kaputt", versuche=3, pause=0)
    assert Antworten.aufrufe == 3


def test_nicht_erreichbar():
    with pytest.raises(NetzFehler, match="nicht erreichbar"):
        abrufen("http://127.0.0.1:1/", timeout=2)
