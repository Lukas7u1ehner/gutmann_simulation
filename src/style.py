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

GUTMANN_DARK_GREEN = "#25342F"
GUTMANN_ACCENT_GREEN = "#B3D463"
GUTMANN_LIGHT_TEXT = "#D1D1D1"
GUTMANN_SECONDARY_DARK = "#3E524D"

def apply_gutmann_style():
    st.markdown(f"""
    <style>

    div[data-testid="stAppViewContainer"] > section > div:first-child {{
        padding-top: 0px !important;
    }}

    [data-testid="stSidebar"] {{
        display: none;
    }}

    div[data-testid="stRadio"] > div[role="radiogroup"] {{
        display: flex;
        justify-content: center;
        width: 100%;
        margin-top: 15px;
        margin-bottom: -10px;
    }}

    div[data-testid="stRadio"] > div[role="radiogroup"] > div {{
        display: contents;
    }}

    div[data-testid="stRadio"] div[role="radiogroup"] input[type="radio"] {{
        display: none !important;
    }}

    div[data-testid="stRadio"] div[role="radiogroup"] label::before {{
        content: none !important;
        display: none !important;
        width: 0 !important;
        height: 0 !important;
    }}

    div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child {{
        display: none !important;
    }}

    div[data-testid="stRadio"] div[role="radiogroup"] label {{
        display: inline-block;
        background-color: {GUTMANN_SECONDARY_DARK};
        color: {GUTMANN_LIGHT_TEXT};
        padding: 10px 24px;
        border-radius: 5px 5px 0 0;
        margin: 0 3px;
        border: 1px solid {GUTMANN_DARK_GREEN};
        border-bottom: none;
        transition: all 0.2s ease;
        cursor: pointer;
        font-weight: 500;
        transform: translateY(2px);
    }}

    div[data-testid="stRadio"] div[role="radiogroup"] label:hover {{
        background-color: {GUTMANN_DARK_GREEN};
    }}

    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input[type="radio"]:checked) {{
        background-color: {GUTMANN_ACCENT_GREEN};
        color: {GUTMANN_DARK_GREEN};
        font-weight: bold;
        border-color: {GUTMANN_ACCENT_GREEN};
        transform: translateY(0);
    }}

    body {{
        background-color: {GUTMANN_DARK_GREEN};
        color: {GUTMANN_LIGHT_TEXT};
    }}
    .stApp {{
        background-color: {GUTMANN_DARK_GREEN};
        color: {GUTMANN_LIGHT_TEXT};
    }}

    h1, h2, h3, h4, h5, h6 {{
        color: {GUTMANN_LIGHT_TEXT};
    }}

    /* --- FEEDBACK-ANPASSUNG: Button Kontrast & Sichtbarkeit --- */
    .stButton > button {{
        background-color: {GUTMANN_ACCENT_GREEN} !important;
        color: {GUTMANN_DARK_GREEN} !important;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
        opacity: 1 !important; /* Verhindert ausgegrauten Look */
    }}
    .stButton > button:hover {{
        background-color: {GUTMANN_ACCENT_GREEN};
        filter: brightness(110%);
        color: {GUTMANN_DARK_GREEN} !important;
    }}
    .stButton > button:focus {{
        outline: none;
        box-shadow: 0 0 0 2px {GUTMANN_ACCENT_GREEN};
        color: {GUTMANN_DARK_GREEN} !important;
    }}
    .stButton > button p {{
        color: {GUTMANN_DARK_GREEN} !important;
    }}

    .stSelectbox > div > div, 
    .stTextInput > div > div > input,
    .stNumberInput > div > input {{
        background-color: {GUTMANN_SECONDARY_DARK};
        color: {GUTMANN_LIGHT_TEXT};
        border-color: {GUTMANN_SECONDARY_DARK};
    }}
    .stTextInput label, .stNumberInput label, .stSelectbox label, .stDateInput label, .stSlider label {{
        color: {GUTMANN_LIGHT_TEXT};
    }}

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
        background-color: {GUTMANN_DARK_GREEN};
    }}
    .stDataFrame thead th {{
        background-color: {GUTMANN_DARK_GREEN};
        color: {GUTMANN_ACCENT_GREEN};
        font-weight: bold;
    }}

    .stSlider > div > div > div[data-testid="stThumbValue"] {{
        background-color: {GUTMANN_ACCENT_GREEN};
        color: {GUTMANN_DARK_GREEN};
    }}
    .stSlider > div > div > div[data-testid="stProgress"] > div {{
        background-color: {GUTMANN_ACCENT_GREEN};
    }}

    .streamlit-expanderHeader {{
        background-color: {GUTMANN_SECONDARY_DARK};
        color: {GUTMANN_LIGHT_TEXT};
    }}
    .streamlit-expanderContent {{
        background-color: {GUTMANN_DARK_GREEN};
    }}

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
        font-size: 2.0em;
    }}

    </style>
    """, unsafe_allow_html=True)

def add_gutmann_logo():
    pass