# Automatisch laufen lassen

Der Agent soll **einmal im Monat** von selbst laufen und dabei immer dieselbe Datei aktualisieren: `output/ausschreibungen.xlsx`. Power BI bleibt mit dieser Datei verbunden.

## Wichtig vorab

- Er muss **auf einem Rechner in Deutschland** laufen, nicht über Google Colab oder andere US-Server, sonst blockiert öffentlichevergabe.de die Anfrage.
- **Nur eine Person** im Team richtet das ein, auf dem Rechner, auf dem auch die Excel-Datei für Power BI liegen soll.
- Der Rechner muss zur geplanten Zeit **eingeschaltet** sein. Ist ein Mac zu dieser Zeit im Ruhezustand, holt er den Lauf nach, sobald er aufwacht. Ist er ausgeschaltet, fällt der Lauf aus.
- Für den echten Betrieb bei ZUFALL wäre später ein Server in Deutschland besser.

## Mac

Einmalig im Terminal, im Hauptordner `Zufall`:

```bash
bash automatisch/einrichten_mac.sh
```

Das war's. Der Agent läuft dann am 1. jedes Monats um 8:00 Uhr.

- **Sofort testen:** `launchctl start de.zufall.ausschreibungsagent` und nach ein paar Minuten in `output/log.txt` schauen.
- **Anderer Rhythmus:** oben in `automatisch/einrichten_mac.sh` TAG, STUNDE und MINUTE ändern und das Skript noch einmal starten.
- **Ausschalten:** `bash automatisch/ausschalten_mac.sh`
- **Fehler „Operation not permitted“ im Protokoll:** macOS erlaubt den Zugriff auf den Ordner nicht (passiert oft bei „Dokumente“ oder „Schreibtisch“). Lösung: den Ordner `Zufall` z. B. direkt in den Benutzerordner verschieben und das Skript neu starten.

## Windows

Über die **Aufgabenplanung** (im Startmenü „Aufgabenplanung“ suchen):

1. Rechts **Einfache Aufgabe erstellen** → Name: `Ausschreibungs-Agent`
2. Trigger: **Monatlich** → alle Monate, Tag 1, Uhrzeit 08:00
3. Aktion: **Programm starten**
   - Programm: `C:\Pfad\zu\Zufall\.venv\Scripts\python.exe`
   - Argumente: `-m agent.main`
   - Starten in: `C:\Pfad\zu\Zufall`
4. **Fertig stellen.** Zum Testen: Rechtsklick auf die Aufgabe → **Ausführen**.
