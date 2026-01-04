import streamlit as st
from datetime import date
import base64
import time
import streamlit.components.v1 as components

def generate_checkout_csv(assets, handover_data, inputs):
    """
    Generiert einen CSV-String mit den aktuellen Portfolio-Daten.
    Enthält Kopfdaten (Kunde/Berater) und eine Liste der Positionen.
    """
    # 1. Header Info
    header = [
        f"Export-Datum;{date.today().strftime('%d.%m.%Y')}",
        f"Kunde;{handover_data.get('client','-')}",
        f"Berater;{handover_data.get('advisor','-')}",
        f"Budget;{inputs.get('budget',0)}",
        f"Einmalerlag;{inputs.get('einmalerlag',0)}",
        f"Sparrate;{inputs.get('sparrate',0)}",
        "" # Leerzeile
    ]
    
    # 2. Positionen
    cols = ["Name", "ISIN", "Gewichtung (%)", "Einmalerlag (EUR)", "Sparbetrag (EUR)", "Intervall"]
    data_rows = [";".join(cols)]
    
    for a in assets:
        row = [
            str(a.get("Name", "")),
            str(a.get("ISIN / Ticker", "")),
            str(a.get("Gewichtung (%)", 0)).replace(".", ","),
            str(a.get("Einmalerlag (€)", 0)).replace(".", ","),
            str(a.get("Sparbetrag (€)", 0)).replace(".", ","),
            str(a.get("Spar-Intervall", ""))
        ]
        data_rows.append(";".join(row))
        
    return "\n".join(header + data_rows)

def reset_simulation_state():
    """
    Setzt alle relevanten Simulation-States auf ihre Default-Werte zurück.
    """
    # 1. Assets leeren (Komplett leer, damit keine leere Zeile gerendert wird)
    st.session_state.assets = []
    
    # 2. Inputs zurücksetzen (DEFERRED)
    # WICHTIG: Wir können hier nicht 'editable_budget' etc. setzen, da diese an Widgets gebunden sind
    # und das Skript noch läuft ("StreamlitAPIException").
    # Stattdessen setzen wir ein Flag, das beim nächsten Laden von Startseite.py den Reset durchführt.
    st.session_state["pending_reset"] = True
    
    # 3. Berechnete Daten löschen
    st.session_state.simulations_daten = None
    st.session_state.prognose_daten = None
    st.session_state.historical_returns_pa = None
    st.session_state.prognosis_assumptions_pa = {}
    st.session_state.asset_final_values = {}
    
    # 4. Navigation zurück zur Startseite (DEFERRED via Startseite.py logic)
    # st.session_state.main_nav = "Startseite"  <-- verursacht API Exception
    # Sub-Nav resetten (optional, aber sauber)
    st.session_state.sim_sub_nav_state = "Historische Simulation"

def render_finish_button(key_suffix):
    """
    Rendert den 'Jetzt Abschließen' Button.
    Handled CSV-Generierung, JS-Download und anschließenden Reset+Redirect.
    """
    
    # CSS für Grünen Button (Success Green)
    st.markdown("""
    <style>
    div.stButton > button[key^='btn_finish'] {
        background-color: #28a745 !important;
        color: white !important;
        border: none;
        font-weight: bold;
    }
    div.stButton > button[key^='btn_finish']:hover {
        background-color: #218838 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("Jetzt Abschließen", key=f"btn_finish_{key_suffix}", use_container_width=True):
        # 1. Daten sammeln
        inputs = {
            "budget": st.session_state.editable_budget,
            "einmalerlag": st.session_state.editable_einmalerlag,
            "sparrate": st.session_state.editable_sparrate
        }
        
        # CSV String erzeugen
        csv_data = generate_checkout_csv(st.session_state.assets, st.session_state.handover_data, inputs)
        
        # 2. Download Trigger (JS)
        # utf-8-sig damit Excel Umlaute richtig anzeigt
        b64 = base64.b64encode(csv_data.encode('utf-8-sig')).decode()
        filename = f"Gutmann_Abschluss_{date.today()}.csv"
        
        js = f"""
        <script>
            var link = document.createElement('a');
            link.href = 'data:text/csv;base64,{b64}';
            link.download = '{filename}';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        </script>
        """
        
        # JS ausführen
        html_placeholder = st.empty()
        with html_placeholder:
            components.html(f"<html><body>{js}</body></html>", height=0)
        
        # 3. User Feedback & Delay
        st.success("Daten wurden an übermittelt")
        
        # Kurzer Sleep nötig, damit der Browser den Download initiiert,
        # bevor der Streamlit Rerun (Reset) alles killt.
        time.sleep(2.5) 
        
        # 4. Reset & Redirect
        reset_simulation_state()
        st.rerun()
