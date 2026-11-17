# Kriterien: was der Agent sucht

In diesem Ordner stehen alle fachlichen Kriterien als CSV-Dateien. Sie lassen sich in Excel bearbeiten, ohne den Code anzufassen. Der Agent liest sie bei jedem Lauf neu ein.

| Datei | Inhalt | Spalten |
|-------|--------|---------|
| `cpv_codes.csv` | CPV-Codes, nach denen gesucht wird (Stand: CPV-Liste v2 von ZUFALL, 14.11.2026) | Code, Bezeichnung, Zufall Produkt, Segment, Aktiv |
| `produkte.csv` | Erlaubte ZUFALL-Produkte und ob sie regional begrenzt sind | Zufall Produkt, Regional begrenzt, Kürzel in ZUFALLs Liste |
| `standorte.csv` | ZUFALL-Standorte mit Koordinaten der Ortsmitte und Radius (70 km Luftlinie) | Standort, Breitengrad, Längengrad, Radius km |
| `region_kreise.csv` | Landkreise (NUTS-3-Codes) im Radius der Standorte, **berechnet** aus `standorte.csv` (siehe unten) | NUTS-Code, Landkreis, Standort, Lage, Entfernung Mittelpunkt km, Entfernung Rand km, NUTS-Stand |
| `ausschluss_codes.csv` | Ist einer dieser Codes der **Hauptcode** einer Ausschreibung, wird sie aussortiert (inkl. Unterkategorien) | Code, Bezeichnung, Grund |
| `ausschluss_woerter.csv` | Steht eines dieser Wörter im **Titel**, wird die Ausschreibung aussortiert | Wort |
| `suchworte.csv` | Suchbegriffe von ZUFALL. **Werden noch nicht verwendet**, ihre Rolle ist noch offen | Begriff, Sprache |

## So bearbeitet man die Dateien

1. Datei per Doppelklick in Excel öffnen.
2. Zeilen ändern, hinzufügen oder löschen. Die **Überschriften in Zeile 1 nicht ändern**.
3. Speichern mit *Datei → Speichern unter → „CSV UTF-8 (durch Trennzeichen getrennt)“*. Falls Excel fragt, ob das Format beibehalten werden soll: **Ja**.

Auch „CSV (Trennzeichen-getrennt)“ und Komma statt Semikolon funktionieren. Nur nicht als `.xlsx` speichern.

## Regeln

- **Code:** 8 Ziffern. `60100000-9` (mit Prüfziffer) geht auch, die Prüfziffer wird ignoriert. Jeder Code darf nur einmal vorkommen.
- **Oberbegriffe** schließen alle Unterkategorien ein: `60100000` findet auch `60112000` (Busse). Unerwünschte Unterkategorien gehören deshalb nach `ausschluss_codes.csv`.
- **Gleicher Zweig, mehrere Produkte:** Es gewinnt der genaueste Code. `60183000` (NSE) schlägt `60180000` (Landverkehr), und `60000000` (Transport allgemein) greift nur, wenn kein genauerer Code passt.
- **Aktiv:** `ja` oder `nein`. Mit `nein` bleibt ein Code in der Liste stehen, wird aber nicht gesucht. Das ist praktisch zum Ausprobieren.
- **Zufall Produkt** muss genau so in `produkte.csv` stehen. Ein neues Produkt zuerst dort eintragen.
- **Regional begrenzt = ja:** Ausschreibungen dieses Produkts zählen nur, wenn der Leistungsort in einem Landkreis aus `region_kreise.csv` liegt. Ohne Angabe zum Leistungsort bleiben sie drin.
- **Ausschluss-Wörter** werden ohne Rücksicht auf Groß- und Kleinschreibung gesucht und passen auch auf Wortanfänge: `pax` sortiert auch „PAX-Flüge“ aus.

## Region: Standorte und Radius

Entscheidung: **70 km Luftlinie ab Ortsmitte** jedes Standorts. Die Grenze ist bewusst großzügig:
Ein Landkreis zählt, sobald **irgendein Teil** von ihm im Radius liegt.

- `Lage = im Radius`: Der Mittelpunkt des Kreises liegt im Radius.
- `Lage = Randkreis`: Nur ein Teil des Kreises liegt im Radius (z. B. Frankfurt am Main, Region Hannover).
  Wer es enger will, löscht diese Zeilen einfach aus `region_kreise.csv`.
- Ein Kreis kann zweimal vorkommen (z. B. Wartburgkreis DEG0P und DEG0R): Eurostat hat die Codes
  einiger Kreise 2024 geändert, Bekanntmachungen verwenden beide Stände.

**Standort oder Radius ändern:** `standorte.csv` bearbeiten und danach einmal ausführen
(braucht Internet, lädt die Kreisgrenzen von Eurostat):

```bash
python werkzeuge/region_berechnen.py
```

Das überschreibt `region_kreise.csv`. Von Hand gelöschte Randkreise sind dann wieder drin.

Ausschreibungen ganz ohne Angabe zum Leistungsort bleiben drin (lieber mehr als zu wenig).

## Prüfen nach einer Änderung

```bash
python -m pytest
```

Enthält eine Datei einen Fehler, bricht der Agent mit einer Meldung ab, die Datei und Zeile nennt, zum Beispiel:
`kriterien/cpv_codes.csv, Zeile 5: Produkt 'Landverkehrr' gibt es nicht in kriterien/produkte.csv`.
