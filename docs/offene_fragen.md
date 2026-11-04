# Offene Punkte

Erledigtes einfach abhaken: `- [x]`

## Aus dem Teamtreffen am 04.11.2026

### Technik
- [ ] **Wo läuft das Skript?** Es muss lokal oder über einen deutschen Server laufen. Über Google Colab (US-Server) wird die Anfrage an öffentlichevergabe.de blockiert.
- [ ] **NSPA (Nato):** wahrscheinlich nicht machbar, da keine öffentliche API. Mit ZUFALL besprechen.
- [ ] **Feste Regeln für Dopplungen** definieren (wann gilt eine Ausschreibung als doppelt, auch über Plattformen hinweg?).
- [ ] **Spalte Timestamp** hinzufügen, um Veränderungen aufzuzeigen.
- [ ] **Ändert sich die Ausschreibungs-ID** auf der Plattform, wenn die Ausschreibung geändert wird? An einem echten Beispiel prüfen.
  Hinweis: Der Code unterscheidet schon zwischen *Ausschreibungs ID Platform* (pro Bekanntmachung) und *Verfahrens ID* (pro Vergabeverfahren). Die Dubletten-Prüfung behält pro Verfahrens ID die neueste Bekanntmachung.

### An ZUFALL klären
- [ ] **Versionsverlauf:** Ist ein Versionsverlauf der Ausschreibungen gewünscht, wenn sie aktualisiert werden, oder reicht die aktuellste Version mit dem Hinweis „Änderung liegt vor“?
- [ ] **Geografische Angaben:** Nur die Städte/Landkreise der Standorte oder ein Umkreis von z. B. 50 km?
- [ ] **CPV-Codes** nochmal prüfen und spezifizieren: Sind sie wirklich richtig und vollständig?

## Aus den Kommentaren im Code

### An ZUFALL
- [ ] **CPV 60440000:** Laut ZUFALL „Luftfracht- und Posttransportdienste“, in den TED-Daten aber „Dienstleistungen unter Einsatz von Luftfahrzeugen“. Bringt Hagelabwehrflüge, Drohnen, Helikopter, keine Luftfracht. Behalten oder streichen? (`agent/konfiguration.py`)
- [ ] **CPV 60410000 (Linienflugverkehr):** Bringt Passagierflüge („PAX weltweit“). Behalten oder streichen?
- [ ] **Region Landverkehr:** Zählt der Leistungsort (wo gefahren wird) und nicht der Sitz des Auftraggebers? Nur die Landkreise der Standorte, ohne Nachbarkreise?
- [ ] **Bekanntmachungen ohne CPV-Code:** Fallen bei öffentlichevergabe.de aktuell raus. Ist das in Ordnung?
- [ ] **Notice-Typ `qu-sy` (Qualifizierungssystem):** mit Eike klären, ob relevant.

## Noch zu entscheiden im Team

- [ ] **KI-Bewertung:** Welches Modell, welche Kriterien, was soll die KI ausgeben? (`agent/ki_bewertung.py`)
- [ ] **Power-BI-Dashboard:** Welche Inhalte und Ansichten? (`dashboard/README.md`)
- [ ] **Weitere Plattformen anbinden:** Service.Bund, e-Vergabe (`agent/quellen/vorlage.py`)
