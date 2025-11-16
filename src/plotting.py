import plotly.graph_objects as go
import pandas as pd
import streamlit as st

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

# Farben für die Prognose-Bänder
PROGNOSE_MEDIAN_COLOR = "#1E90FF"  # Kräftiges Blau für die Median-Linie
PROGNOSE_REAL_MEDIAN_COLOR = "#00FFFF" # Cyan für die reale Median-Linie
# --- KORREKTUR: Linienfarben (deckend) und dicker ---
PROGNOSE_BEST_LINE_COLOR = "rgba(0, 200, 0, 1.0)"  # Deckend Grün
PROGNOSE_WORST_LINE_COLOR = "rgba(200, 0, 0, 1.0)" # Deckend Rot
PROGNOSE_EINZAHLUNG_COLOR = "#707070" # Dunkleres Grau


def create_simulation_chart(
    df_history: pd.DataFrame, 
    df_forecast: pd.DataFrame = None,
    title: str = "Simulierte Portfolio-Entwicklung"
):
    fig = go.Figure()

    # --- 1. HISTORISCHE DATEN (wie zuvor) ---
    fig.add_trace(
        go.Scatter(
            x=df_history.index,
            y=df_history["Portfolio (nominal)"],
            mode="lines",
            name="Portfolio (nominal, historisch)",
            line=dict(color=GUTMANN_ACCENT_GREEN, width=2.5),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_history.index,
            y=df_history["Portfolio (real)"],
            mode="lines",
            name="Portfolio (real, historisch)",
            line=dict(
                color='#707070', width=2, dash="dash"
            ),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_history.index,
            y=df_history["Einzahlungen (brutto)"],
            mode="lines",
            name="Einzahlungen (brutto, historisch)",
            line=dict(color='#303030', width=2.5),
        )
    )

    # --- 2. PROGNOSE-DATEN (NEU mit Monte Carlo) ---
    if df_forecast is not None and not df_forecast.empty:
        
        # --- B: Median-Linie (Nominal) ---
        fig.add_trace(
            go.Scatter(
                x=df_forecast.index,
                y=df_forecast["Portfolio (Median)"],
                mode="lines",
                name="Prognose Median (nominal)",
                line=dict(
                    color=PROGNOSE_MEDIAN_COLOR, width=2.5, dash="dash"
                ),
            )
        )
        
        # --- A: Linien für Best/Worst Case (Nominal) ---
        # --- KORREKTUR: 'fill=None' und 'width=2.0' ---
        fig.add_trace(
            go.Scatter(
                x=df_forecast.index,
                y=df_forecast["Portfolio (BestCase)"],
                mode="lines",
                name="Best Case (95%)",
                line=dict(color=PROGNOSE_BEST_LINE_COLOR, width=2.0, dash="dot"), # Dicker, deckend
                fill=None # Keine Füllung
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df_forecast.index,
                y=df_forecast["Portfolio (WorstCase)"],
                mode="lines",
                name="Worst Case (5%)",
                line=dict(color=PROGNOSE_WORST_LINE_COLOR, width=2.0, dash="dot"), # Dicker, deckend
                fill=None # Keine Füllung
            )
        )
        
        # --- C: Median-Linie (Real) ---
        fig.add_trace(
            go.Scatter(
                x=df_forecast.index,
                y=df_forecast["Portfolio (Real_Median)"],
                mode="lines",
                name="Prognose Median (real)",
                line=dict(
                    color=PROGNOSE_REAL_MEDIAN_COLOR, width=2, dash="dot"
                ),
            )
        )

        # --- D: Einzahlungen (Deterministisch) ---
        fig.add_trace(
            go.Scatter(
                x=df_forecast.index,
                y=df_forecast["Einzahlungen (brutto)"],
            mode="lines",
            name="Einzahlungen (brutto, prognose)",
            line=dict(
                color=PROGNOSE_EINZAHLUNG_COLOR, width=2.5, dash="dash"
            ),
        )
        )
    # --- 3. LAYOUT (KORREKTUR: Heller Hintergrund + Achsen-Titel-Farben) ---
    fig.update_layout(
        title_text=title,
        title_font_color='#000000', 
        xaxis_title="Datum",
        yaxis_title="Wert in €",
        xaxis_title_font_color='#000000', # KORREKTUR: Explizit gesetzt
        yaxis_title_font_color='#000000', # KORREKTUR: Explizit gesetzt
        hovermode="x unified",
        legend=dict(
            yanchor="top", y=0.99, xanchor="left", x=0.01, 
            font_color='#000000'
        ),
        plot_bgcolor='white', 
        paper_bgcolor='white', 
        font_color='#000000', 
        height=600,
        xaxis=dict(
            showgrid=True,
            gridcolor='#e0e0e0',
            showline=True,
            linecolor="#000000",
            linewidth=2,
            zeroline=True,
            zerolinecolor='#c0c0c0',
            tickfont=dict(color='#000000') # KORREKTUR: Achsen-Zahlen
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#e0e0e0',
            showline=True,
            linecolor="#000000",
            linewidth=2,
            zeroline=True,
            zerolinecolor='#c0c0c0',
            tickfont=dict(color='#000000') # KORREKTUR: Achsen-Zahlen
        ),
    )

    return fig


def create_price_chart(df: pd.DataFrame):
    # Diese Funktion bleibt unverändert
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Close"],
            mode="lines",
            name="Schlusskurs",
            line=dict(color=GUTMANN_ACCENT_GREEN, width=2),
        )
    )

    # --- KORREKTUR: Heller Hintergrund + Achsen-Titel-Farben ---
    fig.update_layout(
        title_text="Historischer Kursverlauf (ISIN)",
        title_font_color='#000000',
        xaxis_title="Datum",
        yaxis_title="Preis in €",
        xaxis_title_font_color='#000000', # KORREKTUR: Explizit gesetzt
        yaxis_title_font_color='#000000', # KORREKTUR: Explizit gesetzt
        hovermode="x unified",
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_color='#000000',
        legend=dict(font_color='#000000'),
        xaxis=dict(
            showgrid=True,
            gridcolor='#e0e0e0',
            showline=True,
            linecolor="#000000",
            linewidth=2,
            zeroline=True,
            zerolinecolor='#c0c0c0',
            tickfont=dict(color='#000000') # KORREKTUR: Achsen-Zahlen
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#e0e0e0',
            showline=True,
            linecolor="#000000",
            linewidth=2,
            zeroline=True,
            zerolinecolor='#c0c0c0',
            tickfont=dict(color='#000000') # KORREKTUR: Achsen-Zahlen
        ),
    )
    return fig