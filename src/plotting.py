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

PROGNOSE_NOMINAL_COLOR = "#1E90FF"
PROGNOSE_REAL_COLOR = "#00FFFF"
PROGNOSE_EINZAHLUNG_COLOR = "#A9A9A9"


def create_simulation_chart(
    df_history: pd.DataFrame, 
    df_forecast: pd.DataFrame = None,
    title: str = "Simulierte Portfolio-Entwicklung" # NEUER Parameter
):
    fig = go.Figure()

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
                color=GUTMANN_LIGHT_TEXT, width=2, dash="dash"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_history.index,
            y=df_history["Einzahlungen (brutto)"],
            mode="lines",
            name="Einzahlungen (brutto, historisch)",
            line=dict(color=GUTMANN_SECONDARY_DARK, width=2.5),
        )
    )

    if df_forecast is not None and not df_forecast.empty:
        fig.add_trace(
            go.Scatter(
                x=df_forecast.index,
                y=df_forecast["Portfolio (nominal)"],
                mode="lines",
                name="Portfolio (nominal, prognose)",
                line=dict(
                    color=PROGNOSE_NOMINAL_COLOR, width=2.5, dash="dash"
                ),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df_forecast.index,
                y=df_forecast["Portfolio (real)"],
                mode="lines",
                name="Portfolio (real, prognose)",
                line=dict(
                    color=PROGNOSE_REAL_COLOR, width=2, dash="dot"
                ),
            )
        )

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

    fig.update_layout(
        title_text=title, # NEU: Dynamischer Titel
        title_font_color=GUTMANN_LIGHT_TEXT,
        xaxis_title="Datum",
        yaxis_title="Wert in €",
        hovermode="x unified",
        legend=dict(
            yanchor="top", y=0.99, xanchor="left", x=0.01, font_color=GUTMANN_LIGHT_TEXT
        ),
        plot_bgcolor=GUTMANN_DARK_GREEN,
        paper_bgcolor=GUTMANN_DARK_GREEN,
        font_color=GUTMANN_LIGHT_TEXT,
        height=600,
        xaxis=dict(
            showgrid=True,
            gridcolor=GUTMANN_SECONDARY_DARK,
            showline=True,
            linecolor="black",
            linewidth=2,
            zeroline=True,
            zerolinecolor=GUTMANN_SECONDARY_DARK,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GUTMANN_SECONDARY_DARK,
            showline=True,
            linecolor="black",
            linewidth=2,
            zeroline=True,
            zerolinecolor=GUTMANN_SECONDARY_DARK,
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
        title_font_color=GUTMANN_LIGHT_TEXT,
        xaxis_title="Datum",
        yaxis_title="Preis in €",
        hovermode="x unified",
        height=500,
        plot_bgcolor=GUTMANN_DARK_GREEN,
        paper_bgcolor=GUTMANN_DARK_GREEN,
        font_color=GUTMANN_LIGHT_TEXT,
        legend=dict(font_color=GUTMANN_LIGHT_TEXT),
        xaxis=dict(
            showgrid=True,
            gridcolor=GUTMANN_SECONDARY_DARK,
            showline=True,
            linecolor="black",
            linewidth=2,
            zeroline=True,
            zerolinecolor=GUTMANN_SECONDARY_DARK,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GUTMANN_SECONDARY_DARK,
            showline=True,
            linecolor="black",
            linewidth=2,
            zeroline=True,
            zerolinecolor=GUTMANN_SECONDARY_DARK,
        ),
    )

    return fig