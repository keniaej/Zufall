# Offene Fragen

Gesammelt aus den Kommentaren im Code. Erledigtes einfach abhaken: `- [x]`

## An ZUFALL

- [ ] **CPV 60440000:** Laut ZUFALL „Luftfracht- und Posttransportdienste“, in den TED-Daten aber „Dienstleistungen unter Einsatz von Luftfahrzeugen“. Bringt Hagelabwehrflüge, Drohnen, Helikopter, keine Luftfracht. Behalten oder streichen? (`agent/konfiguration.py`)
- [ ] **CPV 60410000 (Linienflugverkehr):** Bringt Passagierflüge („PAX weltweit“). Behalten oder streichen?
- [ ] **Region Landverkehr:** Zählt der Leistungsort (wo gefahren wird) und nicht der Sitz des Auftraggebers? Nur die Landkreise der Standorte, ohne Nachbarkreise?
- [ ] **Bekanntmachungen ohne CPV-Code:** Fallen bei öffentlichevergabe.de aktuell raus. Ist das in Ordnung?
- [ ] **Notice-Typ `qu-sy` (Qualifizierungssystem):** mit Eike klären, ob relevant.

## Im Team

- [ ] KI-Bewertung: Modell, Kriterien, Ausgabe (`agent/ki_bewertung.py`)
- [ ] Dashboard: Werkzeug und Inhalte (`dashboard/README.md`)
- [ ] Weitere Quellen anbinden? (`agent/quellen/vorlage.py`)
- [ ] öffentlichevergabe.de lief am letzten Test in einen Timeout: nur zeitweise oder dauerhaft?
