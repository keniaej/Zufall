# Ausschreibungs-Agent (ZUFALL logistics group)

Ein Agent, der öffentliche Ausschreibungen sammelt, nach ZUFALLs Kriterien filtert, mit KI bewertet und in einem BI-Dashboard anzeigt.

## Der Ablauf und wo wir stehen

```
1. Abrufen      →  2. Prüfen      →  3. Excel       →  4. KI-Bewertung  →  5. Dashboard
   TED,              CPV, Region,      Relevant +        passt es zu        BI-Dashboard
   öffentliche-      Fristen,          Aussortiert       ZUFALL?            für ZUFALL
   vergabe.de        Schlagwörter
   ✅ fertig          ✅ fertig          🟡 erste Version   ⬜ offen            ⬜ offen
```

| Schritt | Datei | Stand |
|---------|-------|-------|
| Konfiguration (was gesucht wird) | `agent/konfiguration.py` | ✅ fertig, einige Fragen an ZUFALL offen |
| Gemeinsames Format (welche Spalten) | `agent/format.py` | ✅ fertig |
| 1. Quelle TED | `agent/quellen/ted.py` | ✅ funktioniert |
| 1. Quelle öffentlichevergabe.de | `agent/quellen/oeffentlichevergabe.py` | 🟡 gebaut, im letzten Test Timeout |
| 1. Weitere Quellen | `agent/quellen/vorlage.py` | ⬜ Vorlage vorhanden |
| 2. Prüfungen und Dubletten | `agent/pruefungen.py` | ✅ fertig |
| 3. Excel-Export | `agent/excel_export.py` | 🟡 einfache erste Version |
| 4. KI-Bewertung | `agent/ki_bewertung.py` | ⬜ offen |
| 5. Dashboard | `dashboard/` | ⬜ offen |
| Ablauf (alles zusammen) | `agent/main.py` | ✅ fertig |

Offene Fragen an ZUFALL und im Team stehen in [docs/offene_fragen.md](docs/offene_fragen.md).

## Ordner

```
Zufall/
├── agent/                 Der eigentliche Code (eine Datei pro Teil)
│   ├── konfiguration.py   TEIL 1: Was gesucht wird (CPV-Codes, Region, Schlagwörter)
│   ├── format.py          TEIL 2: Welche Spalten jede Quelle liefern muss
│   ├── quellen/           TEIL 3: Eine Datei pro Plattform
│   ├── pruefungen.py      TEIL 4: CPV, Region, Fristen, Schlagwörter, Dubletten
│   ├── excel_export.py    Schreibt die Excel-Datei
│   ├── ki_bewertung.py    OFFEN: KI-Bewertung
│   └── main.py            TEIL 5: Ablauf, hier läuft alles zusammen
├── notebooks/             Unser ursprüngliches Notebook (Stand 04.11.2026) und zum Ausprobieren
├── dashboard/             OFFEN: BI-Dashboard
├── docs/                  Offene Fragen, Notizen
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

Immer aus dem Hauptordner `Zufall`:

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
