import streamlit as st
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
    st.button("➡️ Simulation starten", use_container_width=True, type="primary", on_click=go_to_simulation)