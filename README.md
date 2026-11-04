# Ausschreibungs-Agent

Ein KI-Agent, der über die APIs von Ausschreibungsportalen aktuelle Ausschreibungen abruft und in einer Excel-Datei sammelt.

## Projektstruktur

```
Zufall/
├── src/ausschreibungs_agent/
│   ├── main.py            # Startpunkt: holt Ausschreibungen und schreibt die Excel-Datei
│   ├── config.py          # Liest API-Keys und Einstellungen aus der .env-Datei
│   ├── excel_export.py    # Schreibt die Ergebnisse nach Excel
│   └── quellen/           # Eine Datei pro Ausschreibungsportal
│       └── beispiel_quelle.py
├── tests/                 # Tests
├── output/                # Hier landen die Excel-Dateien (nicht in Git)
├── docs/                  # Notizen, Doku zu den APIs
├── .env.example           # Vorlage für eure API-Keys
├── requirements.txt       # Python-Pakete
└── CONTRIBUTING.md        # So arbeiten wir im Team mit Git
```

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

# 4. API-Keys eintragen
# .env.example kopieren und in .env umbenennen, dann die Keys eintragen
cp .env.example .env
```

## Starten

```bash
python -m src.ausschreibungs_agent.main
```

Die Excel-Datei erscheint danach im Ordner `output/`.

## Wichtig: API-Keys

API-Keys gehören **nur** in die Datei `.env`. Diese Datei wird nie zu GitHub hochgeladen (sie steht in `.gitignore`). Teilt die Keys im Team über einen sicheren Weg, z. B. einen Passwort-Manager, aber niemals im Code oder im Chat des Repos.

## Branches

| Branch | Wofür |
|--------|-------|
| `main` | Immer die funktionierende Version. Hier wird **nie direkt** gearbeitet, nur per Pull Request. |
| `feature/...` | Ein Branch pro Aufgabe, z. B. `feature/quelle-ted`. Wird nach dem Merge gelöscht. |
| `fix/...` | Für Fehlerbehebungen, z. B. `fix/datum-format`. |

Wie das genau geht, steht in [CONTRIBUTING.md](CONTRIBUTING.md).

## Aufgaben

Die Aufgaben verteilen wir gemeinsam und tragen sie dann als Issues ein (Tab *Issues* auf GitHub).
