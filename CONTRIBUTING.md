# Mitmachen

Neue Wanderungen sind willkommen, wenn sie zur Sammlung passen.

## Grundregeln

- bevorzugt offizielle Quellen von Bahnbetreibern, Destinationen oder Tourismusorganisationen verwenden
- keine Daten erfinden; fehlende Angaben mit `offen` markieren
- pro Wanderung eine ursprüngliche Quelle verlinken
- GPX-Dateien nur speichern, wenn sie aus einer nachvollziehbaren Quelle stammen
- GPX-Dateien klein schreiben, ohne Leerzeichen und ohne Umlaute benennen
- bei Streckenwanderungen Rückreisehinweis ergänzen

## Tabellenformat

```markdown
| Wanderung | Distanz | Dauer | Schwierigkeit | Swisstopo | Karte | GPX | Quelle |
|---|---:|---:|---|---|---|---|---|
```

Nach dem Ergänzen oder Ändern von GPX-Dateien:

```bash
python3 scripts/update_gpx_links.py
```
