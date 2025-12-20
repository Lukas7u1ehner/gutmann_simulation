import streamlit as st
import yfinance as yf
from .style import (
    GUTMANN_LOGO_URL,
    GUTMANN_ACCENT_GREEN,
    GUTMANN_LIGHT_TEXT,
    GUTMANN_SECONDARY_DARK
)

def render():
    """
    Rendert den Inhalt des 'Startseite' Tabs (Advisor Dashboard).
    """
    st.markdown(f"""<div style="display: flex; align-items: center; justify-content: center; margin-top: 20px; margin-bottom: 30px;"><img src="{GUTMANN_LOGO_URL}" alt="Bank Gutmann Logo" style="width: 350px;"></div>""", unsafe_allow_html=True)
    
    st.title("Private Banking Simulation Suite")
    st.markdown("### 🏛️ Leitfaden für das Kundengespräch")
    st.markdown("Willkommen im Beratungs-Interface. Dieses Tool dient zur Visualisierung von **Vermögensszenarien** auf Basis realer Marktdaten und stochastischer Prognosen.")

    col_info1, col_info2 = st.columns(2)
    
    # Custom HTML Boxen für CI-Konformität
    with col_info1:
        st.markdown(f"""
        <div class="gutmann-box">
            <h4>1. Phase: Status Quo & Historie</h4>
            <ul>
                <li><strong>Erfassung:</strong> Geplantes Portfolio (Einmalerlag & Sparpläne).</li>
                <li><strong>Backtesting:</strong> Zeigen Sie dem Kunden die Entwicklung seit z.B. 2020.</li>
                <li><em>Ziel: Vertrauen durch Transparenz schaffen.</em></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with col_info2:
        st.markdown(f"""
        <div class="gutmann-box">
            <h4>2. Phase: Zukunft & Erwartungsmanagement</h4>
            <ul>
                <li><strong>Monte-Carlo-Simulation:</strong> Projektion über 5 bis 30 Jahre.</li>
                <li><strong>Szenarien:</strong> Best Case, Worst Case und Median.</li>
                <li><em>Ziel: Realistische Einschätzung von Chancen und Risiken.</em></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### ⚠️ Compliance-Hinweis für den Berater")
    st.caption("""
    Bitte weisen Sie den Kunden darauf hin, dass vergangene Wertentwicklungen kein verlässlicher Indikator für die Zukunft sind. 
    Die Prognosen basieren auf mathematischen Modellen (Monte Carlo) und stellen keine Garantie dar. 
    Alle Werte verstehen sich vor Steuern, sofern nicht anders konfiguriert.
    """)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- FIX FÜR DEN FEHLER ---
    # Wir definieren eine Callback-Funktion. Diese wird ausgeführt, BEVOR Streamlit neu lädt.
    def go_to_simulation():
        st.session_state.main_nav = "Simulation"

    # Wir nutzen 'on_click' um den State sicher zu ändern
    # ÄNDERUNG: Emoji entfernt, nur Text "Simulation starten"
    st.button("Simulation starten", use_container_width=True, type="primary", on_click=go_to_simulation)

    # --- DATEN-WARTUNG (Cache Pre-loading) ---
    with st.expander("🛠️ System-Wartung (Daten-Cache)"):
        st.write("Laden Sie hier alle Marktdaten für den Katalog lokal herunter, um die App offline-fähig und robuster zu machen.")
        
        if st.button("Gesamten Katalog vorladen (ab 2000)", use_container_width=True):
            from .cache_manager import preload_all_data
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.write("⏳ Starte Pre-loading... Dies kann einige Minuten dauern.")
            
            # Da wir die Progress-Bar anzeigen wollen, rufen wir eine leicht angepasste Version auf
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
                time.sleep(0.1) # Kurze Pause
                
            status_text.write("✅ **Pre-loading abgeschlossen!** Alle Daten sind nun lokal gespeichert.")
            st.balloons()