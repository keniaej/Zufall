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
| 2. Excel-Export | `agent/excel_export.py` | 🟡 einfache erste Version |
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

## Ordner

```
Zufall/
├── agent/                 Der eigentliche Code (eine Datei pro Teil)
│   ├── konfiguration.py   TEIL 1: Was gesucht wird (CPV-Codes, Region, Schlagwörter)
│   ├── format.py          TEIL 2: Welche Spalten jede Quelle liefern muss
│   ├── quellen/           TEIL 3: Eine Datei pro Plattform
│   ├── pruefungen.py      TEIL 4: CPV, Region, Fristen, Schlagwörter, Dubletten
│   ├── ki_bewertung.py    OFFEN: KI-Bewertung
│   ├── excel_export.py    Schreibt die Excel-Datei
│   └── main.py            TEIL 5: Ablauf, hier läuft alles zusammen
├── notebooks/             Unser ursprüngliches Notebook (Stand 04.11.2026) und zum Ausprobieren
├── dashboard/             OFFEN: Power-BI-Dashboard
├── docs/                  Aufgabenstellung, offene Punkte
├── tests/                 Kleine Tests der Regeln
└── output/                Hier landen die Excel-Dateien (nicht in Git)
```

Die Teile 1 bis 5 sind dieselben wie in unserem Notebook, nur jeweils in einer eigenen Datei. So können mehrere Leute gleichzeitig an verschiedenen Teilen arbeiten, ohne sich gegenseitig zu überschreiben.

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

Die Excel-Datei erscheint danach in `output/`.

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
