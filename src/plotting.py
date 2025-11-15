import plotly.graph_objects as go
import pandas as pd
import streamlit as st

# Importiere die Farben aus dem Style-Modul
try:
    # --- (KORREKTUR) ---
    # Da plotting.py und style.py im selben Ordner 'src' liegen,
    # muss der Import relativ sein (mit einem Punkt).
    from .style import (
        GUTMANN_ACCENT_GREEN,
        GUTMANN_LIGHT_TEXT,
        GUTMANN_SECONDARY_DARK,
        GUTMANN_DARK_GREEN,
    )
except ImportError:
    # Fallback-Farben, falls style.py nicht gefunden wird
    GUTMANN_ACCENT_GREEN = "#B3D463"
    GUTMANN_LIGHT_TEXT = "#D1D1D1"
    GUTMANN_SECONDARY_DARK = "#3E524D"
    GUTMANN_DARK_GREEN = "#25342F"

# (NEU) Definiere klare Farben für die Prognose
PROGNOSE_NOMINAL_COLOR = "#1E90FF"  # DodgerBlue
PROGNOSE_REAL_COLOR = "#00FFFF"  # Cyan / Aqua
PROGNOSE_EINZAHLUNG_COLOR = "#A9A9A9"  # DarkGray


def create_simulation_chart(df_history: pd.DataFrame, df_forecast: pd.DataFrame = None):
    """
    Erstellt einen interaktiven Plotly-Chart aus den Simulationsdaten
    (Historisch und optional Prognose).
    """

    fig = go.Figure()

    # --- Historische Daten (Solide Linien) ---
    fig.add_trace(
        go.Scatter(
            x=df_history.index,
            y=df_history["Portfolio (nominal)"],
            mode="lines",
            name="Portfolio (nominal, historisch)",
            line=dict(color=GUTMANN_ACCENT_GREEN, width=2.5),  # Gutmann-Grün
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
            ),  # Heller Text, gestrichelt
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_history.index,
            y=df_history["Einzahlungen (brutto)"],
            mode="lines",
            name="Einzahlungen (brutto, historisch)",
            line=dict(color=GUTMANN_SECONDARY_DARK, width=2.5),  # Dunkles Grau/Grün
        )
    )

    # --- Prognose Daten (Gestrichelte Linien in NEUEN Farben) ---
    if df_forecast is not None and not df_forecast.empty:
        fig.add_trace(
            go.Scatter(
                x=df_forecast.index,
                y=df_forecast["Portfolio (nominal)"],
                mode="lines",
                name="Portfolio (nominal, prognose)",
                line=dict(
                    color=PROGNOSE_NOMINAL_COLOR, width=2.5, dash="dash"
                ),  # (NEUE FARBE)
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
                ),  # (NEUE FARBE)
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
                ),  # (NEUE FARBE)
            )
        )

    # Layout-Anpassungen
    fig.update_layout(
        title_text="Simulierte Portfolio-Entwicklung (Historisch & Prognose)",
        title_font_color=GUTMANN_LIGHT_TEXT,
        xaxis_title="Datum",
        yaxis_title="Wert in €",
        hovermode="x unified",  # Zeigt alle Werte für ein Datum beim Hovern
        legend=dict(
            yanchor="top", y=0.99, xanchor="left", x=0.01, font_color=GUTMANN_LIGHT_TEXT
        ),
        plot_bgcolor=GUTMANN_DARK_GREEN,  # Plot-Hintergrund
        paper_bgcolor=GUTMANN_DARK_GREEN,  # Gesamt-Hintergrund
        font_color=GUTMANN_LIGHT_TEXT,  # Textfarbe für Achsen
        height=600,  # Setze eine feste Höhe von 600 Pixeln
        # --- (FIX 2: ACHSENLINIEN) ---
        xaxis=dict(
            showgrid=True,  # Gitter anzeigen
            gridcolor=GUTMANN_SECONDARY_DARK,  # Gitterfarbe
            # (ÄNDERUNG) Wir verwenden 'showline' für einen klaren Rahmen
            showline=True,  # Zeige die Haupt-Achsenlinie (den Balken)
            linecolor="black",  # Setze die Farbe des Balkens
            linewidth=2,  # Setze die Breite des Balkens
            zeroline=True,  # Nulllinie trotzdem anzeigen
            zerolinecolor=GUTMANN_SECONDARY_DARK,  # Aber in Gitterfarbe
        ),
        yaxis=dict(
            showgrid=True,  # Gitter anzeigen
            gridcolor=GUTMANN_SECONDARY_DARK,  # Gitterfarbe
            # (ÄNDERUNG) Wir verwenden 'showline' für einen klaren Rahmen
            showline=True,  # Zeige die Haupt-Achsenlinie (den Balken)
            linecolor="black",  # Setze die Farbe des Balkens
            linewidth=2,  # Setze die Breite des Balkens
            zeroline=True,  # Nulllinie trotzdem anzeigen
            zerolinecolor=GUTMANN_SECONDARY_DARK,  # Aber in Gitterfarbe
        ),
    )

    return fig


# (NEUE FUNKTION)
def create_price_chart(df: pd.DataFrame):
    """
    Erstellt einen interaktiven Plotly-Chart für den reinen 'Close'-Preis.
    """

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Close"],
            mode="lines",
            name="Schlusskurs",
            line=dict(color=GUTMANN_ACCENT_GREEN, width=2),  # Gutmann-Grün
        )
    )

    fig.update_layout(
        title_text="Historischer Kursverlauf (ISIN)",
        title_font_color=GUTMANN_LIGHT_TEXT,
        xaxis_title="Datum",
        yaxis_title="Preis in €",  # Annahme €
        hovermode="x unified",
        height=500,  # (NEU) Höhe hinzugefügt
        plot_bgcolor=GUTMANN_DARK_GREEN,
        paper_bgcolor=GUTMANN_DARK_GREEN,
        font_color=GUTMANN_LIGHT_TEXT,
        legend=dict(font_color=GUTMANN_LIGHT_TEXT),
        # --- (FIX 2: ACHSENLINIEN) ---
        xaxis=dict(
            showgrid=True,
            gridcolor=GUTMANN_SECONDARY_DARK,
            # (ÄNDERUNG) Wir verwenden 'showline' für einen klaren Rahmen
            showline=True,  # Zeige die Haupt-Achsenlinie (den Balken)
            linecolor="black",  # Setze die Farbe des Balkens
            linewidth=2,  # Setze die Breite des Balkens
            zeroline=True,  # Nulllinie trotzdem anzeigen
            zerolinecolor=GUTMANN_SECONDARY_DARK,  # Aber in Gitterfarbe
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GUTMANN_SECONDARY_DARK,
            # (ÄNDERUNG) Wir verwenden 'showline' für einen klaren Rahmen
            showline=True,  # Zeige die Haupt-Achsenlinie (den Balken)
            linecolor="black",  # Setze die Farbe des Balkens
            linewidth=2,  # Setze die Breite des Balkens
            zeroline=True,  # Nulllinie trotzdem anzeigen
            zerolinecolor=GUTMANN_SECONDARY_DARK,  # Aber in Gitterfarbe
        ),
    )

    return fig