# Projektbeschreibung

**Projekt WS 2026/27**
**Thema:** KI-Agenten – Zur Sammlung und Verarbeitung von externen/öffentlichen Informationen

## Unternehmen

Die **ZUFALL logistics group** ist ein familiengeführter Transport- und Logistikdienstleister. Gegründet 1928 in Kassel, liegt der heutige Firmensitz in Göttingen.

Das Unternehmen gliedert sich in zwei große Geschäftsbereiche:
- **Transport:** Landverkehre Deutschland und Europa, Night Star Express, Luft- und Seefracht, Zoll Service
- **Logistik:** Kontraktlogistik, also kundenorientierte, langfristige Kooperationen zwischen Unternehmen und Logistikdienstleister

Mit ca. 2.100 Mitarbeitenden (davon 157 Auszubildende) an 11 Standorten in ganz Deutschland transportiert das Unternehmen rund 5 Millionen Sendungen pro Jahr und erwirtschaftete im vergangenen Geschäftsjahr einen Umsatz von rund 430 Millionen Euro.

Das Unternehmen hat sich auf den Weg gemacht, die Logistik nachhaltig achtsam zu gestalten. 2019 hat ZUFALL das **zufall.lab** in Göttingen gegründet. In der Experimentierwerkstatt stehen Forschung und Entwicklung im Vordergrund. Hier testet der Logistikdienstleister neue logistische Ansätze, Prototypen und Prozesse für eine bessere und nachhaltigere Logistik von morgen.

## Aufgabenstellung

Entwicklung zweier KI-Agenten (je eine Projektgruppe):
1. Sammeln öffentlicher Transportausschreibungen von unterschiedlichen Plattformen (bspw. TED, Service.Bund, NSPA etc.) sowie deren Qualifizierung. 

## Erwartete Ergebnisse

### „Agent Öffentliche Ausschreibungen“ (unsere Gruppe)

1. KI-Agent, der öffentliche Transport- und Lagerausschreibungen auf den Plattformen **TED, Service.Bund, NSPA (Nato), e-Vergabe, öffentlichevergabe.de** nach vordefinierten Kriterien sammelt

## Unsere geplante Pipeline

1. **Abrufen und Python-Filter:** Ausschreibungen per API in Python abrufen. Nicht alle werden übernommen: Ein fester Filter nach Kriterien (CPV-Codes, Region, Fristen, Schlagwörter) begrenzt die Menge.
2. **KI-Filter und Excel:** Die gefilterten Ausschreibungen werden in Python von einer KI bewertet: Sind sie für ZUFALL interessant oder nicht? Das Ergebnis wird mit der Bewertung in eine Excel-Datei geschrieben. Es gibt also zwei Filter: einen festen in Python und einen „intelligenten“ mit KI.
3. **Power BI:** Die qualifizierten Ausschreibungen werden in einem Power-BI-Dashboard dargestellt. Datenquelle ist die Excel-Datei.
