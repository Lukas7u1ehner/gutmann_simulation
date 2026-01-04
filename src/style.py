import streamlit as st
import base64
import os

def get_image_as_base64(path):
    if not os.path.exists(path):
        st.error(f"Logo-Datei nicht gefunden unter: {path}")
        return ""
    try:
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return f"data:image/png;base64,{encoded_string}"
    except Exception as e:
        st.error(f"Fehler beim Laden des Logos: {e}")
        return ""

LOGO_PATH = "assets/gutmann_logo.png"
GUTMANN_LOGO_URL = get_image_as_base64(LOGO_PATH)

# Definierte Farben (werden unten für das 'Fixed Theme' genutzt)
GUTMANN_DARK_GREEN = "#25342F"
GUTMANN_ACCENT_GREEN = "#B3D463"
GUTMANN_LIGHT_TEXT = "#E0E0E0"  # Heller gemacht für besseren Kontrast
GUTMANN_SECONDARY_DARK = "#3E524D"

def apply_gutmann_style():
    # Wir injizieren CSS, das die globalen Variablen (:root) überschreibt.
    # Damit wird der Light-Mode des Browsers effektiv "deaktiviert" für unsere App.
    st.markdown(f"""
    <style>
    
    /* --- 1. GLOBALEN THEME-OVERRIDE (Light Mode Killer) --- */
    :root {{
        --primary-color: {GUTMANN_ACCENT_GREEN};
        --background-color: {GUTMANN_DARK_GREEN};
        --secondary-background-color: {GUTMANN_SECONDARY_DARK};
        --text-color: {GUTMANN_LIGHT_TEXT};
        --font: "Source Sans Pro", sans-serif;
    }}

    /* Erzwingt dunklen Hintergrund für die gesamte App, egal was der Browser sagt */
    .stApp {{
        background-color: {GUTMANN_DARK_GREEN} !important;
        color: {GUTMANN_LIGHT_TEXT} !important;
    }}

    div[data-testid="stAppViewContainer"] > section > div:first-child {{
        padding-top: 0px !important;
    }}

    [data-testid="stSidebar"] {{
        display: none;
    }}
    
    /* --- 2. RADIO BUTTONS (STANDARD: TABS für Navigation) --- */
    /* Dies stellt das ursprüngliche Tab-Design für die Hauptnavigation sicher */
    
    div[data-testid="stRadio"] > div[role="radiogroup"] {{
        display: flex;
        justify-content: center;
        width: 100%;
        margin-top: 15px;
        margin-bottom: -10px;
        gap: 0px; 
    }}

    div[data-testid="stRadio"] > div[role="radiogroup"] > div {{
        display: contents;
    }}

    div[data-testid="stRadio"] div[role="radiogroup"] input[type="radio"] {{
        display: none !important;
    }}
    div[data-testid="stRadio"] div[role="radiogroup"] label::before {{
        display: none !important;
    }}
    div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child {{
        display: none !important;
    }}

    /* Standard Tab-Style (Reiter für Hauptmenü) */
    div[data-testid="stRadio"] div[role="radiogroup"] label {{
        display: inline-block;
        background-color: {GUTMANN_SECONDARY_DARK} !important;
        color: {GUTMANN_LIGHT_TEXT} !important;
        padding: 10px 24px;
        border-radius: 5px 5px 0 0 !important; /* Runde Ecken nur oben */
        margin: 0 3px !important; /* Abstand zwischen Tabs */
        border: 1px solid {GUTMANN_DARK_GREEN} !important;
        border-bottom: none !important;
        transition: all 0.2s ease;
        cursor: pointer;
        font-weight: 500;
        text-align: center;
    }}

    /* Text im Tab */
    div[data-testid="stRadio"] div[role="radiogroup"] label p {{
        color: {GUTMANN_LIGHT_TEXT} !important;
        margin: 0 !important;
    }}

    div[data-testid="stRadio"] div[role="radiogroup"] label:hover {{
        background-color: {GUTMANN_DARK_GREEN} !important;
    }}

    /* Aktiver Tab */
    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input[type="radio"]:checked) {{
        background-color: {GUTMANN_ACCENT_GREEN} !important;
        color: {GUTMANN_DARK_GREEN} !important;
        font-weight: bold;
        border-color: {GUTMANN_ACCENT_GREEN} !important;
    }}
    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input[type="radio"]:checked) p {{
        color: {GUTMANN_DARK_GREEN} !important;
        font-weight: bold !important;
    }}


    /* --- 3. SPEZIAL: MARKTPHASEN CONTROL (Segmented Control) --- */
    /* Überschreibt den Style NUR für das Radio mit Label "Marktphasen anzeigen" */
    
    div[role="radiogroup"][aria-label="Marktphasen anzeigen"] {{
        justify-content: flex-start !important;
        width: fit-content !important;
        margin-top: 0 !important;
        gap: 0 !important;
    }}

    /* Basis Style für die Segmente (Ja/Nein) */
    div[role="radiogroup"][aria-label="Marktphasen anzeigen"] label {{
        background-color: {GUTMANN_SECONDARY_DARK} !important;
        border-radius: 0 !important; /* Keine Reiter-Form, sondern flach */
        margin: 0 !important; /* Kein Abstand zwischen Ja und Nein */
        padding: 3px 0px !important; /* DÜNNER: Wenig padding oben/unten */
        width: 60px !important; /* FIXE BREITE: Beide gleich groß */
        border: 1px solid {GUTMANN_ACCENT_GREEN} !important;
        border-right: none !important; /* Rechten Rand entfernen für Verbindung */
        border-bottom: 1px solid {GUTMANN_ACCENT_GREEN} !important;
        justify-content: center !important; /* Text zentrieren */
        align-items: center !important;
        display: flex !important;
    }}

    /* Erstes Element (Ja): Links leicht abgerundet */
    div[role="radiogroup"][aria-label="Marktphasen anzeigen"] label:first-of-type {{
        border-top-left-radius: 4px !important;
        border-bottom-left-radius: 4px !important;
    }}

    /* Letztes Element (Nein): Rechts leicht abgerundet & Rand rechts wieder da */
    div[role="radiogroup"][aria-label="Marktphasen anzeigen"] label:last-of-type {{
        border-top-right-radius: 4px !important;
        border-bottom-right-radius: 4px !important;
        border-right: 1px solid {GUTMANN_ACCENT_GREEN} !important;
    }}
    
    /* Aktives Segment */
    div[role="radiogroup"][aria-label="Marktphasen anzeigen"] label:has(input[type="radio"]:checked) {{
        background-color: {GUTMANN_ACCENT_GREEN} !important;
        z-index: 1;
    }}
    
    /* Text im Control */
    div[role="radiogroup"][aria-label="Marktphasen anzeigen"] label p {{
        font-size: 0.9rem !important; /* Etwas kleinere Schrift passend zum dünnen Balken */
        line-height: 1 !important;
    }}


    /* --- 4. TEXT HEADERS --- */
    h1, h2, h3, h4, h5, h6 {{
        color: {GUTMANN_LIGHT_TEXT} !important;
    }}
    
    label[data-testid="stWidgetLabel"] p {{
        color: {GUTMANN_LIGHT_TEXT} !important;
    }}
    div[data-testid="stCheckbox"] label span p, 
    div[data-testid="stCheckbox"] label p {{
        color: {GUTMANN_LIGHT_TEXT} !important;
    }}

    /* --- 5. BUTTONS (Startseite & Simulation) --- */
    .stButton > button {{
        background-color: {GUTMANN_ACCENT_GREEN} !important;
        color: {GUTMANN_DARK_GREEN} !important;
        border-radius: 5px;
        border: none !important;
        padding: 10px 20px;
        font-weight: bold !important;
        opacity: 1 !important;
    }}
    
    .stButton > button[kind="primary"], 
    .stButton > button[data-testid="baseButton-primary"] {{
        background-color: {GUTMANN_ACCENT_GREEN} !important;
        border: none !important;
    }}

    .stButton > button p, 
    .stButton > button div,
    .stButton > button span,
    div[data-testid="stButton"] button p {{
        color: {GUTMANN_DARK_GREEN} !important;
        font-weight: bold !important;
        fill: {GUTMANN_DARK_GREEN} !important;
    }}

    .stButton > button:focus {{
        outline: none;
        box-shadow: none;
    }}

    /* --- 6. SEKUNDÄRE BUTTONS (Kosten Einstellungen) --- */
    .stButton > button[kind="secondary"] {{
        background-color: {GUTMANN_SECONDARY_DARK} !important;
        color: {GUTMANN_LIGHT_TEXT} !important;
        border: 1px solid {GUTMANN_ACCENT_GREEN} !important;
    }}
    .stButton > button[kind="secondary"] p {{
        color: {GUTMANN_LIGHT_TEXT} !important;
    }}

    /* --- 7. INPUT FELDER & DROPDOWNS --- */
    .stSelectbox > div > div, 
    .stTextInput > div > div > input,
    .stNumberInput > div > input {{
        background-color: {GUTMANN_SECONDARY_DARK} !important;
        color: {GUTMANN_LIGHT_TEXT} !important;
        -webkit-text-fill-color: {GUTMANN_LIGHT_TEXT} !important;
        border-color: {GUTMANN_SECONDARY_DARK} !important;
        caret-color: {GUTMANN_ACCENT_GREEN} !important;
    }}
    
    .stTextInput input::placeholder {{
        color: #8c9e99 !important;
        opacity: 1 !important;
    }}
    
    .stTextInput label, .stNumberInput label, .stSelectbox label, .stDateInput label, .stSlider label {{
        color: {GUTMANN_LIGHT_TEXT} !important;
    }}
    
    ul[data-testid="stSelectboxVirtualDropdown"] {{
        background-color: {GUTMANN_SECONDARY_DARK} !important;
    }}
    ul[data-testid="stSelectboxVirtualDropdown"] li {{
        background-color: {GUTMANN_SECONDARY_DARK} !important;
        color: {GUTMANN_LIGHT_TEXT} !important;
    }}
    ul[data-testid="stSelectboxVirtualDropdown"] li:hover {{
        background-color: {GUTMANN_DARK_GREEN} !important;
    }}

    /* --- 8. TABELLEN --- */
    div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {{
        background-color: {GUTMANN_SECONDARY_DARK} !important;
        border: 1px solid {GUTMANN_DARK_GREEN};
        --st-background-color: {GUTMANN_SECONDARY_DARK};
        --st-secondary-background-color: {GUTMANN_DARK_GREEN};
        --st-text-color: {GUTMANN_LIGHT_TEXT};
        --st-font-family: "Source Sans Pro", sans-serif;
    }}
    
    .stDataFrame thead th {{
        background-color: {GUTMANN_DARK_GREEN} !important;
        color: {GUTMANN_ACCENT_GREEN} !important;
        font-weight: bold;
        border-bottom: 1px solid {GUTMANN_ACCENT_GREEN} !important;
    }}
    .stDataFrame tbody tr {{
        background-color: {GUTMANN_SECONDARY_DARK} !important;
        color: {GUTMANN_LIGHT_TEXT} !important;
    }}
    .stDataFrame tbody tr:hover {{
        background-color: {GUTMANN_DARK_GREEN} !important;
    }}

    /* --- 9. SONSTIGES --- */
    .stSlider > div > div > div[data-testid="stThumbValue"] {{
        background-color: {GUTMANN_ACCENT_GREEN} !important;
        color: {GUTMANN_DARK_GREEN} !important;
    }}
    .stSlider > div > div > div[data-testid="stProgress"] > div {{
        background-color: {GUTMANN_ACCENT_GREEN} !important;
    }}
    
    div[data-testid="stMarkdownContainer"] p {{
        color: {GUTMANN_LIGHT_TEXT} !important;
    }}

    .streamlit-expanderHeader {{
        background-color: {GUTMANN_SECONDARY_DARK} !important;
        color: {GUTMANN_LIGHT_TEXT} !important;
    }}
    .streamlit-expanderHeader p {{
        color: {GUTMANN_LIGHT_TEXT} !important;
    }}
    .streamlit-expanderContent {{
        background-color: {GUTMANN_DARK_GREEN} !important;
        color: {GUTMANN_LIGHT_TEXT} !important;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] > div > div {{
        border-color: {GUTMANN_ACCENT_GREEN} !important;
    }}

    div[data-testid="stMetric"] {{
        background-color: {GUTMANN_SECONDARY_DARK} !important;
        padding: 5px 10px 5px 10px;
        border-radius: 2px;
        margin-bottom: 2px;
        color: {GUTMANN_LIGHT_TEXT} !important;
    }}
    div[data-testid="stMetric"] label {{
        color: {GUTMANN_LIGHT_TEXT} !important;
    }}
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
        color: {GUTMANN_ACCENT_GREEN} !important;
        font-size: 2.0em;
    }}

    </style>
    """, unsafe_allow_html=True)

def add_gutmann_logo():
    pass