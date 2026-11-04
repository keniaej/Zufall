# Agent Öffentliche Ausschreibungen (ZUFALL logistics group)

Projekt WS 2026/27: Ein KI-Agent, der öffentliche Transport- und Lagerausschreibungen von mehreren Plattformen sammelt, nach ZUFALLs Kriterien qualifiziert und in einem Power-BI-Dashboard darstellt.

Die vollständige Aufgabenstellung steht in [docs/projekt.md](docs/projekt.md), die offenen Punkte in [docs/offene_fragen.md](docs/offene_fragen.md).

## Pipeline und Stand

```
1. Abrufen + Python-Filter    →    2. KI-Filter + Excel    →    3. Power BI
   API-Abruf der Plattformen,        KI bewertet in Python,        Dashboard mit den
   feste Kriterien (CPV, Region,     ob interessant für ZUFALL;    qualifizierten
   Fristen, Schlagwörter)            Ergebnis in Excel             Ausschreibungen
   ✅ größtenteils fertig             🟡 Excel da, KI offen          ⬜ offen
```

| Schritt | Datei | Stand |
|---------|-------|-------|
| Konfiguration (was gesucht wird) | `agent/konfiguration.py` | ✅ fertig, CPV-Codes noch zu prüfen |
| Gemeinsames Format (welche Spalten) | `agent/format.py` | ✅ fertig |
| 1. Abrufen der Plattformen | `agent/quellen/` | 🟡 siehe Plattform-Tabelle |
| 1. Python-Filter und Dubletten | `agent/pruefungen.py` | ✅ fertig, Regeln für Dopplungen noch festlegen |
| 2. KI-Bewertung | `agent/ki_bewertung.py` | ⬜ offen |
| 2. Excel-Export | `agent/excel_export.py` | ✅ eine feste Datei `output/ausschreibungen.xlsx`, wird bei jedem Lauf aktualisiert |
| Automatischer Lauf (einmal im Monat) | `automatisch/` | ✅ Anleitung und Skript für Mac, Anleitung für Windows |
| 3. Power-BI-Dashboard | `dashboard/` | ⬜ offen |
| Ablauf (alles zusammen) | `agent/main.py` | ✅ fertig |

## Plattformen

| Plattform | Datei | Stand |
|-----------|-------|-------|
| TED (EU) | `agent/quellen/ted.py` | ✅ funktioniert |
| öffentlichevergabe.de | `agent/quellen/oeffentlichevergabe.py` | 🟡 gebaut, läuft nur lokal bzw. von deutschem Server (über Google Colab blockiert) |
| Service.Bund | – | ⬜ offen |
| e-Vergabe | – | ⬜ offen |
| NSPA (Nato) | – | ❌ wahrscheinlich nicht machbar, keine öffentliche API |

Neue Plattform anbinden: `agent/quellen/vorlage.py` kopieren und in `agent/quellen/__init__.py` eintragen.

## Ordner und Dateien

Die Spalte **Herkunft** zeigt, woher der Inhalt kommt:
- **Notebook:** unser Code aus `TED_API.ipynb`, nur in eine eigene Datei verschoben
- **neu:** später dazugekommen

### `agent/`: der eigentliche Code

Der Agent wird mit `python -m agent.main` gestartet. `main.py` ruft die anderen Dateien der Reihe nach auf.

| Datei | Was sie macht | Herkunft |
|-------|---------------|----------|
| `konfiguration.py` | **TEIL 1.** Alle Einstellungen: Startdatum, Land, CPV-Codes pro ZUFALL-Produkt, Landkreise für den Landverkehr, Ausschluss-Schlagwörter. Wer etwas an den Kriterien ändern will, ändert es nur hier. | Notebook |
| `format.py` | **TEIL 2.** Legt fest, welche Spalten jede Plattform liefern muss (z. B. Titel, Frist, CPV), damit alle Plattformen gleich weiterverarbeitet werden können. Dazu kleine Hilfsfunktionen, z. B. Datum umwandeln. | Notebook |
| `quellen/ted.py` | **TEIL 3.** Ruft die Ausschreibungen von TED ab und bringt sie ins gemeinsame Format. | Notebook |
| `quellen/oeffentlichevergabe.py` | **TEIL 3.** Ruft die Ausschreibungen von öffentlichevergabe.de ab (CSV- und XML-Dateien) und bringt sie ins gemeinsame Format. | Notebook |
| `quellen/__init__.py` | Liste aller Plattformen, die der Agent abfragt. Neue Plattform = hier eintragen. | Notebook |
| `quellen/vorlage.py` | Leere Vorlage zum Kopieren, wenn eine neue Plattform dazukommt (z. B. Service.Bund). Wird nicht ausgeführt. | neu |
| `pruefungen.py` | **TEIL 4.** Die festen Filter: CPV-Codes, Region, Fristen, Schlagwörter und Dubletten. Alles Aussortierte bekommt einen Grund. | Notebook |
| `ki_bewertung.py` | **Platzhalter** für den KI-Filter. Macht noch nichts, außer die Meldung „noch nicht gebaut“ auszugeben. Hier kommt die KI-Bewertung hin. | neu |
| `excel_export.py` | Schreibt das Ergebnis in `output/ausschreibungen.xlsx` mit den Blättern *Relevant*, *Aussortiert* und *Status*. Überschreibt die Datei bei jedem Lauf. | neu |
| `main.py` | **TEIL 5.** Der Ablauf: Plattformen abrufen → Dubletten → Prüfungen → KI-Bewertung → Excel. | Notebook, am Ende um KI-Bewertung und Excel ergänzt |
| `__init__.py` | Leere Datei. Python braucht sie, damit es den Ordner `agent` als zusammengehörigen Code erkennt. Nicht löschen. | neu |

### Weitere Ordner

| Ordner / Datei | Was es ist | Herkunft |
|----------------|------------|----------|
| `notebooks/TED_API.ipynb` | Unser ursprüngliches Notebook, unverändert (Stand 04.11.2026). Zum Nachschauen und Ausprobieren. Der Agent selbst nutzt es nicht. | Notebook |
| `automatisch/README.md` | Anleitung, wie der Agent einmal im Monat von selbst läuft (Mac und Windows). | neu |
| `automatisch/einrichten_mac.sh` | Schaltet auf dem Mac den monatlichen Lauf ein. Einmal starten mit `bash automatisch/einrichten_mac.sh`. | neu |
| `automatisch/ausschalten_mac.sh` | Schaltet den monatlichen Lauf auf dem Mac wieder aus. | neu |
| `dashboard/README.md` | **Platzhalter** für das Power-BI-Dashboard, mit den Fragen, die wir noch klären müssen. | neu |
| `docs/projekt.md` | Aufgabenstellung und unsere geplante Pipeline. | neu |
| `docs/offene_fragen.md` | Checkliste aller offenen Punkte (Team und Fragen an ZUFALL). | neu |
| `tests/test_pruefungen.py` | Drei kleine Tests, ob die Regeln richtig rechnen (z. B. ob ein Schlagwort aussortiert wird). Starten mit `python -m pytest`. Braucht kein Internet. | neu |
| `output/` | Hier landen `ausschreibungen.xlsx` und `log.txt` (Protokoll des automatischen Laufs). Beides wird **nicht** zu GitHub hochgeladen, es liegt nur auf eurem Rechner. | neu |

### Dateien im Hauptordner

| Datei | Was sie macht |
|-------|---------------|
| `README.md` | Diese Übersicht. |
| `CONTRIBUTING.md` | Anleitung, wie wir mit Git zusammenarbeiten (Branches, Pull Requests). |
| `requirements.txt` | Liste der Python-Pakete. `pip install -r requirements.txt` installiert sie alle. |
| `.env.example` | Vorlage für API-Keys. Kopieren, in `.env` umbenennen und Keys eintragen. Wird erst für die KI gebraucht. |
| `.gitignore` | Liste der Dateien, die Git **nie** hochlädt: `.env` mit den Keys, Excel-Dateien, die Python-Umgebung `.venv`. |

Die Dateien mit einem Punkt am Anfang (`.env.example`, `.gitignore`) sind auf dem Mac im Finder versteckt. In VS Code sieht man sie normal.

## Einrichtung (einmalig pro Person)

Voraussetzungen: [Git](https://git-scm.com/downloads) und [Python 3.11+](https://www.python.org/downloads/).

```bash
# 1. Repo klonen
git clone https://github.com/keniaej/Zufall.git
cd Zufall

# 2. Virtuelle Umgebung anlegen und aktivieren
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 3. Pakete installieren
pip install -r requirements.txt
```

## Starten

Immer aus dem Hauptordner `Zufall` und **lokal auf eurem Rechner** (nicht über Google Colab, sonst blockiert öffentlichevergabe.de die Anfrage):

```bash
python -m agent.main
```

Das Ergebnis steht danach in `output/ausschreibungen.xlsx`. Die Datei wird bei jedem Lauf mit dem aktuellen Stand überschrieben.

Damit der Agent **automatisch einmal im Monat** läuft, siehe [automatisch/README.md](automatisch/README.md).

Tests (brauchen kein Internet):

```bash
python -m pytest
```

## Wo ändere ich was?

- **Andere CPV-Codes, Region oder Schlagwörter:** nur in `agent/konfiguration.py`
- **Neue Plattform anbinden:** `agent/quellen/vorlage.py` kopieren und in `agent/quellen/__init__.py` eintragen
- **Neue Prüfung:** Funktion in `agent/pruefungen.py` schreiben und unten in `PRUEFUNGEN` eintragen

## API-Keys

API-Keys gehören **nur** in die Datei `.env` (Vorlage: `.env.example`). Diese Datei wird nie hochgeladen. Das Repo ist öffentlich, also **nie Keys in den Code schreiben**.

## Zusammenarbeit

Wie wir mit Branches und Pull Requests arbeiten, steht in [CONTRIBUTING.md](CONTRIBUTING.md). Kurz: Niemand arbeitet direkt auf `main`.

## Aufgaben

Die Aufgaben verteilen wir gemeinsam und tragen sie dann als Issues ein (Tab *Issues* auf GitHub).
