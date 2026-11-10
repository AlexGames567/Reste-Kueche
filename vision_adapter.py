"""Adapter für das bereits vorhandene Vision-Modell.

Erwartete Rückgabe: Liste von Dictionaries, z.B.
[{"name": "Tomaten", "confidence": 0.94}]

Passe NUR recognize_ingredients() an dein Modell an.
"""
import os
import json
DEMO_VISION = 1
def recognize_ingredients(image):
    # Optionaler JSON-Demo-Modus zum Testen der Oberfläche.
    # Setze DEMO_VISION=1, um Beispielergebnisse zurückzugeben.
    if os.getenv("DEMO_VISION", "0") == "1":
        return [
            {"name":"Tomaten","confidence":0.95},
            {"name":"Paprika","confidence":0.91},
            {"name":"Eier","confidence":0.88},
            {"name":"Spinat","confidence":0.78},
        ]

    # TODO: Hier dein fertiges Modell aufrufen.
    # Beispiel:
    # result = dein_modell.predict(image)
    # return [{"name": x.name} for x in result]
    raise RuntimeError(
        "Vision-Modell noch nicht verbunden. Bitte recognize_ingredients() "
        "in vision_adapter.py mit deinem Modell verknüpfen oder DEMO_VISION=1 setzen."
    )
