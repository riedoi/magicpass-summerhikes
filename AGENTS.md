# AGENTS.md

## Projekt

Dieses Repository ist eine statische GPX- und Markdown-Sammlung für Sommerwanderungen zu Magic-Pass-Destinationen.

## Grundregeln

- Kein Overengineering.
- Keine Scraping-Pipeline bauen.
- Keine Datenbank, API oder Web-App bauen.
- Markdown ist der primäre Index.
- Pro Kanton oder Land gibt es ein Markdown-File unter `destinations/`.
- GPX-Dateien liegen unter `gpx/<kanton-oder-land>/<destination>/`.
- Offizielle Quellen bevorzugen.
- Zuerst Betreiberseiten, Bergbahnseiten oder direkte Destinationsseiten prüfen.
- Regionale oder kantonale Tourismusplattformen nur als Fallback verwenden, wenn beim Betreiber keine route-spezifischen Daten oder GPX-Dateien verfügbar sind.
- Nichts erfinden. Fehlende Werte mit `offen` markieren.
- Source-Links müssen zur Wanderung oder mindestens zur offiziellen Destinations-/Tourismusseite führen.
- Relative Links zu GPX-Dateien müssen funktionieren.

## Wanderungskriterien

- ca. 3 Wanderungen pro Destination
- Distanz ca. 5-20 km
- Sommerwanderung
- bevorzugt offizielle Bahnbetreiber-, Destinations- oder Tourismus-Webseiten
- Rundwanderungen bevorzugt
- bei Streckenwanderungen Rückreisehinweis ergänzen

## Markdown-Standard pro Destination

Jede Destination soll enthalten:

1. Offizielle Informationen
2. Aktualitätshinweis
3. Wanderungstabelle
4. Notizen

Standardtabelle:

```markdown
| Wanderung | Distanz | Dauer | Schwierigkeit | GPX | Quelle |
|---|---:|---:|---|---|---|
```

Aktualitätshinweis:

```markdown
> **Aktualität prüfen:** Bitte vor der Wanderung Öffnungszeiten, Bergbahnbetrieb, Wegzustand, Wetter, Sperrungen und Rückreise direkt bei den offiziellen Links dieser Destination prüfen.
```

## Dateinamen

- klein schreiben
- keine Leerzeichen
- keine Umlaute
- Bindestriche verwenden
- `.gpx` für GPX-Dateien

Beispiele:

```text
soerenberg
huernli
memises
marbachegg-huernli-marbach.gpx
```
