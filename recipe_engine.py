import json
from pathlib import Path
import re

DATA = Path(__file__).parent / "data" / "recipes.json"

def load_recipes():
    return json.loads(DATA.read_text(encoding="utf-8"))

def norm(s):
    s = s.lower().strip()
    aliases = {"eier":"ei", "tomaten":"tomate", "kartoffeln":"kartoffel", "zwiebeln":"zwiebel",
               "nudeln":"nudel", "paprika":"paprika", "spinat":"spinat", "champignons":"champignon"}
    return aliases.get(s, s)

def ingredient_match(recipe, available, pantry):
    names = [norm(x["name"]) for x in available] + [norm(x) for x in pantry]
    required = [norm(x) for x in recipe["ingredients"]]
    have = [x for x in required if any(x == n or x in n or n in x for n in names)]
    missing = [x for x in recipe["ingredients"] if norm(x) not in have]
    return len(set(have)), len(set(required)), missing

def find_recipes(recipes, available, pantry, max_minutes=999, diet="Alle", low_extra=False):
    results = []
    for r in recipes:
        if r["minutes"] > max_minutes: continue
        if diet == "Vegetarisch" and r["category"] == "Vegan": continue
        if diet == "Vegan" and r["category"] != "Vegan": continue
        have,total,missing = ingredient_match(r, available, pantry)
        ratio = have / total if total else 0
        # Normaler Modus: nur Rezepte mit mindestens 60% Zutatenabdeckung.
        if not low_extra and ratio < .60: continue
        results.append((r, have, len(missing)))
    results.sort(key=lambda x: (-x[1]/max(1,len(x[0]["ingredients"])), x[2], x[0]["minutes"]))
    return [x[0] for x in results]
