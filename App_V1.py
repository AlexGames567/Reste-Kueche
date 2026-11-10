import base64
import json
import os

import streamlit as st

st.set_page_config(page_title="Resteküche", page_icon="🥬", layout="centered")

# Farben und Grundstil passend zur PDF-Vorlage
st.markdown("""
<style>
    .stApp { background: #fbfaf5; color: #183e30; }
    h1, h2, h3 { color: #194c38; }
    .block-container { max-width: 900px; padding-top: 1.5rem; }
    div.stButton > button {
        border-radius: 12px; border: 1px solid #d8e1d9;
        color: #194c38; background: white;
    }
    div.stButton > button[kind="primary"] {
        background: #f4772d; color: white; border: 0;
    }
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #eee9de;
        padding: 12px; border-radius: 14px;
    }
    .recipe-card {
        background: white; padding: 16px; border-radius: 16px;
        border: 1px solid #eee9de; margin: 8px 0 14px 0;
    }
    .muted { color: #758078; font-size: .92rem; }
</style>
""", unsafe_allow_html=True)

RECIPES = [
    {
        "name": "Shakshuka mit Spinat", "minutes": 18,
        "ingredients": ["Tomaten", "Paprika", "Eier", "Spinat", "Zwiebel"],
        "steps": "Zwiebel und Paprika anbraten. Tomaten dazugeben und köcheln lassen. "
                 "Mulden formen, Eier hineingeben und zugedeckt stocken lassen. "
                 "Zum Schluss Spinat unterheben.",
        "url": "https://de.wikipedia.org/wiki/Shakshuka",
        "vegetarian": True,
    },
    {
        "name": "Gemüse-Pasta", "minutes": 22,
        "ingredients": ["Nudeln", "Tomaten", "Paprika", "Spinat", "Zwiebel"],
        "steps": "Nudeln kochen. Gemüse klein schneiden und anbraten. Mit etwas Nudelwasser "
                 "vermengen, würzen und die Nudeln unterheben.",
        "url": "https://www.chefkoch.de/",
        "vegetarian": True,
    },
    {
        "name": "Brotauflauf gegen Reste", "minutes": 30,
        "ingredients": ["Brot", "Eier", "Milch", "Spinat", "Käse"],
        "steps": "Brot würfeln und in eine Form geben. Eier mit Milch verquirlen, Gemüse "
                 "und Käse dazugeben. Darüber gießen und bei 180 °C backen, bis die Masse "
                 "gestockt und goldbraun ist.",
        "url": "https://www.chefkoch.de/",
        "vegetarian": True,
    },
    {
        "name": "Tomaten-Paprika-Omelett", "minutes": 15,
        "ingredients": ["Eier", "Tomaten", "Paprika", "Käse"],
        "steps": "Gemüse anbraten. Eier verquirlen, darüber gießen und stocken lassen. "
                 "Mit Käse bestreuen.",
        "url": "https://www.chefkoch.de/",
        "vegetarian": True,
    },
    {
        "name": "Spinat-Feta-Pfanne", "minutes": 15,
        "ingredients": ["Spinat", "Feta", "Eier", "Zwiebel"],
        "steps": "Zwiebel anbraten, Spinat dazugeben und zusammenfallen lassen. Feta "
                 "darüberbröseln und nach Wunsch mit Ei servieren.",
        "url": "https://www.chefkoch.de/",
        "vegetarian": True,
    },
]

if "ingredients" not in st.session_state:
    st.session_state.ingredients = {
        "Tomaten": "3 Stück", "Paprika": "1 Stück", "Eier": "4 Stück",
        "Spinat": "ca. 100 g",
    }
if "favorites" not in st.session_state:
    st.session_state.favorites = []
if "always_available" not in st.session_state:
    st.session_state.always_available = ["Salz", "Öl", "Zucker"]
if "page" not in st.session_state:
    st.session_state.page = "Start"


def recognize_image(image_bytes, mime_type):
    """Erkennt Zutaten per Vision-Modell; API-Schlüssel bleibt serverseitig."""
    api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
    if not api_key:
        raise RuntimeError("Kein OPENAI_API_KEY hinterlegt.")

    from openai import OpenAI

    data_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode()}"
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-6-luna"),
        input=[{
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        "Erkenne essbare Zutaten im Bild. Schätze Mengen nur grob und "
                        "kennzeichne sie als Schätzung. Antworte ausschließlich als JSON "
                        'im Format {"items":[{"name":"Tomaten","amount":"ca. 3 Stück"}]}. '
                        "Erfinde keine Zutaten, die nicht sichtbar sind."
                    ),
                },
                {"type": "input_image", "image_url": data_url},
            ],
        }],
    )
    text = response.output_text.strip()
    # Falls das Modell ausnahmsweise JSON-Markdown zurückgibt:
    text = text.removeprefix("```json").removesuffix("```").strip()
    return json.loads(text)["items"]


def matching_recipes(available, max_minutes, vegetarian, favorites_only=False):
    available_set = {x.casefold() for x in available}
    pantry_set = {x.casefold() for x in st.session_state.always_available}
    results = []

    for recipe in RECIPES:
        if favorites_only and recipe["name"] not in st.session_state.favorites:
            continue
        if recipe["minutes"] > max_minutes:
            continue
        if vegetarian and not recipe["vegetarian"]:
            continue

        needed = {x.casefold() for x in recipe["ingredients"]}
        matched = needed & (available_set | pantry_set)
        missing = needed - (available_set | pantry_set)
        results.append((recipe, len(matched), missing))

    # Erst passende Rezepte; bei Gleichstand möglichst wenige fehlende Zutaten.
    results.sort(key=lambda row: (-row[1], len(row[2]), row[0]["minutes"]))
    return results


def show_recipes(available, max_minutes, vegetarian, favorites_only=False):
    results = matching_recipes(
        available, max_minutes, vegetarian, favorites_only
    )
    if not results:
        st.info("Keine Rezepte für diese Filter gefunden.")
        return

    exact = [r for r in results if not r[2]]
    if exact:
        st.subheader("Rezeptvorschläge")
        chosen = exact
    else:
        min_missing = min(len(r[2]) for r in results)
        chosen = [r for r in results if len(r[2]) == min_missing]
        st.subheader("Vorschläge mit möglichst wenigen Extras")
        st.caption("Kein Rezept passt vollständig – diese Vorschläge benötigen am wenigsten zusätzliche Zutaten.")

    for recipe, matched_count, missing in chosen:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### {recipe['name']}")
                st.caption(
                    f"🕒 {recipe['minutes']} Min. · "
                    f"{matched_count}/{len(recipe['ingredients'])} Zutaten vorhanden"
                )
            with col2:
                if st.button(
                    "♥" if recipe["name"] in st.session_state.favorites else "♡",
                    key=f"fav_{recipe['name']}_{favorites_only}",
                ):
                    if recipe["name"] in st.session_state.favorites:
                        st.session_state.favorites.remove(recipe["name"])
                    else:
                        st.session_state.favorites.append(recipe["name"])
                    st.rerun()

            if missing:
                st.warning("Fehlt noch: " + ", ".join(sorted(missing)))
            with st.expander("Zutaten und Zubereitung"):
                st.write("**Zutaten:** " + ", ".join(recipe["ingredients"]))
                st.write(recipe["steps"])
                st.link_button("Rezeptseite öffnen", recipe["url"])


st.title("🌿 Resteküche")
st.caption("Was ist noch da? Verwende Reste, statt sie wegzuwerfen.")

pages = ["Start", "Zutaten", "Favoriten", "Profil"]
nav_cols = st.columns(len(pages))
for col, page in zip(nav_cols, pages):
    if col.button(page, use_container_width=True):
        st.session_state.page = page

st.divider()

if st.session_state.page == "Start":
    st.header("Was ist noch da?")
    st.write("Fotografiere deine Zutaten und lass dir passende Rezepte vorschlagen.")

    upload = st.file_uploader(
        "Zutaten fotografieren oder Bild hochladen",
        type=["jpg", "jpeg", "png", "webp"],
    )
    if upload:
        st.image(upload, caption="Dein Zutatenfoto", use_container_width=True)
        if st.button("Zutaten mit KI erkennen", type="primary"):
            try:
                with st.spinner("Zutaten werden erkannt …"):
                    items = recognize_image(upload.getvalue(), upload.type)
                for item in items:
                    name = item.get("name", "").strip()
                    amount = item.get("amount", "Menge prüfen").strip()
                    if name:
                        st.session_state.ingredients[name] = amount
                st.success("Erkennung abgeschlossen. Bitte prüfe die geschätzten Mengen.")
                st.rerun()
            except Exception as error:
                st.error(f"Erkennung fehlgeschlagen: {error}")

    st.subheader("Erkannte Zutaten")
    if st.session_state.ingredients:
        cols = st.columns(3)
        for i, (name, amount) in enumerate(st.session_state.ingredients.items()):
            cols[i % 3].metric(name, amount)
    else:
        st.info("Füge Zutaten hinzu oder lade ein Foto hoch.")

    c1, c2 = st.columns(2)
    with c1:
        max_minutes = st.slider("Maximale Kochzeit", 10, 90, 30, step=5)
    with c2:
        vegetarian = st.toggle("Vegetarisch", value=False)

    show_recipes(
        list(st.session_state.ingredients),
        max_minutes,
        vegetarian,
    )

elif st.session_state.page == "Zutaten":
    st.header("Meine Zutaten")
    st.caption("Behalte den Überblick und bearbeite erkannte Mengen.")

    for name in list(st.session_state.ingredients):
        c1, c2, c3 = st.columns([2, 2, 1])
        c1.write(name)
        st.session_state.ingredients[name] = c2.text_input(
            f"Menge für {name}",
            st.session_state.ingredients[name],
            key=f"amount_{name}",
            label_visibility="collapsed",
        )
        if c3.button("🗑", key=f"delete_{name}"):
            del st.session_state.ingredients[name]
            st.rerun()

    with st.form("add_ingredient"):
        new_name = st.text_input("Zutat hinzufügen")
        new_amount = st.text_input("Menge, z. B. 2 Stück oder 100 g")
        if st.form_submit_button("＋ Zutat hinzufügen", type="primary"):
            if new_name.strip():
                st.session_state.ingredients[new_name.strip()] = new_amount.strip() or "Menge offen"
                st.rerun()

    st.subheader("Immer vorrätig")
    st.session_state.always_available = st.multiselect(
        "Diese Zutaten werden bei Rezepten als vorhanden behandelt",
        options=sorted(set(
            st.session_state.always_available
            + ["Salz", "Öl", "Zucker", "Pfeffer", "Essig"]
        )),
        default=st.session_state.always_available,
    )

elif st.session_state.page == "Favoriten":
    st.header("Meine Favoriten")
    st.caption("Deine gespeicherten Rezepte auf einen Blick.")
    show_recipes(
        list(st.session_state.ingredients),
        90,
        False,
        favorites_only=True,
    )

elif st.session_state.page == "Profil":
    st.header("Profil & Einstellungen")
    st.write("Gemeinsam retten wir Lebensmittel.")
    st.metric("Gerettete Zutaten", len(st.session_state.ingredients))
    st.subheader("Immer vorrätige Zutaten")
    st.write(", ".join(st.session_state.always_available) or "Keine ausgewählt")
    st.caption(
        "Die Zutaten- und Favoritendaten werden im aktuellen Streamlit-"
        "Sitzungszustand gehalten. Für dauerhafte Nutzerkonten brauchst du "
        "zusätzlich eine Datenbank und Authentifizierung."
    )
