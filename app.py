import streamlit as st
from PIL import Image
from pathlib import Path
import json
from recipe_engine import load_recipes, find_recipes, ingredient_match
from vision_adapter import recognize_ingredients

st.set_page_config(page_title="Resteküche", page_icon="🥬", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
:root { --green:#174b38; --green2:#e9f1e9; --orange:#f4772b; --cream:#fbf8f1; }
.stApp { background:var(--cream); color:#203b2f; font-family:'DM Sans',sans-serif; }
.block-container { max-width:1120px; padding-top:1.2rem; }
h1,h2,h3 { font-family:'Playfair Display',serif !important; color:var(--green) !important; }
.brand { color:var(--green); font-family:'Playfair Display',serif; font-size:1.7rem; font-weight:700; }
.hero { background:linear-gradient(115deg,#174b38,#28664c); border-radius:22px; padding:28px; color:white; }
.hero h1 { color:white !important; margin:0; }
.hero p { color:#e6efe8; margin-bottom:0; }
div.stButton > button[kind="primary"] { background:var(--orange); border:0; color:white; border-radius:12px; font-weight:700; }
div.stButton > button { border-radius:12px; }
.ingredient { background:white; border:1px solid #e9e5dc; padding:12px; border-radius:14px; }
.recipe { background:white; border:1px solid #eee9df; border-radius:18px; padding:16px; margin-bottom:12px; }
.small-muted { color:#778078; font-size:.88rem; }
[data-testid="stSidebar"] { background:#f1f3eb; }
</style>
""", unsafe_allow_html=True)

DEFAULT_PANTRY = ["Salz", "Pfeffer", "Öl", "Zucker", "Essig"]
if "ingredients" not in st.session_state:
    st.session_state.ingredients = [
        {"name":"Tomaten"}, {"name":"Paprika"},
        {"name":"Eier"}, {"name":"Spinat"}
    ]
if "pantry" not in st.session_state: st.session_state.pantry = DEFAULT_PANTRY.copy()
if "favorites" not in st.session_state: st.session_state.favorites = []
if "page" not in st.session_state: st.session_state.page = "Start"

with st.sidebar:
    st.markdown('<div class="brand">🌿 Resteküche</div>', unsafe_allow_html=True)
    st.caption("Aus Resten wird Lieblingsessen.")
    page = st.radio("Navigation", ["Start","Zutaten","Favoriten","Profil & Einstellungen"], label_visibility="collapsed")
    st.session_state.page = page
    st.divider()
    st.caption("Dein Beitrag")
    st.metric("Zutaten im Vorrat", len(st.session_state.ingredients))
    st.caption("Gemeinsam retten wir Lebensmittel.")

def render_ingredient_editor():
    st.subheader("Meine Zutaten")
    st.caption("Bearbeite Mengen oder entferne Zutaten, die du nicht mehr hast.")
    for i, item in enumerate(st.session_state.ingredients):
        c1,c2 = st.columns([5,1])
        with c1: st.write(f"🥬 **{item['name']}**")
        with c2:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.ingredients.pop(i); st.rerun()
    with st.expander("＋ Zutat hinzufügen"):
        with st.form("add_ingredient", clear_on_submit=True):
            name = st.text_input("Zutat")
            if st.form_submit_button("Hinzufügen", type="primary") and name.strip():
                st.session_state.ingredients.append({"name":name.strip()})
                st.rerun()

def recipe_cards(recipes):
    if not recipes:
        st.info("Noch keine passenden Rezepte gefunden. Probiere „Wenig Extras“ oder passe deine Zutaten an.")
        return
    for r in recipes:
        have, total, missing = ingredient_match(r, st.session_state.ingredients, st.session_state.pantry)
        with st.container(border=True):
            a,b = st.columns([1,2])
            with a:
                if r.get("image"):
                    st.image(r["image"], use_container_width=True)
                else:
                    st.markdown(f"<div style='font-size:4rem;text-align:center;background:#f4f1e8;border-radius:14px;padding:20px'>{r.get('emoji','🍲')}</div>", unsafe_allow_html=True)
            with b:
                st.markdown(f"### {r['name']}")
                st.caption(f"⏱️ {r['minutes']} Min.　 ·　 {r['category']}　 ·　 {have}/{total} Zutaten vorhanden")
                st.progress(have/total if total else 1)
                st.write(r.get("description",""))
                if missing:
                    st.caption("Fehlt noch: " + ", ".join(missing))
                else:
                    st.success("Du hast alles dafür da!")
                x,y = st.columns([1,1])
                with x:
                    if st.button("Rezept ansehen", key=f"open_{r['id']}", type="primary"):
                        st.session_state["selected_recipe"] = r["id"]
                with y:
                    label = "♥ Gespeichert" if r["id"] in st.session_state.favorites else "♡ Merken"
                    if st.button(label, key=f"fav_{r['id']}"):
                        if r["id"] in st.session_state.favorites: st.session_state.favorites.remove(r["id"])
                        else: st.session_state.favorites.append(r["id"])
                        st.rerun()
                if st.session_state.get("selected_recipe") == r["id"]:
                    st.markdown("**Zutaten**")
                    for ing in r["ingredients"]: st.write(f"• {ing}")
                    st.markdown("**Zubereitung**")
                    for n, step in enumerate(r["steps"],1): st.write(f"{n}. {step}")
                    if r.get("source"): st.caption(f"Quelle: {r['source']}")

recipes = load_recipes()
st.markdown('<div class="brand">🌿 Resteküche</div>', unsafe_allow_html=True)

if page == "Start":
    st.markdown('<div class="hero"><h1>Was ist noch da?</h1><p>Fotografiere deine Zutaten und entdecke passende Rezepte – bevor Lebensmittel im Müll landen.</p></div>', unsafe_allow_html=True)
    st.write("")
    left,right = st.columns([1,1])
    with left:
        st.subheader("📷 Zutaten fotografieren")
        uploads = st.file_uploader("Foto vom Kühlschrank, Tisch oder Vorrat hochladen", type=["png","jpg","jpeg","webp"], accept_multiple_files=True)
        if uploads:
            for up in uploads:
                st.image(up, caption=up.name, use_container_width=True)
            if st.button("Zutaten mit KI erkennen", type="primary", use_container_width=True):
                with st.spinner("Die KI schaut sich deine Zutaten an …"):
                    detected = []
                    for up in uploads:
                        img = Image.open(up).convert("RGB")
                        detected.extend(recognize_ingredients(img))
                    # Merge by normalized name
                    merged = {}
                    for d in detected:
                        name = d.get("name","").strip()
                        if name:
                            merged[name.lower()] = {"name":name}
                    if merged:
                        st.session_state.ingredients = list(merged.values())
                        st.success(f"{len(merged)} Zutaten erkannt.")
                        st.rerun()
                    else:
                        st.warning("Es wurden keine Zutaten erkannt. Du kannst sie unten manuell ergänzen.")
        st.caption("Tipp: Gute Beleuchtung und möglichst wenig verdeckte Lebensmittel verbessern die Erkennung.")
    with right:
        st.subheader("🧺 Erkannte Zutaten")
        render_ingredient_editor()
    st.divider()
    st.subheader("Rezeptvorschläge")
    f1,f2,f3 = st.columns(3)
    with f1: max_time = st.selectbox("Zubereitungszeit", ["Beliebig","Unter 20 Min.","Unter 30 Min.","Unter 45 Min."])
    with f2: diet = st.selectbox("Ernährung", ["Alle","Vegetarisch","Vegan"])
    with f3: low_waste = st.checkbox("Wenig Extras bevorzugen", value=False)
    limit = {"Beliebig":999,"Unter 20 Min.":20,"Unter 30 Min.":30,"Unter 45 Min.":45}[max_time]
    found = find_recipes(recipes, st.session_state.ingredients, st.session_state.pantry, max_minutes=limit, diet=diet, low_extra=low_waste)
    if not found and not low_waste:
        st.info("Keine vollständige Übereinstimmung? Hier sind Ideen mit möglichst wenigen zusätzlichen Zutaten.")
        found = find_recipes(recipes, st.session_state.ingredients, st.session_state.pantry, max_minutes=limit, diet=diet, low_extra=True)
    recipe_cards(found[:6])

elif page == "Zutaten":
    render_ingredient_editor()
    st.subheader("Immer vorrätig")
    st.caption("Diese Basics zählen bei Rezeptvorschlägen als vorhanden.")
    pantry_options = ["Salz","Pfeffer","Öl","Olivenöl","Zucker","Essig","Mehl","Nudeln","Reis","Knoblauch","Zwiebeln","Brühe","Sojasauce"]
    selected = st.multiselect("Vorratszutaten", pantry_options, default=[x for x in st.session_state.pantry if x in pantry_options])
    st.session_state.pantry = selected

elif page == "Favoriten":
    st.subheader("Meine Favoriten")
    favs = [r for r in recipes if r["id"] in st.session_state.favorites]
    recipe_cards(favs)

else:
    st.subheader("Profil & Einstellungen")
    st.markdown("### 🌱 Gemeinsam retten wir Lebensmittel.")
    st.write("Passe deine Vorlieben an, damit die Vorschläge besser zu dir passen.")
    st.session_state["diet_pref"] = st.selectbox("Ernährungsweise",["Alles","Vegetarisch","Vegan"], index=0)
    st.session_state["allergies"] = st.text_input("Unverträglichkeiten (kommagetrennt)", value=st.session_state.get("allergies",""))
    st.session_state["portions"] = st.number_input("Standard-Portionen", min_value=1, max_value=12, value=2)
    st.checkbox("KI-Zutaten-Erkennung aktivieren", value=True, key="vision_enabled")
    st.caption("Fotos werden in dieser Demo nur während der aktuellen Sitzung verarbeitet. Für produktiven Betrieb bitte Speicher- und Datenschutzkonzept ergänzen.")

st.markdown("---")
st.caption("Resteküche · Weniger wegwerfen. Leckerer essen.")
