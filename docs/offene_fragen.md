# Offene Punkte

Erledigtes einfach abhaken: `- [x]`

## Aus dem Teamtreffen am 04.11.2026

### Technik
- [x] **Wo läuft das Skript?** Entscheidung 17.11.2026: unter Windows, manuell per Doppelklick auf `Agent starten.bat` (lokal, nicht über Google Colab). Offen bleibt, auf welchem Rechner es nach Projektende bei ZUFALL läuft.
- [ ] **NSPA (Nato):** wahrscheinlich nicht machbar, da keine öffentliche API. Mit ZUFALL besprechen.
- [x] **Feste Regeln für Dopplungen:** gleiche Verfahrens-ID = gleiche Ausschreibung, die neueste Fassung bleibt (am selben Tag die TED-Fassung), „Gefunden auf“ nennt alle Plattformen. Bei TED und öffentlichevergabe.de kam keine Bekanntmachung ohne Verfahrens-ID an. Für künftige Quellen ohne ID (z. B. Service.Bund) wäre eine Zusatzregel nötig (Auftraggeber + Frist + ähnlicher Titel).
- [x] **Spalte Timestamp:** umgesetzt als „Erstmals gefunden am“, „Zuletzt aktualisiert am“ und „Neu“ in der Übersicht.
- [x] **Ändert sich die Ausschreibungs-ID** bei Änderungen? Bei TED ja (neue Bekanntmachungsnummer). Deshalb laufen Dubletten und Abgleich über die Verfahrens-ID.
  Hinweis: Der Code unterscheidet schon zwischen *Ausschreibungs ID Platform* (pro Bekanntmachung) und *Verfahrens ID* (pro Vergabeverfahren). Die Dubletten-Prüfung behält pro Verfahrens ID die neueste Bekanntmachung.

### An ZUFALL klären
- [ ] **Versionsverlauf:** Ist ein Versionsverlauf der Ausschreibungen gewünscht, wenn sie aktualisiert werden, oder reicht die aktuellste Version mit dem Hinweis „Änderung liegt vor“?
- [x] **Geografische Angaben:** ZUFALL am 14.11.2026: ca. 70 km um die Standorte. Umgesetzt am 17.11.2026: Luftlinie ab Ortsmitte, Landkreise ganz oder teilweise im Radius (93 NUTS-Codes, `kriterien/region_kreise.csv`).
- [x] **CPV-Codes:** CPV-Liste v2 von ZUFALL erhalten (14.11.2026), steht in `kriterien/cpv_codes.csv`.

## Aus den Kommentaren im Code

### An ZUFALL
- [ ] **CPV 60440000 / 60410000 (Luft-Unterpunkte):** In v2 gestrichen, kommen aber über den Oberbegriff 60400000 weiter mit (Hagelabwehr, Hubschrauber, PAX). Lösung: in `kriterien/ausschluss_codes.csv` eintragen? Alte Frage: 60440000 Laut ZUFALL „Luftfracht- und Posttransportdienste“, in den TED-Daten aber „Dienstleistungen unter Einsatz von Luftfahrzeugen“. Bringt Hagelabwehrflüge, Drohnen, Helikopter, keine Luftfracht. Behalten oder streichen?
- [ ] **Region Landverkehr:** Zählt der Leistungsort (wo gefahren wird) und nicht der Sitz des Auftraggebers? (Annahme: Leistungsort.) Radius ist umgesetzt, siehe oben.
- [ ] **Bekanntmachungen ohne CPV-Code:** Fallen bei öffentlichevergabe.de aktuell raus. Ist das in Ordnung?
- [ ] **Notice-Typ `qu-sy` (Qualifizierungssystem):** mit Eike klären, ob relevant.

## Zur CPV-Liste v2 (14.11.2026)

- [x] **Oberbegriffe 60000000 und 63000000:** bringen Personenverkehr, Reisebüros u. a. mit. Entscheidung 17.11.2026: bleibt vorerst so, breite Liste ist zu Beginn gewollt. Eingrenzen später über `kriterien/ausschluss_codes.csv`.
- [ ] **Produktnamen:** Wir verwenden ausgeschriebene Namen (Landverkehr, Kontraktlogistik, Luftfracht, Seefracht …) statt der Kürzel aus v2 (LV, KL, Luft, See). Einverstanden?
- [ ] **Spalte Segment:** in den Bericht übernehmen?
- [ ] **Region je Produkt:** fehlt in v2. Annahme: nur Landverkehr regional begrenzt.
- [ ] **60160000 (Post auf der Straße)** ist in v2 gestrichen und fällt jetzt unter Landverkehr (60100000), also mit Regionsfilter. Gewollt?
- [ ] **Suchworte:** Wofür genau? Zusatzfilter, Ersatz bei fehlendem CPV-Code oder nur für die Oberbegriffe? „Linienverkehr Güter“ kollidiert mit dem Ausschlusswort „linienverkehr“.

## Noch zu entscheiden im Team

- [x] **KI-Bewertung:** entfällt (Entscheidung 14.11.2026). Gefiltert wird nur regelbasiert.
- [ ] **Power-BI-Dashboard:** Welche Inhalte und Ansichten? (`dashboard/README.md`)
- [ ] **Weitere Plattformen anbinden:** Service.Bund, e-Vergabe (`agent/quellen/vorlage.py`)
