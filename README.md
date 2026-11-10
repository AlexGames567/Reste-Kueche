# Resteküche – Streamlit

## Starten
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## KI-Modell anschließen
Die UI ruft `recognize_ingredients(image)` in `vision_adapter.py` auf.
Verbinde dort dein vorhandenes Bild-/Vision-Modell. Die erwartete Ausgabe:
```python
[
  {"name": "Tomaten", "confidence": 0.94},
  {"name": "Spinat", "confidence": 0.81}
]
```
Zum Testen der Oberfläche ohne Modell: `DEMO_VISION=1` setzen.

## Rezepte
Die Beispieldaten liegen in `data/recipes.json`. Eigene Rezepte können im gleichen JSON-Format ergänzt werden.
Für Internetrezepte kann `recipe_engine.py` um eine externe Rezept-API erweitert werden. Achte auf Nutzungsbedingungen, Quellenangaben und Rate Limits.

## Enthalten
- Foto-Upload (mehrere Bilder) und KI-Erkennungsadapter
- Zutatenliste bearbeiten/löschen/hinzufügen
- Vorratszutaten, die immer als vorhanden gelten
- Filter nach Zeit und Ernährungsweise
- Matching und Fallback-Sortierung nach möglichst wenigen fehlenden Zutaten
- Rezeptdetails und Favoriten
- Profil-/Einstellungsansicht

## Vor Produktivbetrieb
- Nutzerkonten und persistente Datenbank ergänzen
- Datenschutz, Löschfristen und Einwilligung für Bildverarbeitung definieren
- Allergene/Unverträglichkeiten zuverlässig berücksichtigen
- Mengen-Normalisierung und Synonyme für Zutaten ausbauen
- Externe Rezeptquelle/API anbinden
