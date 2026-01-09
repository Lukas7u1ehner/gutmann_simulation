import streamlit as st
from .style import (
    GUTMANN_LOGO_URL,
    GUTMANN_ACCENT_GREEN,
    GUTMANN_DARK_GREEN,
    GUTMANN_LIGHT_TEXT,
    GUTMANN_SECONDARY_DARK
)

def render():
    """
    Rendert den Inhalt des 'Startseite' Tabs als modernes Advisor Dashboard.
    """
    # Header Area (Logo Only, Centered)
    st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; margin-top: 20px; margin-bottom: 30px;" role="banner" aria-label="Header mit Firmenlogo">
        <img src="{GUTMANN_LOGO_URL}" alt="Bank Gutmann Logo" style="width: 400px; max-width: 90%; height: auto;">
    </div>
    """, unsafe_allow_html=True)
    
    def go_to_simulation():
         st.session_state.main_nav = "Simulation"
    
    # Action Card
    st.markdown(f"""
    <div style="background-color: {GUTMANN_SECONDARY_DARK}; padding: 20px; border-radius: 8px; border-left: 6px solid {GUTMANN_ACCENT_GREEN}; margin-bottom: 20px;" role="region" aria-label="Neues Kundengespräch">
        <h3 style="color: {GUTMANN_ACCENT_GREEN}; margin-top:0;">Neues Kundengespräch</h3>
        <p style="color: {GUTMANN_LIGHT_TEXT}; font-size: 1.0rem;">Starten Sie eine neue Simulation. Konfigurieren Sie Portfolio, Sparpläne und Szenarien.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Button-Layout
    c_btn1, c_btn2, c_btn3 = st.columns([1, 1, 1])
    with c_btn1:
        st.button("Simulation starten", key="btn_start_sim", use_container_width=True, type="primary", on_click=go_to_simulation)

    st.markdown("<br>", unsafe_allow_html=True)

    # Advisor Talking Points
    st.subheader("Talking Points: Markt & Strategie")
    
    tp_col1, tp_col2 = st.columns(2)
    
    with tp_col1:
         st.info("**Aktuelles Marktumfeld**")
         st.markdown("""
         *   **Zinswende:** Die Zentralbanken signalisieren stabile Zinsen. Anleihen bieten wieder attraktive laufende Erträge.
         *   **Technologie-Sektor:** Volatilität bleibt hoch, aber langfristige Trends (AI, Cloud) sind intakt.
         *   **Inflation:** Rückläufig, aber strukturell höher als vor 2020. Realzinserhalt bleibt Priorität.
         """)
         
    with tp_col2:
         st.success("**Strategische Argumente**")
         st.markdown("""
         *   **Cost-Average-Effekt:** Sparpläne nutzen Schwächephasen automatisch zum günstigen Nachkauf.
         *   **Diversifikation:** Nicht alles auf eine Karte setzen. Der Mix aus Tech & Value stabilisiert das Depot.
         *   **Langfristigkeit:** Historisch betrachtet hat sich der Aktienmarkt über 15+ Jahre immer positiv entwickelt.
         """)

    st.markdown("<br>", unsafe_allow_html=True)

    # System Wartung (Nur sichtbar mit ?admin=1 in der URL)
    if st.query_params.get("admin") == "1":
        with st.expander("🛠️ System-Wartung (Daten-Cache)"):
            st.write("Laden Sie hier alle Marktdaten für den Katalog lokal herunter, um die App offline-fähig und robuster zu machen.")
            
            if st.button("Gesamten Katalog vorladen (ab 2000)", use_container_width=True):
                from .cache_manager import preload_all_data
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.write("⏳ Starte Pre-loading... Dies kann einige Minuten dauern.")
                
                from .catalog import KATALOG
                from . import backend_simulation
                from datetime import date
                import time
                
                tickers = [v for k, v in KATALOG.items() if v]
                total = len(tickers)
                
                for i, ticker in enumerate(tickers, 1):
                    status_text.write(f"Verarbeite {i}/{total}: **{ticker}**")
                    try:
                        backend_simulation.load_data(ticker, date(2000, 1, 1), date.today())
                    except Exception as e:
                        st.error(f"Fehler bei {ticker}: {e}")
                    
                    progress_bar.progress(i / total)
                    time.sleep(0.05) 
                    
                status_text.write("✅ **Pre-loading abgeschlossen!** Alle Daten sind nun lokal gespeichert.")
                st.balloons()

