import streamlit as st
from datetime import date
import sys, os

st.set_page_config(page_title="Simulation | Gutmann", page_icon="📈", layout="wide")

try:
    from src.style import (
        apply_gutmann_style,
        GUTMANN_LIGHT_TEXT,
        GUTMANN_DARK_GREEN,
        GUTMANN_SECONDARY_DARK,
        GUTMANN_ACCENT_GREEN
    )
    # Neue modulare Imports mit Tab_ Prefix
    from src import Tab_Startseite 
    from src import Tab_Simulation
    # Marktanalyse Import entfernt, da integriert

    apply_gutmann_style()

except ImportError as e:
    st.error(
        f"**FATALER FEHLER beim Import von `src`:** {e}. Stelle sicher, dass der 'src'-Ordner im selben Verzeichnis wie Startseite.py liegt."
    )
    st.stop()

# --- CSS ANPASSUNGEN (Global) ---
st.markdown(f"""
<style>
/* 1. Slider Style */
div[data-testid="stSliderTickBarMin"], div[data-testid="stSliderTickBarMax"], div[data-testid="stThumbValue"] {{
    font-size: 1.1em !important;
    font-weight: 600 !important;
}}
div[data-testid="stSlider"] div[data-baseweb="slider"] {{
    padding-top: 10px;
}}

/* 2. Fixe Settings: Variable Breite & Größere Schrift */
.fixed-settings-container {{
    background-color: rgba(255,255,255,0.05);
    padding: 10px 20px;
    border-radius: 6px;
    border: 1px solid rgba(179, 212, 99, 0.2);
    margin-bottom: 20px;
    display: inline-flex;
    align-items: center;
    gap: 15px;
    flex-wrap: wrap;
    width: fit-content;
}}
.fixed-label-main {{
    font-size: 1.2rem;
    font-weight: 700;
    color: #FFFFFF;
    margin-right: 5px;
}}
.fixed-val {{
    font-size: 1.0rem;
    color: #E0E0E0;
    background-color: rgba(0,0,0,0.3);
    padding: 4px 12px;
    border-radius: 4px;
}}
.fixed-val strong {{
    color: {GUTMANN_ACCENT_GREEN};
}}

/* 3. Labels der Radio Buttons (Tabs) vergrößern */
div[data-testid="stRadio"] label p {{
    font-size: 1.3rem !important; 
    font-weight: 600 !important;
}}

/* 4. Custom Info Boxen für Startseite */
.gutmann-box {{
    background-color: {GUTMANN_SECONDARY_DARK};
    border-left: 5px solid {GUTMANN_ACCENT_GREEN};
    padding: 20px;
    border-radius: 5px;
    margin-bottom: 20px;
    color: {GUTMANN_LIGHT_TEXT};
}}
.gutmann-box h4 {{
    color: {GUTMANN_ACCENT_GREEN};
    margin-top: 0;
}}
</style>
""", unsafe_allow_html=True)


# --- SESSION STATE INITIALISIERUNG ---
if "main_nav" not in st.session_state:
    st.session_state.main_nav = "Startseite"
if "sim_sub_nav_state" not in st.session_state:
    st.session_state.sim_sub_nav_state = "Historische Simulation"

# Datum Init
if "sim_start_date" not in st.session_state:
    st.session_state.sim_start_date = date(2020, 1, 1)
if "sim_end_date" not in st.session_state:
    st.session_state.sim_end_date = date.today()

# Katalog & Assets Init
if "katalog_auswahl" not in st.session_state:
    st.session_state.katalog_auswahl = "Bitte wählen..."
if "assets" not in st.session_state:
    st.session_state.assets = [
        {"Name": "Apple Aktie", "ISIN / Ticker": "US0378331005", "Einmalerlag (€)": 500.0, "Sparbetrag (€)": 50.0, "Spar-Intervall": "monatlich"},
    ]

# Globale Parameter Init
if "cost_ausgabe" not in st.session_state:
    st.session_state.cost_ausgabe = 2.0
if "cost_management" not in st.session_state:
    st.session_state.cost_management = 2.0
if "cost_depot" not in st.session_state:
    st.session_state.cost_depot = 50.0
if "inflation_slider" not in st.session_state:
    st.session_state.inflation_slider = 3.0

# Prognose Parameter Init
if "prognose_jahre" not in st.session_state:
    st.session_state.prognose_jahre = 5 

# Daten-Container Init
if "simulations_daten" not in st.session_state:
    st.session_state.simulations_daten = None
if "prognose_daten" not in st.session_state:
    st.session_state.prognose_daten = None
if "historical_returns_pa" not in st.session_state:
    st.session_state.historical_returns_pa = {}
if "asset_final_values" not in st.session_state:
    st.session_state.asset_final_values = {}
if "prognosis_assumptions_pa" not in st.session_state:
    st.session_state.prognosis_assumptions_pa = {}


# --- HAUPT-NAVIGATION ---
# Feedback: Marktanalyse Tab entfernt, da nun integriert
st.radio(" ", options=["Startseite", "Simulation"], key="main_nav", horizontal=True)


# --- VIEW LOGIK (ROUTING) ---
if st.session_state.main_nav == "Startseite":
    Tab_Startseite.render()

elif st.session_state.main_nav == "Simulation":
    Tab_Simulation.render()