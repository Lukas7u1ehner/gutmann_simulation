import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import date

try:
    from .style import (
        GUTMANN_ACCENT_GREEN,
        GUTMANN_LIGHT_TEXT,
        GUTMANN_SECONDARY_DARK,
        GUTMANN_DARK_GREEN,
    )
except ImportError:
    GUTMANN_ACCENT_GREEN = "#B3D463"
    GUTMANN_LIGHT_TEXT = "#D1D1D1"
    GUTMANN_SECONDARY_DARK = "#3E524D"
    GUTMANN_DARK_GREEN = "#25342F"

# --- EREIGNIS-DEFINITIONEN (S&P 500 Bärenmärkte & Korrekturen) ---
# Start = Markt-Hoch, End = Markt-Tief
MARKET_PHASES = [
    {
        "label": "Dotcom-Blase",
        "start": "2000-03-24",
        "end": "2002-10-09",
        "desc": "Platzen der Technologieblase. Der S&P 500 verlor ca. 49%.",
        "color": "rgba(255, 0, 0, 0.1)" # Leichtes Rot
    },
    {
        "label": "Finanzkrise (GFC)",
        "start": "2007-10-09",
        "end": "2009-03-09",
        "desc": "Globale Finanzkrise ausgelöst durch den US-Hypothekenmarkt. Rückgang ca. 57%.",
        "color": "rgba(255, 0, 0, 0.1)"
    },
    {
        "label": "Euro-Krise & US-Downgrade",
        "start": "2011-04-29",
        "end": "2011-10-03",
        "desc": "Staatsschuldenkrise in Europa und Herabstufung der US-Bonität. Rückgang ca. 19%.",
        "color": "rgba(255, 165, 0, 0.1)" # Orange (Korrektur)
    },
    {
        "label": "Corona-Crash",
        "start": "2020-02-19",
        "end": "2020-03-23",
        "desc": "Schnellster Bärenmarkt der Geschichte durch COVID-19 Pandemie. Rückgang ca. 34%.",
        "color": "rgba(255, 0, 0, 0.1)"
    },
    {
        "label": "Zinswende & Inflation",
        "start": "2022-01-03",
        "end": "2022-10-12",
        "desc": "Hohe Inflation, Ukraine-Krieg und steigende Zinsen. Rückgang ca. 25%.",
        "color": "rgba(255, 0, 0, 0.1)"
    }
]

@st.cache_data
def load_market_history():
    """
    Lädt S&P 500 Daten (^GSPC) ab 1995.
    """
    try:
        ticker = "^GSPC"
        start_date = "1995-01-01"
        end_date = date.today().strftime("%Y-%m-%d")
        
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        # MultiIndex Glättung falls nötig
        if isinstance(df.columns, pd.MultiIndex):
            df = df.xs('Close', axis=1, level=0, drop_level=False)
            df.columns = ["Close"]
        else:
            df = df[["Close"]]
            
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        st.error(f"Fehler beim Laden der Marktdaten: {e}")
        return pd.DataFrame()

def create_market_event_chart(df):
    """
    Erstellt Chart mit schraffierten Krisen-Phasen.
    """
    fig = go.Figure()

    # 1. Kurs-Linie
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["Close"],
        mode="lines",
        name="S&P 500",
        line=dict(color=GUTMANN_ACCENT_GREEN, width=2),
        hovertemplate='%{y:,.0f} Pkt<extra></extra>'
    ))

    # 2. Phasen einzeichnen (vrect) und Annotationen
    for phase in MARKET_PHASES:
        start_dt = pd.to_datetime(phase["start"])
        end_dt = pd.to_datetime(phase["end"])
        
        # Nur zeichnen, wenn im Datenbereich
        if start_dt >= df.index.min() and end_dt <= df.index.max():
            
            # Schraffierter Bereich
            fig.add_vrect(
                x0=start_dt, 
                x1=end_dt, 
                fillcolor=phase["color"], 
                opacity=1, 
                layer="below", 
                line_width=0,
            )

            # Label (Annotation) in der Mitte der Phase, etwas oberhalb des Kurses
            # Wir suchen den max Kurs in diesem Zeitraum für die Y-Position
            mask = (df.index >= start_dt) & (df.index <= end_dt)
            if not df[mask].empty:
                max_price_in_phase = df[mask]["Close"].max()
                
                fig.add_annotation(
                    x=start_dt + (end_dt - start_dt) / 2, # Zeit-Mitte
                    y=max_price_in_phase,
                    text=f"<b>{phase['label']}</b>",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="#555",
                    ay=-40,
                    font=dict(color="black", size=10),
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="#ccc",
                    borderwidth=1
                )

    fig.update_layout(
        title_text="Historische Marktentwicklung & Krisenphasen (S&P 500)",
        title_font_color='#000000',
        xaxis_title="Jahr",
        yaxis_title="Punkte",
        xaxis_title_font_color='#000000',
        yaxis_title_font_color='#000000',
        hovermode="x unified",
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_color='#000000',
        
        xaxis=dict(
            showgrid=True, gridcolor='#e0e0e0', showline=True, linecolor="#000000", tickfont=dict(color='black')
        ),
        yaxis=dict(
            showgrid=True, gridcolor='#e0e0e0', showline=True, linecolor="#000000", tickfont=dict(color='black')
        ),
    )
    return fig

def render():
    st.subheader("🌍 Markthistorie: Krisen als Chance verstehen")
    st.markdown("""
    Diese Analyse zeigt den Verlauf des **S&P 500** über die letzten Jahrzehnte. 
    Die <span style='color:red; font-weight:bold;'>rot markierten Phasen</span> kennzeichnen Bärenmärkte und große Korrekturen. 
    Trotz dieser Rückschläge hat sich der Markt historisch immer erholt und neue Höchststände erreicht.
    """, unsafe_allow_html=True)

    with st.spinner("Lade Marktdaten..."):
        df = load_market_history()
    
    if not df.empty:
        # Chart
        fig = create_market_event_chart(df)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 📉 Details zu den historischen Marktphasen")
        
        # --- CUSTOM TABLE LAYOUT (KEIN DROPDOWN) ---
        # Wir bauen eine schöne Grid-Ansicht für die Events
        
        # Header
        col1, col2, col3 = st.columns([1, 1, 3])
        col1.markdown("**Ereignis**")
        col2.markdown("**Zeitraum**")
        col3.markdown("**Hintergrund & Auswirkung**")
        st.markdown("<hr style='margin: 5px 0; border-color: #555;'>", unsafe_allow_html=True)

        for phase in sorted(MARKET_PHASES, key=lambda x: x['start'], reverse=True):
            c1, c2, c3 = st.columns([1, 1, 3])
            
            with c1:
                st.markdown(f"<span style='color:{GUTMANN_ACCENT_GREEN}; font-weight:bold;'>{phase['label']}</span>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"{phase['start']} bis<br>{phase['end']}", unsafe_allow_html=True)
            with c3:
                st.caption(phase['desc'])
            
            st.markdown("<div style='margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.1);'></div>", unsafe_allow_html=True)

    else:
        st.warning("Keine Daten verfügbar.")