import plotly.graph_objects as go
import pandas as pd
import streamlit as st
import numpy as np

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
PROGNOSE_MEDIAN_COLOR = "#1E90FF"
PROGNOSE_REAL_MEDIAN_COLOR = "#00FFFF"
PROGNOSE_BEST_LINE_COLOR = "rgba(0, 200, 0, 1.0)"
PROGNOSE_WORST_LINE_COLOR = "rgba(200, 0, 0, 1.0)"
PROGNOSE_EINZAHLUNG_COLOR = "#707070"

# --- MARKT-PHASEN DATEN (Erweitert bis 1980) ---
MARKET_PHASES = [
    {
        "label": "Dotcom-Blase",
        "start": "2000-03-24",
        "end": "2002-10-09",
        "desc": "Platzen der Technologieblase. Der S&P 500 verlor ca. 49%.",
        "color": "rgba(255, 0, 0, 0.1)"
    },
    {
        "label": "Finanzkrise",
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
        "color": "rgba(255, 165, 0, 0.1)"
    },
    {
        "label": "Corona-Crash",
        "start": "2020-02-19",
        "end": "2020-03-23",
        "desc": "Schnellster Bärenmarkt der Geschichte durch COVID-19. Rückgang ca. 34%.",
        "color": "rgba(255, 0, 0, 0.1)"
    },
    {
        "label": "Zinswende & Inflation",
        "start": "2022-01-03",
        "end": "2022-10-12",
        "desc": "Hohe Inflation, Ukraine-Krieg und steigende Zinsen. Rückgang ca. 25%.",
        "color": "rgba(255, 0, 0, 0.1)"
    },
    # --- NEUE HISTORISCHE PHASEN (1980-2000) ---
    {
        "label": "Russlandkrise & LTCM",
        "start": "1998-07-17",
        "end": "1998-10-08",
        "desc": "Zahlungsausfall Russlands und Beinahe-Kollaps des Hedgefonds LTCM. Rückgang ca. 19%.",
        "color": "rgba(255, 165, 0, 0.1)" # Orange (Korrektur)
    },
    {
        "label": "Golfkrieg & Rezession",
        "start": "1990-07-16",
        "end": "1990-10-11",
        "desc": "Ölpreisschock durch Invasion Kuwaits und folgende US-Rezession. Rückgang ca. 20%.",
        "color": "rgba(255, 165, 0, 0.1)"
    },
    {
        "label": "Schwarzer Montag",
        "start": "1987-08-25",
        "end": "1987-12-04",
        "desc": "Größter Tagesverlust der Geschichte (-22,6% am 19. Okt). Program Trading verschärfte den Crash. Gesamtrückgang ca. 34%.",
        "color": "rgba(255, 0, 0, 0.1)"
    },
    # --- AKTUELLE EREIGNISSE (2025+) ---
    {
        "label": "Trump Zölle",
        "start": "2025-04-01",
        "end": "2025-04-30",
        "desc": "Ankündigung neuer US-Importzölle führte zu globaler Handelsunsicherheit und Volatilität an den Märkten.",
        "color": "rgba(255, 165, 0, 0.15)"  # Orange, etwas stärker
    }
]

# --- FARBPALETTE FÜR PIE CHART (10 deutlich unterscheidbare Farben) ---
PIE_CHART_COLORS = [
    "#B3D463",  # Grün (Gutmann Accent)
    "#3498DB",  # Dunkelblau
    "#FF6B6B",  # Koralle/Rot
    "#F39C12",  # Orange
    "#9B59B6",  # Violett
    "#1ABC9C",  # Türkis
    "#E91E63",  # Pink/Rosa
    "#FFC107",  # Gelb
    "#00BCD4",  # Cyan/Hellblau
    "#8D6E63",  # Braun/Taupe
]


def create_weight_pie_chart(assets: list[dict]):
    """
    Erstellt ein Tortendiagramm zur Visualisierung der Portfolio-Gewichtungen.
    Zeigt einen transparenten "Rest"-Bereich wenn Gesamtgewichtung < 100%.
    
    Args:
        assets: Liste der Assets mit 'Name' und 'Gewichtung (%)' Keys
    
    Returns:
        Plotly Figure mit dem Pie Chart
    """
    # Daten extrahieren
    labels = []
    values = []
    
    for asset in assets:
        name = asset.get("Name", "Unbekannt")
        weight = asset.get("Gewichtung (%)", 0.0)
        if weight > 0:  # Nur Assets mit Gewichtung > 0 anzeigen
            labels.append(name)
            values.append(weight)
    
    # Falls keine Daten vorhanden, leeres Chart zurückgeben
    if not labels:
        fig = go.Figure()
        fig.add_annotation(
            text="Keine Gewichtungen vorhanden",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color=GUTMANN_LIGHT_TEXT)
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=300
        )
        return fig
    
    # Farben zuweisen (zyklisch durch Palette)
    colors = [PIE_CHART_COLORS[i % len(PIE_CHART_COLORS)] for i in range(len(labels))]
    
    # Berechne Gesamtgewichtung und füge "Rest" hinzu wenn < 100%
    total_weight = sum(values)
    has_remaining = total_weight < 100
    
    if has_remaining:
        remaining = 100 - total_weight
        labels.append("")  # Leerer Label für Rest
        values.append(remaining)
        colors.append("rgba(100, 100, 100, 0.2)")  # Transparentes Grau für Rest
    
    # Custom Text-Array: Nur für echte Assets, nicht für Rest-Segment
    num_real_assets = len(labels) - 1 if has_remaining else len(labels)
    custom_text = [f"{labels[i]}<br>{values[i]:.1f}%" for i in range(num_real_assets)]
    if has_remaining:
        custom_text.append("")  # Kein Text für Rest-Segment
    
    # Pie Chart erstellen
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,  # Donut-Style für modernes Aussehen
        marker=dict(
            colors=colors,
            line=dict(color=GUTMANN_DARK_GREEN, width=1)  # Dünnere Linie
        ),
        textposition='outside',
        text=custom_text,
        textinfo='text',  # Verwende custom text statt automatisch
        textfont=dict(size=11, color=GUTMANN_LIGHT_TEXT),
        hoverinfo='label+percent' if not has_remaining else 'skip',
        hovertemplate='<b>%{label}</b><br>Gewichtung: %{percent}<br>(%{value:.1f}%)<extra></extra>',
        pull=[0] * len(labels)  # Kein Explode-Effekt für gleichmäßige Abstände
    )])
    
    # Layout anpassen
    fig.update_layout(
        showlegend=False,  # Labels sind bereits im Chart
        paper_bgcolor="rgba(0,0,0,0)",  # Transparenter Hintergrund
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=30, b=20),
        height=350,
        annotations=[
            dict(
                text="<b>Gewichtung</b>",
                x=0.5, y=0.5,
                font=dict(size=14, color=GUTMANN_LIGHT_TEXT),
                showarrow=False
            )
        ]
    )
    
    return fig


def create_simulation_chart(
    df_history: pd.DataFrame = None, 
    df_forecast: pd.DataFrame = None,
    title: str = "Simulierte Portfolio-Entwicklung",
    show_crisis_events: bool = False
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
                hovertemplate='%{y:,.0f} €'
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

        # --- MARKTANALYSE EVENTS (Nur für Historie relevant) ---
        if show_crisis_events:
            min_date = df_history.index.min()
            max_date = df_history.index.max()

            for phase in MARKET_PHASES:
                p_start = pd.to_datetime(phase["start"])
                p_end = pd.to_datetime(phase["end"])

                # Check: Liegt die Phase (oder Teile davon) im sichtbaren Bereich?
                if p_end >= min_date and p_start <= max_date:
                    
                    vis_start = max(min_date, p_start)
                    vis_end = min(max_date, p_end)
                    
                    # 1. Visueller Bereich (Hintergrundfarbe)
                    fig.add_vrect(
                        x0=vis_start, x1=vis_end,
                        fillcolor=phase["color"], opacity=1,
                        layer="below", line_width=0,
                    )

                    # 2. Performance im Zeitraum berechnen
                    try:
                        # asof sucht den nächstgelegenen Wert, falls Datum fehlt (Wochenende)
                        val_start = df_history["Portfolio (nominal)"].asof(vis_start)
                        val_end = df_history["Portfolio (nominal)"].asof(vis_end)
                        
                        if pd.notna(val_start) and pd.notna(val_end) and val_start > 0:
                            perf_pct = ((val_end / val_start) - 1) * 100
                            perf_str = f"{perf_pct:+.2f} %"
                        else:
                            perf_str = "n/a"
                    except:
                        perf_str = "n/a"

                    # 3. Unsichtbare Linie für Hover im GESAMTEN Bereich
                    # Wir erstellen ein DataFrame für diesen Zeitraum, um für jeden Tag einen Hover-Punkt zu haben
                    mask = (df_history.index >= vis_start) & (df_history.index <= vis_end)
                    df_phase = df_history.loc[mask]
                    
                    if not df_phase.empty:
                        # Hover-Text für jeden Punkt in diesem Zeitraum
                        hover_text = (
                            f"<b>{phase['label']}</b><br>"
                            f"📅 {phase['start']} bis {phase['end']}<br><br>"
                            f"📉 <b>Portfolio-Rendite (Phase):</b> {perf_str}<br>"
                            f"ℹ️ <i>{phase['desc']}</i>"
                        )
                        
                        # Unsichtbare Linie (opacity=0), die aber Hover-Events fängt
                        fig.add_trace(go.Scatter(
                            x=df_phase.index,
                            y=df_phase["Portfolio (nominal)"], # Folgt der Portfolio-Linie
                            mode="lines",
                            line=dict(width=0), # Unsichtbar
                            name=phase['label'],
                            showlegend=False,
                            hoverinfo="text",
                            hovertext=[hover_text] * len(df_phase),
                            hoverlabel=dict(bgcolor="white", font_size=12)
                        ))
                    
                    # Label oben am Rand zur Orientierung
                    mid_date = vis_start + (vis_end - vis_start) / 2
                    fig.add_annotation(
                        x=mid_date, y=1.02, yref="paper",
                        text=f"<b>{phase['label']}</b>",
                        showarrow=False,
                        font=dict(size=10, color="#555")
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
                name="Optimistisches Szenario (95%)",
                line=dict(color=PROGNOSE_BEST_LINE_COLOR, width=2.0, dash="dot"),
                hovertemplate='<b>Optimistisch:</b> %{y:,.0f} €<extra></extra>'
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df_forecast.index,
                y=df_forecast["Portfolio (WorstCase)"],
                mode="lines",
                name="Pessimistisches Szenario (5%)",
                line=dict(color=PROGNOSE_WORST_LINE_COLOR, width=2.0, dash="dot"),
                hovertemplate='<b>Pessimistisch:</b> %{y:,.0f} €<extra></extra>'
            )
        )
        
        # --- C: Median-Linie (Real) ---
        fig.add_trace(
            go.Scatter(
                x=df_forecast.index,
                y=df_forecast["Portfolio (Real_Median)"],
                mode="lines",
                name="Prognose Median (real, kaufkraftber.)",
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
            name="Investiertes Kapital (Plan)",
            line=dict(
                color=PROGNOSE_EINZAHLUNG_COLOR, width=2.5, dash="dash"
            ),
            hovertemplate='<b>Gesamtkapital:</b> %{y:,.0f} €<extra></extra>'
        )
        )

    # --- 3. LAYOUT ---
    fig.update_layout(
        title_text=title,
        title_font_color='#000000', 
        xaxis_title="Zeitverlauf",
        yaxis_title="Portfolio-Wert (in €)",
        xaxis_title_font_color='#000000', 
        yaxis_title_font_color='#000000',
        hovermode="x unified",
        legend=dict(
            yanchor="top", y=0.99, xanchor="left", x=0.01, 
            font_color='#000000',
            bgcolor="rgba(255,255,255,0.8)" 
        ),
        plot_bgcolor='white', 
        paper_bgcolor='white', 
        font_color='#000000', 
        height=600,
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial",
            font_color="black"
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='#e0e0e0',
            showline=True,
            linecolor="#000000",
            linewidth=2,
            zeroline=True,
            zerolinecolor='#c0c0c0',
            tickfont=dict(color='#000000', size=12),
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
            tickfont=dict(color='#000000', size=12),
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