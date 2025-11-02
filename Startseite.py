import streamlit as st
import sys, os

# (ÄNDERUNG) Der alte sys.path.append kann hier komplett weg.
# Python findet den 'src' Ordner automatisch vom Hauptverzeichnis aus.

try:
    # KORREKTUR: Muss jetzt explizit aus dem 'src' Paket importieren
    from src.style import (
        apply_gutmann_style,
        GUTMANN_LOGO_URL,
        GUTMANN_ACCENT_GREEN,
        GUTMANN_DARK_GREEN,
    )
except ImportError:
    st.error(
        "Fehler: 'src/style.py' konnte nicht gefunden werden. Stelle sicher, dass die Datei im Hauptverzeichnis liegt."
    )

    # Fallback-Funktionen, damit die App nicht abstürzt
    def apply_gutmann_style():
        pass

    GUTMANN_LOGO_URL = "https://www.gutmann.at/fileadmin/templates/img/logo.svg"
    GUTMANN_ACCENT_GREEN = "#B3D463"
    GUTMANN_DARK_GREEN = "#25342F"


# Konfiguriert den Titel und das Layout der Browser-Registerkarte
st.set_page_config(
    page_title="Gutmann Simulation", page_icon=GUTMANN_LOGO_URL, layout="wide"
)

# Wende das Gutmann CSS-Styling an
apply_gutmann_style()

# --- Logo ---
st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: center; margin-top: 20px; margin-bottom: 30px;">
        <img src="{GUTMANN_LOGO_URL}" alt="Bank Gutmann Logo" style="width: 350px;">
    </div>
    """,
    unsafe_allow_html=True,
)

st.title("Willkommen zur Bank Gutmann Wertpapier-Simulation")
st.markdown(
    "Dies ist ein interaktiver Prototyp zur Simulation von Wertpapier-Portfolios, entwickelt im Rahmen des Studiums 'Digital Technology and Innovation'."
)

st.divider()

# --- Button zur Simulation ---
st.markdown("### Starten Sie Ihre persönliche Simulation")
st.markdown(
    "Analysieren Sie die historische Performance Ihrer Investment-Ideen. Stellen Sie ein Portfolio zusammen und sehen Sie, wie es sich unter Berücksichtigung von Sparplänen, Inflation und Kosten entwickelt hätte."
)

if st.button("📈 Zur Simulation starten", use_container_width=True):
    st.switch_page("pages/1_Simulation.py")

st.divider()

# --- Erklärungen ---
st.markdown("### Was simuliert dieses Tool?")
st.markdown(
    "Dieses Tool führt ein **Backtesting** durch. Es nutzt reale, historische Kursdaten von `yfinance`, um die Wertentwicklung eines von dir zusammengestellten Portfolios in der Vergangenheit nachzubilden."
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"#### 💸 Einzahlungen")
    st.markdown(
        """
        - **Einmalerlag:** Ein Startkapital, das Sie zu Beginn investieren.
        - **Sparplan:** Regelmäßige (z.B. monatliche) Einzahlungen, die Ihr Portfolio kontinuierlich aufbauen.
        """
    )

with col2:
    st.markdown(f"#### 📉 Inflation & Kosten")
    st.markdown(
        """
        - **Inflation (Real):** Zeigt die "echte" Wertentwicklung nach Abzug der Inflation (Kaufkraftverlust).
        - **Kosten (Nominal):** Berücksichtigt Gebühren wie den Ausgabeaufschlag, die Ihre investierte Summe und somit die Rendite schmälern.
        """
    )

with col3:
    st.markdown(f"#### 📈 Rendite (KPIs)")
    st.markdown(
        """
        - **Nominale Rendite:** Die reine Wertentwicklung Ihres Portfolios in Prozent, ohne Inflation.
        - **Reale Rendite:** Die inflationsbereinigte Rendite. Sie zeigt, wie stark Ihr Vermögen *tatsächlich* an Kaufkraft gewonnen hat.
        """
    )

st.sidebar.markdown("---")
st.sidebar.info(
    "Entwickelt für Bank Gutmann | FH Wien | Digital Technology and Innovation"
)
