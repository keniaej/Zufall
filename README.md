# Agent Öffentliche Ausschreibungen (ZUFALL logistics group)

Projekt WS 2026/27: Ein KI-Agent, der öffentliche Transport- und Lagerausschreibungen von mehreren Plattformen sammelt, nach ZUFALLs Kriterien qualifiziert und in einem Power-BI-Dashboard darstellt.

Die vollständige Aufgabenstellung steht in [docs/projekt.md](docs/projekt.md), die offenen Punkte in [docs/offene_fragen.md](docs/offene_fragen.md).

## Pipeline und Stand

```
1. Abrufen + Python-Filter    →    2. Excel                →    3. Power BI
   API-Abruf der Plattformen,        Übersicht abgleichen,         Dashboard mit den
   feste Kriterien (CPV, Region,     ob interessant für ZUFALL;    qualifizierten
   Fristen, Schlagwörter)            Ergebnis in Excel             Ausschreibungen
   ✅ größtenteils fertig             ✅ fertig                      ⬜ offen
```

| Schritt | Datei | Stand |
|---------|-------|-------|
| Kriterien (was gesucht wird) | `kriterien/*.csv` | ✅ CPV-Liste v2 von ZUFALL (14.11.2026), 70-km-Radius, in Excel bearbeitbar |
| 1. Abrufen der Plattformen | `agent/quellen/` | 🟡 siehe Plattform-Tabelle |
| 1. Feste Filter und Dubletten | `agent/pruefungen/` | ✅ fertig |
| 2. Excel | `agent/bericht/` | ✅ feste Datei `output/ausschreibungen.xlsx`, Übersicht wird abgeglichen statt neu aufgebaut |
| Ablauf (alles zusammen) | `agent/ablauf.py`, `agent/main.py` | ✅ fertig |
| Automatischer Lauf (einmal im Monat) | `automatisch/` | ✅ Anleitung und Skript für Mac, Anleitung für Windows |
| 3. Power-BI-Dashboard | `dashboard/` | ⬜ offen |

## Plattformen

| Plattform | Datei | Stand |
|-----------|-------|-------|
| TED (EU) | `agent/quellen/ted.py` | ✅ funktioniert |
| öffentlichevergabe.de | `agent/quellen/oeffentlichevergabe.py` | 🟡 gebaut, läuft nur lokal bzw. von deutschem Server (über Google Colab blockiert) |
| Service.Bund | – | ⬜ offen |
| e-Vergabe | – | ⬜ offen |
| NSPA (Nato) | – | ❌ wahrscheinlich nicht machbar, keine öffentliche API |

Neue Plattform anbinden: `agent/quellen/vorlage.py` kopieren, die Klasse ausfüllen und in `QUELLEN_KLASSEN` in `agent/quellen/__init__.py` eintragen.

## Ordner und Dateien

Die Spalte **Herkunft** zeigt, woher der Inhalt kommt:
- **Notebook:** unser Code aus `TED_API.ipynb`, nur in eine eigene Datei verschoben
- **neu:** später dazugekommen

### `agent/`: der eigentliche Code

Der Agent wird mit `python -m agent.main` gestartet. Der Code ist **objektorientiert** aufgebaut (Stand 17.11.2026), damit neue Plattformen und Regeln leicht dazukommen. Das Verhalten ist dasselbe wie vorher, nur sauber aufgeteilt.

#### So hängt alles zusammen

```
main.py          baut den Agenten zusammen:
                   Einstellungen + Kriterien laden → Quellen + Prüfungen + Bericht erzeugen
   │
   ▼
ablauf.py        class Agent – der Ablauf eines Laufs:
                   1. jede Quelle.holen()            (TED, öffentlichevergabe.de, ...)
                   2. DublettenErkennung.entfernen()
                   3. jede Pruefung.pruefen()        (CPV, Region, Frist, Schlagwörter)
                   4. ExcelBericht.schreiben()
```

Der `Agent` kennt keine einzelne Plattform und keine einzelne Regel. Er arbeitet nur mit den **Basisklassen** `Quelle` und `Pruefung`. Eine neue Plattform oder Regel braucht deshalb keine Änderung am Ablauf.

**Kurz erklärt: Basisklasse und Vererbung.** Eine Basisklasse legt fest, welche Methoden jede Unterklasse haben **muss** (mit `@abstractmethod` markiert). `TedQuelle(Quelle)` heißt: TedQuelle ist eine Quelle und füllt deren Methoden `abrufen()` und `umwandeln()` aus. Vergisst eine neue Quelle eine davon, meldet Python sofort einen Fehler, statt erst mitten im Lauf.

#### Dateien

| Datei | Was sie macht | Herkunft |
|-------|---------------|----------|
| `main.py` | Startpunkt. Baut den Agenten aus Einstellungen, Kriterien, Quellen, Prüfungen und Bericht zusammen. | neu |
| `ablauf.py` | **`class Agent`**: der Ablauf (abrufen → Dubletten → Prüfungen → Bericht). Fällt eine Quelle aus, laufen die anderen weiter. | Notebook (TEIL 5) |
| `einstellungen.py` | **`class Einstellungen`**: Technik (Startdatum, Land, Bekanntmachungsarten, Ordner). | Notebook (TEIL 1) |
| `kriterien.py` | **`class Kriterien`**: liest und prüft die CSV-Dateien aus `kriterien/` (Fehler mit Datei und Zeile), ordnet CPV-Codes den ZUFALL-Produkten zu. | Notebook (TEIL 1) |
| `modell.py` | Die Liste `SPALTEN`, die jede Quelle liefern muss, und **`class LaufErgebnis`** (alles, was ein Lauf erzeugt). | Notebook (TEIL 2) |
| `werte.py` | Kleine Hilfsfunktionen: Datum, Land, Vergabeart, Vertragsdauer, Texte bereinigen. | Notebook (TEIL 2) |
| `quellen/basis.py` | **`class Quelle`** (Basisklasse): `abrufen()`, `umwandeln()`, `holen()`. | neu |
| `quellen/ted.py` | **`class TedQuelle`**: TED-Search-API. | Notebook (TEIL 3) |
| `quellen/oeffentlichevergabe.py` | **`class OeffentlicheVergabeQuelle`**: Monats-CSV + eForms-XML. | Notebook (TEIL 3) |
| `quellen/vorlage.py` | Vorlage zum Kopieren für eine neue Plattform. Wird nicht ausgeführt. | neu |
| `quellen/__init__.py` | Liste `QUELLEN_KLASSEN`: welche Plattformen abgefragt werden. | Notebook |
| `pruefungen/basis.py` | **`class Pruefung`** (Basisklasse): `gruende()` liefern, `pruefen()` teilt in behalten/aussortiert. | neu |
| `pruefungen/cpv.py`, `region.py`, `frist.py`, `schlagwoerter.py` | Je eine Prüfung als Klasse: `CpvPruefung`, `RegionPruefung`, `FristPruefung`, `SchlagwortPruefung`. | Notebook (TEIL 4) |
| `pruefungen/dubletten.py` | **`class DublettenErkennung`**: gleiche Verfahrens-ID = gleiche Ausschreibung, neueste Fassung bleibt. | Notebook (TEIL 4) |
| `pruefungen/__init__.py` | `standard_pruefungen()`: welche Prüfungen in welcher Reihenfolge laufen. | neu |
| `bericht/excel_bericht.py` | **`class ExcelBericht`**: Datei öffnen, sichern, speichern; bricht früh ab, wenn sie in Excel offen ist. | neu |
| `bericht/uebersicht.py` | **`class UebersichtAbgleich`**: Blatt *Übersicht* abgleichen statt neu aufbauen (Einträge von ZUFALL bleiben). | neu |
| `bericht/blaetter.py` | **`class PlattformBlatt`**, **`class StatusBlatt`**: Blätter, die jedes Mal neu entstehen. | neu |
| `bericht/excel_hilfen.py` | Helfer für Excel: als Tabelle formatieren, Links, Spaltenbreiten. | neu |
| `__init__.py` | Leere Datei. Python braucht sie, damit es den Ordner als zusammengehörigen Code erkennt. Nicht löschen. | neu |

### Weitere Ordner

| Ordner / Datei | Was es ist | Herkunft |
|----------------|------------|----------|
| `notebooks/TED_API.ipynb` | Unser ursprüngliches Notebook, unverändert (Stand 04.11.2026). Zum Nachschauen und Ausprobieren. Der Agent selbst nutzt es nicht. | Notebook |
| `automatisch/README.md` | Anleitung, wie der Agent einmal im Monat von selbst läuft (Mac und Windows). | neu |
| `automatisch/einrichten_mac.sh` | Schaltet auf dem Mac den monatlichen Lauf ein. Einmal starten mit `bash automatisch/einrichten_mac.sh`. | neu |
| `automatisch/ausschalten_mac.sh` | Schaltet den monatlichen Lauf auf dem Mac wieder aus. | neu |
| `werkzeuge/region_berechnen.py` | Berechnet einmalig die Landkreise im 70-km-Radius der Standorte und schreibt `kriterien/region_kreise.csv`. Nur nötig, wenn sich Standorte oder Radius ändern. | neu |
| `kriterien/` | **Die Suchkriterien als CSV-Dateien:** CPV-Codes, Produkte, Region, Ausschluss-Codes, Ausschluss-Wörter, Suchworte. ZUFALL kann sie in Excel bearbeiten. Anleitung in `kriterien/README.md`. | neu |
| `dashboard/README.md` | **Platzhalter** für das Power-BI-Dashboard, mit den Fragen, die wir noch klären müssen. | neu |
| `docs/projekt.md` | Aufgabenstellung und unsere geplante Pipeline. | neu |
| `docs/offene_fragen.md` | Checkliste aller offenen Punkte (Team und Fragen an ZUFALL). | neu |
| `tests/` | Tests ohne Internet, starten mit `python -m pytest`. `test_agent_und_bericht.py` lässt den ganzen Agenten mit Testquellen laufen (inkl. Excel und Abgleich), die anderen prüfen Kriterien, Prüfungen, Quellen und Hilfsfunktionen. `conftest.py` enthält `FesteQuelle`, eine Testquelle ohne Internet. | neu |
| `output/` | Hier landen `ausschreibungen.xlsx`, die Sicherungen (`sicherungen/`, die letzten 10 Stände) und `log.txt` (Protokoll des automatischen Laufs). Wird **nicht** zu GitHub hochgeladen, es liegt nur auf eurem Rechner. | neu |

### Dateien im Hauptordner

| Datei | Was sie macht |
|-------|---------------|
| `README.md` | Diese Übersicht. |
| `CONTRIBUTING.md` | Anleitung, wie wir mit Git zusammenarbeiten (Branches, Pull Requests). |
| `requirements.txt` | Liste der Python-Pakete. `pip install -r requirements.txt` installiert sie alle. |
| `.env.example` | Vorlage für API-Keys. Kopieren, in `.env` umbenennen und Keys eintragen. Aktuell braucht keine Plattform einen Key. |
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

Das Ergebnis steht danach in `output/ausschreibungen.xlsx`:
- **Übersicht:** relevante Ausschreibungen in ZUFALLs Struktur. Wird bei jedem Lauf **abgeglichen**, nicht neu aufgebaut: neue Ausschreibungen kommen unten dazu (feste ID, `Neu = ja`), bekannte werden aktualisiert, nichts wird gelöscht. Spalten wie *Entscheidung* und *Kommentar* oder eigene Spalten von ZUFALL bleiben erhalten.
- **TED, oeffentlichevergabe.de:** alles, was abgerufen wurde, mit Spalte *Ergebnis*. Jedes Mal neu.
- **Status:** wann der Lauf war und was jede Plattform geliefert hat.

Die Datei muss beim Start **geschlossen** sein, sonst bricht der Agent sofort ab. Vor jedem Speichern wird der alte Stand in `output/sicherungen/` gesichert.

Damit der Agent **automatisch einmal im Monat** läuft, siehe [automatisch/README.md](automatisch/README.md).

Tests (brauchen kein Internet):

```bash
python -m pytest
```

## Wo ändere ich was?

- **Andere CPV-Codes, Produkte, Region, Ausschlüsse oder Suchworte:** nur in den CSV-Dateien in `kriterien/` (in Excel bearbeitbar, siehe [kriterien/README.md](kriterien/README.md))
- **Standorte oder Radius:** in `kriterien/standorte.csv`, danach `python werkzeuge/region_berechnen.py` ausführen
- **Startdatum, Land, Bekanntmachungsarten:** in `agent/einstellungen.py`
- **Neue Plattform anbinden:** `agent/quellen/vorlage.py` kopieren, Klasse ausfüllen und in `QUELLEN_KLASSEN` in `agent/quellen/__init__.py` eintragen. Sie bekommt automatisch ein eigenes Blatt im Excel.
- **Neue Prüfung:** Klasse von `Pruefung` ableiten (Beispiel: `agent/pruefungen/frist.py`) und in `standard_pruefungen()` in `agent/pruefungen/__init__.py` eintragen
- **Spalten der Übersicht:** in `agent/bericht/uebersicht.py`

## API-Keys

API-Keys gehören **nur** in die Datei `.env` (Vorlage: `.env.example`). Diese Datei wird nie hochgeladen. Das Repo ist öffentlich, also **nie Keys in den Code schreiben**.

## Zusammenarbeit

Wie wir mit Branches und Pull Requests arbeiten, steht in [CONTRIBUTING.md](CONTRIBUTING.md). Kurz: Niemand arbeitet direkt auf `main`.

## Aufgaben

Die Aufgaben verteilen wir gemeinsam und tragen sie dann als Issues ein (Tab *Issues* auf GitHub).
