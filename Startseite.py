import streamlit as st
from datetime import date
import sys, os

#  PERMANENTER SSL-FIX (vor allen anderen Imports) 
try:
    import certifi
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    os.environ['SSL_CERT_FILE'] = certifi.where()
except ImportError:
    pass
# 

st.set_page_config(page_title="Simulation | Gutmann", page_icon="📈", layout="wide")

#  CHECKOUT RESET LOGIC 
if st.session_state.get("pending_reset"):
    # Widget-Keys sicher löschen (sodass sie beim nächsten Render neu initialisiert werden)
    keys_to_reset = ["editable_budget", "editable_einmalerlag", "editable_sparrate", "main_nav"]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]
            
    # Handover-Daten resetten, damit Simulation neu lädt
    if "handover_data" in st.session_state:
        del st.session_state["handover_data"]
        
    # URL-Parameter löschen, damit bei Rerun nicht wieder die alten Daten geladen werden
    st.query_params.clear()
        
    st.session_state["pending_reset"] = False
    st.rerun() # Rerun um sicherzustellen, dass der State sauber ist

#  URL-PARAMETER-HANDLING (Tool A -> Tool B Simulation) 
try:
    query_params = st.query_params
    
    # Parameter extrahieren (mit Fallback auf Dummy-Daten)
    advisor_name = query_params.get("advisorName", "MSc Daniela Delipetar")
    client_name = query_params.get("clientName", "Tamara Wolna")  
    budget_str = query_params.get("budget", "0")
    einmalerlag_str = query_params.get("einmalerlag", "0") 
    portfolio_type = query_params.get("portfolioType", None)  
    savings_rate_str = query_params.get("savings_rate", query_params.get("savingsRate", "0"))
    savings_interval = query_params.get("savingsInterval", "monatlich")
    
    # Custom Gewichtungen parsen 
    custom_weights = {}
    for key in query_params.keys():
        if key.startswith("weight_"):
            ticker = key.replace("weight_", "")
            try:
                weight_value = float(query_params.get(key, "0"))
                if 0 <= weight_value <= 100:
                    custom_weights[ticker] = weight_value
            except ValueError:
                pass  # Ignoriere ungültige Gewichtungen
    
    # Konvertierung zu Zahlen
    try:
        budget = float(budget_str)
        einmalerlag = float(einmalerlag_str)
        savings_rate = float(savings_rate_str)
    except ValueError:
        budget = 0.0
        einmalerlag = 0.0
        savings_rate = 0.0
    
    # In Session State speichern (nur einmal beim ersten Laden)
    if "handover_data" not in st.session_state:
        st.session_state.handover_data = {
            "advisor": advisor_name,
            "client": client_name,
            "budget": budget,
            "einmalerlag": einmalerlag,
            "portfolio_type": portfolio_type,
            "savings_rate": savings_rate,
            "savings_interval": savings_interval,
            "custom_weights": custom_weights,
            "preloaded": False
        }
except Exception as e:
    # Fallback bei Fehler: Dummy-Daten setzen
    if "handover_data" not in st.session_state:
        st.session_state.handover_data = {
            "advisor": "MsC Daniel Delipetar",
            "client": "Tamara Wolna",
            "budget": 500000.0,
            "einmalerlag": 300000.0,
            "portfolio_type": None,
            "savings_rate": 2000.0,
            "savings_interval": "monatlich",
            "custom_weights": {},
            "preloaded": False
        }

try:
    from src.style import (
        apply_gutmann_style,
        GUTMANN_LIGHT_TEXT,
        GUTMANN_DARK_GREEN,
        GUTMANN_SECONDARY_DARK,
        GUTMANN_ACCENT_GREEN
    )
    from src import Tab_Startseite 
    from src import Tab_Simulation

    apply_gutmann_style()

except ImportError as e:
    st.error(
        f"**FATALER FEHLER beim Import von `src`:** {e}. Stelle sicher, dass der 'src'-Ordner im selben Verzeichnis wie Startseite.py liegt."
    )
    st.stop()

#  CSS ANPASSUNGEN (Global) 
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

#  ACCESSIBILITY: JavaScript für Tab-Navigation 
import streamlit.components.v1 as components
components.html("""
<script>
function makeRadioLabelsAccessible() {
    const parentDoc = window.parent.document;
    // NUR die Labels im radiogroup, NICHT das stWidgetLabel darüber
    const labels = parentDoc.querySelectorAll('div[data-testid="stRadio"] div[role="radiogroup"] label');
    labels.forEach(function(label) {
        if (!label.hasAttribute('tabindex')) {
            label.setAttribute('tabindex', '0');
        }
        if (!label.dataset.a11yEnhanced) {
            label.dataset.a11yEnhanced = 'true';
            label.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    label.click();
                }
            });
        }
    });
}
makeRadioLabelsAccessible();
setInterval(makeRadioLabelsAccessible, 500);

// Dieses iframe selbst aus dem Tab-Flow entfernen
if (window.frameElement) {
    window.frameElement.setAttribute('tabindex', '-1');
    window.frameElement.style.outline = 'none';
    window.frameElement.style.border = 'none';
}
</script>
""", height=0)


#  SESSION STATE INITIALISIERUNG 
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
    st.session_state.assets = []

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
    st.session_state.prognose_jahre = 15 

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


#  HAUPT-NAVIGATION 
st.radio("Hauptnavigation", options=["Startseite", "Simulation"], key="main_nav", horizontal=True, label_visibility="collapsed", help="Navigation: Wechseln Sie zwischen Startseite und Simulation")


#  VIEW LOGIK (ROUTING) 
if st.session_state.main_nav == "Startseite":
    Tab_Startseite.render()

elif st.session_state.main_nav == "Simulation":
    Tab_Simulation.render()