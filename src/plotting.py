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
PROGNOSE_BEST_LINE_COLOR = "rgba(0, 200, 0, 1.0)"  # Deckend Grün
PROGNOSE_WORST_LINE_COLOR = "rgba(200, 0, 0, 1.0)" # Deckend Rot
PROGNOSE_EINZAHLUNG_COLOR = "#707070" # Dunkleres Grau


def create_simulation_chart(
    df_history: pd.DataFrame = None, 
    df_forecast: pd.DataFrame = None,
    title: str = "Simulierte Portfolio-Entwicklung"
):
    fig = go.Figure()

    # --- 1. HISTORISCHE DATEN ---
    if df_history is not None and not df_history.empty:
        fig.add_trace(
            go.Scatter(
                x=df_history.index,
                y=df_history["Portfolio (nominal)"],
                mode="lines",
                name="Portfolio (nominal, historisch)",
                line=dict(color=GUTMANN_ACCENT_GREEN, width=2.5),
                hovertemplate='%{y:,.0f} €' # Kompaktes Hover
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
                hovertemplate='%{y:,.0f} €'
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df_history.index,
                y=df_history["Einzahlungen (brutto)"],
                mode="lines",
                name="Einzahlungen (brutto, historisch)",
                line=dict(color='#303030', width=2.5),
                hovertemplate='%{y:,.0f} €'
            )
        )

    # --- 2. PROGNOSE-DATEN ---
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
                hovertemplate='<b>Median (Nom):</b> %{y:,.0f} €<extra></extra>' 
            )
        )
        
        # --- A: Linien für Best/Worst Case (Nominal) ---
        fig.add_trace(
            go.Scatter(
                x=df_forecast.index,
                y=df_forecast["Portfolio (BestCase)"],
                mode="lines",
                name="Best Case (95%)",
                line=dict(color=PROGNOSE_BEST_LINE_COLOR, width=2.0, dash="dot"),
                fill=None,
                hovertemplate='<b>Best (95%):</b> %{y:,.0f} €<extra></extra>'
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df_forecast.index,
                y=df_forecast["Portfolio (WorstCase)"],
                mode="lines",
                name="Worst Case (5%)",
                line=dict(color=PROGNOSE_WORST_LINE_COLOR, width=2.0, dash="dot"),
                fill=None,
                hovertemplate='<b>Worst (5%):</b> %{y:,.0f} €<extra></extra>'
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
                hovertemplate='<b>Median (Real):</b> %{y:,.0f} €<extra></extra>'
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
            hovertemplate='<b>Invest:</b> %{y:,.0f} €<extra></extra>'
        )
        )

    # --- 3. LAYOUT ---
    fig.update_layout(
        title_text=title,
        title_font_color='#000000', 
        # ACHSEN-BESCHRIFTUNGEN ANGEPASST
        xaxis_title="Zeitverlauf",
        yaxis_title="Portfolio-Wert (in €)",
        xaxis_title_font_color='#000000', 
        yaxis_title_font_color='#000000',
        
        hovermode="x unified", # Gemeinsamer Tooltip
        
        # Legende oben links
        legend=dict(
            yanchor="top", y=0.99, xanchor="left", x=0.01, 
            font_color='#000000',
            bgcolor="rgba(255,255,255,0.8)" 
        ),
        plot_bgcolor='white', 
        paper_bgcolor='white', 
        font_color='#000000', 
        height=600,
        
        # Hover-Label Styling (Kompakt)
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial",
            font_color="black" # ZUSÄTZLICHE SICHERHEIT
        ),

        xaxis=dict(
            showgrid=True,
            gridcolor='#e0e0e0',
            showline=True,
            linecolor="#000000",
            linewidth=2,
            zeroline=True,
            zerolinecolor='#c0c0c0',
            tickfont=dict(color='#000000', size=12), # Schrift schwarz erzwungen
            title_font=dict(color='#000000', size=14)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#e0e0e0',
            showline=True,
            linecolor="#000000",
            linewidth=2,
            zeroline=True,
            zerolinecolor='#c0c0c0',
            tickfont=dict(color='#000000', size=12), # Schrift schwarz erzwungen
            title_font=dict(color='#000000', size=14),
            tickformat="s" 
        ),
    )

    return fig


def create_price_chart(df: pd.DataFrame):
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

    fig.update_layout(
        title_text="Historischer Kursverlauf (ISIN)",
        title_font_color='#000000',
        xaxis_title="Zeitverlauf",
        yaxis_title="Preis in €",
        xaxis_title_font_color='#000000', 
        yaxis_title_font_color='#000000',
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
            tickfont=dict(color='#000000')
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#e0e0e0',
            showline=True,
            linecolor="#000000",
            linewidth=2,
            zeroline=True,
            zerolinecolor='#c0c0c0',
            tickfont=dict(color='#000000') 
        ),
    )
    return fig