# style.py
import streamlit as st
import base64  # (NEU) Importieren für die Bild-Kodierung
import os      # (NEU) Importieren, um den Pfad zu prüfen

# (UPDATE) Funktion, um das Logo zu laden und als Base64-String zurückzugeben
def get_image_as_base64(path):
    """Liest eine Bilddatei ein und gibt sie als Base64-kodierten String zurück."""
    if not os.path.exists(path):
        # Zeige einen Fehler in der App an, wenn das Logo fehlt
        st.error(f"Logo-Datei nicht gefunden unter: {path}")
        return ""
    try:
        with open(path, "rb") as image_file:
            # Lese die Datei, kodiere sie und dekodiere sie zu einem String
            encoded_string = base64.b64encode(image_file.read()).decode()
        # Gib den vollständigen Data-URI zurück
        return f"data:image/png;base64,{encoded_string}"
    except Exception as e:
        st.error(f"Fehler beim Laden des Logos: {e}")
        return ""

# Der Pfad zu deinem Logo
LOGO_PATH = "assets/gutmann_logo.png"
# (UPDATE) Die URL ist jetzt der Base64-kodierte Inhalt der Datei
GUTMANN_LOGO_URL = get_image_as_base64(LOGO_PATH) 

GUTMANN_DARK_GREEN = "#25342F" # Hintergrundfarbe
GUTMANN_ACCENT_GREEN = "#B3D463" # Akzentfarbe (wie dein gelber Button)
GUTMANN_LIGHT_TEXT = "#D1D1D1" # Helle Textfarbe
GUTMANN_SECONDARY_DARK = "#3E524D" # Sekundäres Dunkelgrün für Akzente

def apply_gutmann_style():
    st.markdown(f"""
    <style>
    /* Allgemeine Hintergrund- und Textfarben */
    body {{
        background-color: {GUTMANN_DARK_GREEN};
        color: {GUTMANN_LIGHT_TEXT};
    }}
    .stApp {{
        background-color: {GUTMANN_DARK_GREEN};
        color: {GUTMANN_LIGHT_TEXT};
    }}

    /* Header und Titel */
    h1, h2, h3, h4, h5, h6 {{
        color: {GUTMANN_LIGHT_TEXT};
    }}

    /* Buttons */
    .stButton > button {{
        background-color: {GUTMANN_ACCENT_GREEN};
        color: {GUTMANN_DARK_GREEN};
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }}
    .stButton > button:hover {{
        background-color: {GUTMANN_ACCENT_GREEN}; /* Bleibt gleich oder leicht dunkler */
        opacity: 0.9;
    }}
    .stButton > button:focus {{
        outline: none;
        box-shadow: 0 0 0 2px {GUTMANN_ACCENT_GREEN};
    }}

    /* Selectboxen, Text Inputs, Number Inputs (Hintergrund und Text) */
    .stSelectbox > div > div, 
    .stTextInput > div > div > input,
    .stNumberInput > div > input {{
        background-color: {GUTMANN_SECONDARY_DARK};
        color: {GUTMANN_LIGHT_TEXT};
        border-color: {GUTMANN_SECONDARY_DARK};
    }}
    /* Labels für Inputs */
    .stTextInput label, .stNumberInput label, .stSelectbox label, .stDateInput label, .stSlider label {{
        color: {GUTMANN_LIGHT_TEXT};
    }}

    /* st.data_editor (Hintergrund, Text, Header) */
    .stDataFrame, .stDataFrame thead th {{
        background-color: {GUTMANN_SECONDARY_DARK};
        color: {GUTMANN_LIGHT_TEXT};
        border-color: {GUTMANN_DARK_GREEN};
    }}
    .stDataFrame tbody tr {{
        background-color: {GUTMANN_SECONDARY_DARK};
        color: {GUTMANN_LIGHT_TEXT};
    }}
    .stDataFrame tbody tr:hover {{
        background-color: {GUTMANN_DARK_GREEN}; /* Etwas dunkler beim Hover */
    }}
    .stDataFrame thead th {{
        background-color: {GUTMANN_DARK_GREEN};
        color: {GUTMANN_ACCENT_GREEN};
        font-weight: bold;
    }}

    /* Slider */
    .stSlider > div > div > div[data-testid="stThumbValue"] {{
        background-color: {GUTMANN_ACCENT_GREEN};
        color: {GUTMANN_DARK_GREEN};
    }}
    .stSlider > div > div > div[data-testid="stProgress"] > div {{
        background-color: {GUTMANN_ACCENT_GREEN};
    }}
    
    /* Expander */
    .streamlit-expanderHeader {{
        background-color: {GUTMANN_SECONDARY_DARK};
        color: {GUTMANN_LIGHT_TEXT};
    }}
    .streamlit-expanderContent {{
        background-color: {GUTMANN_DARK_GREEN};
    }}
    
    /* (FIX) st.metric Anpassungen */
    div[data-testid="stMetric"] {{
        background-color: {GUTMANN_SECONDARY_DARK};
        padding: 5px 10px 5px 10px; 
        border-radius: 2px;
        margin-bottom: 2px; 
        color: {GUTMANN_LIGHT_TEXT};
    }}
    div[data-testid="stMetric"] label {{
        color: {GUTMANN_LIGHT_TEXT};
    }}
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
        color: {GUTMANN_ACCENT_GREEN};
        font-size: 2.0em; /* (UPDATE) Schriftgröße leicht reduziert */
    }}
    
    </style>
    """, unsafe_allow_html=True)

def add_gutmann_logo():
    # Logo in der Sidebar (für beide Seiten)
    st.sidebar.markdown(
        f"""
        <div style="margin-bottom: 40px; text-align: center;">
            <img src="{GUTMANN_LOGO_URL}" alt="Bank Gutmann Logo" style="width: 220px;">
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Logo auf der Startseite (nur für Startseite.py)
    # st.markdown wird jetzt in Startseite.py direkt aufgerufen

