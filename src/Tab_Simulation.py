import streamlit as st
from datetime import date
import numpy as np
import yfinance as yf
import base64
import copy
import streamlit.components.v1 as components

# Relative Imports innerhalb des src-Pakets
from . import backend_simulation
from . import plotting
from . import portfolio_logic
from . import prognose_logic
from .catalog import KATALOG
from .pdf_report import generate_pdf_report # NEU: Import für PDF
from .portfolio_templates import load_portfolio_template, get_portfolio_display_name
from .style import (
    GUTMANN_ACCENT_GREEN,
    GUTMANN_LIGHT_TEXT,
    GUTMANN_SECONDARY_DARK
)

# --- KONFIGURATION & KONSTANTEN ---
RISK_PROFILES = {
    "Konservativ": {"volatilitaet_pa": 10.0},
    "Ausgewogen":  {"volatilitaet_pa": 17.0},
    "Offensiv":    {"volatilitaet_pa": 25.0}
}
FIXED_RISK_PROFILE_KEY = "Ausgewogen"
FIXED_VOLATILITY = RISK_PROFILES[FIXED_RISK_PROFILE_KEY]["volatilitaet_pa"]
FIXED_N_SIMULATIONS = 100
FIXED_SPARPLAN_ACTIVE = True


def render():
    """
    Rendert den gesamten Inhalt des 'Simulation' Tabs.
    """
    # --- RERUN FLAG SYSTEM ---
    # Initialisiere Flag für verzögerte Reruns (verhindert Button-Konflikte)
    if "needs_rerun" not in st.session_state:
        st.session_state.needs_rerun = False
    
    # --- HEADER: BERATER & KUNDENDATEN (READ-ONLY) ---
    handover = st.session_state.get("handover_data", {})
    budget_limit = handover.get("budget", 0)

    # --- BERECHNUNG & SIDE-WARNUNG (REAKTIV) ---
    # Wir berechnen die projizierte Gesamteinzahlung manuell am Anfang, 
    # damit die Warnung sofort und konsistent mit den KPIs ist.
    months_sim = 0
    if st.session_state.get("sim_start_date") and st.session_state.get("sim_end_date"):
        s = st.session_state.sim_start_date
        e = st.session_state.sim_end_date
        months_sim = (e.year - s.year) * 12 + e.month - s.month



    # Header-Bereich: Noch kompaktere Namen, größere Portfolio-Übersicht
    header_col1, header_col2, header_col3 = st.columns([0.5, 0.5, 2])  # 30% schmaler!
    
    with header_col1:
        st.markdown('<div role="heading" aria-level="2" style="font-weight: bold; color: white;">BERATER</div>', unsafe_allow_html=True)
        st.text_input(
            "Name des Beraters", 
            value=handover.get("advisor", "Mag. Anna Berger")[:30],
            disabled=True, 
            key="ro_advisor",
            label_visibility="collapsed"
        )
    
    with header_col2:
        st.markdown('<div role="heading" aria-level="2" style="font-weight: bold; color: white;">KUNDE</div>', unsafe_allow_html=True)
        st.text_input(
            "Name des Kunden", 
            value=handover.get("client", "Max Mustermann")[:30],
            disabled=True, 
            key="ro_client",
            label_visibility="collapsed"
        )
    
    with header_col3:
        # Header für Portfolio Bereich
        st.markdown('<div role="heading" aria-level="2" style="font-weight: bold; color: white;">PORTFOLIO-ÜBERSICHT</div>', unsafe_allow_html=True)
        
        # --- REACTIVE CALCULATION: Werte werden nun editierbar und triggern Neuberechnung ---
        # Initialisiere editierbare Werte in Session State (falls nicht vorhanden)
        if "editable_budget" not in st.session_state:
            st.session_state.editable_budget = handover.get("budget", 0.0)
        if "editable_einmalerlag" not in st.session_state:
            st.session_state.editable_einmalerlag = handover.get("einmalerlag", 0.0)
        if "editable_sparrate" not in st.session_state:
            st.session_state.editable_sparrate = handover.get("savings_rate", 0.0)
        
        portfolio_type_display = handover.get("portfolio_type", "Manuell")
        
        # Callback für Neuberechnung aller Assets
        def recalculate_assets_from_totals():
            """Berechnet Euro-Beträge aller Assets basierend auf Gewichtung * Gesamt-Werte"""
            for asset in st.session_state.assets:
                weight = asset.get("Gewichtung (%)", 0.0)
                asset["Einmalerlag (€)"] = (st.session_state.editable_einmalerlag * weight) / 100
                asset["Sparbetrag (€)"] = (st.session_state.editable_sparrate * weight) / 100
            st.session_state.needs_rerun = True
        
        # Callback für Budget-Änderung: Einmalerlag auf max. Budget begrenzen
        def on_budget_change():
            # Nur begrenzen wenn Einmalerlag über Budget, NICHT recalculate aufrufen
            if st.session_state.editable_einmalerlag > st.session_state.editable_budget:
                st.session_state.editable_einmalerlag = st.session_state.editable_budget
        
        # Premium Grid mit leerem Bereich rechts (Portfolio Übersicht kleiner)
        col_portfolio, col_empty = st.columns([0.8, 0.2])
        
        with col_portfolio:
            with st.container(border=True):
                r1c1, r1c2, r1c3 = st.columns(3)
            
            with r1c1:
                st.number_input(
                    "Budget (€)",
                    min_value=0.0,
                    step=1000.0,
                    key="editable_budget",
                    format="%.0f",
                    on_change=on_budget_change,
                    help="Das maximale Gesamtbudget, das der Kunde investieren möchte.",
                )
            with r1c2:
                # Einmalerlag OHNE max_value (verhindert Reset bei Budget-Änderung)
                # Validierung erfolgt über on_budget_change Callback
                st.number_input(
                    "Einmalerlag (€)",
                    min_value=0.0,
                    step=1000.0,
                    key="editable_einmalerlag",
                    format="%.0f",
                    on_change=recalculate_assets_from_totals,
                    help="Einmaliger Anlagebetrag zu Beginn der Investition.",
                )
            with r1c3:
                st.number_input(
                    "Laufender Betrag",
                    min_value=0.0,
                    step=100.0,
                    key="editable_sparrate",
                    format="%.0f",
                    on_change=recalculate_assets_from_totals,
                    help="Regelmäßiger Investitionsbetrag pro Intervall.",
                )
            # Portfolio Type wird nicht mehr angezeigt (ausgeblendet)

    # Budget Limit für spätere Verwendung (Sidebar Warnung)
    budget_limit = st.session_state.editable_budget
    
    # --- AUTO-LOADING LOGIC (nur beim ersten Render) ---
    if (handover.get("portfolio_type") and not handover.get("preloaded")):
        portfolio_type = handover["portfolio_type"]
        einmalerlag_for_loading = handover.get("einmalerlag", 0)
        savings_rate = handover.get("savings_rate", 0)
        savings_interval = handover.get("savings_interval", "monatlich")
        custom_weights = handover.get("custom_weights", {})  # NEU: Custom Gewichtungen aus URL
        
        # Portfolio-Template laden
        loaded_assets = load_portfolio_template(
            portfolio_type, 
            einmalerlag_for_loading,
            savings_rate,
            savings_interval
        )
        
        # NEU: Custom Gewichtungen anwenden, falls vorhanden
        if loaded_assets and custom_weights:
            # Gewichtungen überschreiben
            for asset in loaded_assets:
                ticker = asset.get("ISIN / Ticker", "")
                if ticker in custom_weights:
                    new_weight = custom_weights[ticker]
                    asset["Gewichtung (%)"] = new_weight
                    # Euro-Beträge neu berechnen
                    asset["Einmalerlag (€)"] = (einmalerlag_for_loading * new_weight) / 100
                    asset["Sparbetrag (€)"] = (savings_rate * new_weight) / 100
        
        if loaded_assets:
            # Assets zur bestehenden Liste hinzufügen (NICHT ersetzen für Hybrid-Modus)
            st.session_state.assets.extend(loaded_assets)
            
            # Flag setzen, damit es nur einmal lädt
            st.session_state.handover_data["preloaded"] = True
            
            # Popup-Feedback statt permanentem Banner
            portfolio_display_name = get_portfolio_display_name(portfolio_type)
            weight_info = " (mit custom Gewichtungen)" if custom_weights else ""
            st.toast(f"Basis-Portfolio '{portfolio_display_name}'{weight_info} wurde geladen.", icon="✅")
    
    # =====================================================================
    # SECTION 1: EMPFOHLENE PRODUKTE (Main product table)
    # =====================================================================
    
    # st.subheader("Empfohlene Produkte")  <-- GELÖSCHT V4
    
    # FIX: Keine Zwischenvariablen mehr - direkt aus Session State lesen
    # Die number_input Widgets speichern ihre Werte unter dem key im Session State
    # Wir lesen diese Werte direkt bei der Berechnung, nicht hier
    
    # CSS to hide +/- buttons on number inputs AND center content vertically
    st.markdown("""
    <style>
    /* Hide increment/decrement buttons on number inputs if any are left */
    input[type=number]::-webkit-inner-spin-button,
    input[type=number]::-webkit-outer-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
    input[type=number] {
        -moz-appearance: textfield;
    }
    
    /* Align horizontal blocks (rows) ONLY within product table - addressing Header Alignment issue */
    .product-table div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }
    
    /* Force vertical centering in bordered containers (asset rows) */
    div[data-testid="stVerticalBlockBorder"] > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }
    
    /* Ensure columns inside rows stretch to fill height and center content */
    div[data-testid="stVerticalBlockBorder"] div[data-testid="column"] {
        display: flex !important;
        align-items: center !important;
    }
    
    /* Make text cells match input field height */
    div[data-testid="stVerticalBlockBorder"] div[data-testid="column"] > div[data-testid="stVerticalBlock"] {
        justify-content: center !important;
        min-height: 38px !important;
        display: flex !important;
        flex-direction: column !important;
    }

    /* SPECIFICALLY center the table header row */
    div.table-header [data-testid="stMarkdown"] p {
        text-align: center !important;
        font-weight: bold !important;
    }

    /* DRASTISCH REDUCE container padding */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div.element-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* Reduce border container padding - addressing Issue 1 */
    .product-table div[data-testid="stVerticalBlockBorder"] {
        padding: 4px 12px !important;
    }

    /* Target the specific layout wrapper for height auto issues if needed */
    div[data-testid="stLayoutWrapper"] {
        height: auto !important;
    }
    
    /* Fix vertical centering - align all items to same baseline */
    [data-testid="stVerticalBlock"] [data-testid="stMarkdown"] p {
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.2;
    }
    
    [data-testid="stVerticalBlock"] [data-testid="stCaptionContainer"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Align form inputs */
    [data-testid="stNumberInput"] > div,
    [data-testid="stTextInput"] > div,
    [data-testid="stSelectbox"] > div {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    
    /* Style delete button as plain emoji */
    button[kind="secondary"]:has([data-testid="baseButton-secondary"]) {
        background: none !important;
        border: none !important;
        padding: 0 !important;
        font-size: 1.2em;
        cursor: pointer;
        color: inherit;
        box-shadow: none !important;
    }
    button[kind="secondary"]:hover {
        transform: scale(1.2);
        background: none !important;
    }
    
    /* Prevent toggle buttons from resizing on hover/click */
    button[data-testid="stBaseButton-secondary"] {
        transform: none !important;
        transition: background-color 0.2s ease !important;
    }
    button[data-testid="stBaseButton-secondary"]:hover {
        transform: none !important;
    }
    button[data-testid="stBaseButton-secondary"]:active {
        transform: none !important;
    }
    button[data-testid="stBaseButton-secondary"]:focus {
        transform: none !important;
    }

    /* Special compacting for text inputs in the table */
    div[data-testid="stTextInput"] input {
        padding: 4px 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Layout für Tabelle (Links 55%, Rechts für Pie Chart 45%)
    col_main, col_chart = st.columns([0.55, 0.45])
    
    with col_chart:
        # Berechne Gesamtgewichtung für Pie Chart Logik
        total_weight_for_pie = sum(a.get("Gewichtung (%)", 0) for a in st.session_state.assets)
        
        if total_weight_for_pie > 100:
            # Gewichtung über 100% → Fehlermeldung anzeigen
            st.markdown(
                """
                <div style="
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    height: 300px;
                    border: 2px dashed #ff6b6b;
                    border-radius: 10px;
                    background-color: rgba(255, 107, 107, 0.1);
                    margin: 20px;
                ">
                    <div style="text-align: center; color: #ff6b6b;">
                        <p style="font-size: 2em; margin: 0;">⚠️</p>
                        <p style="font-size: 1.1em; font-weight: bold; margin: 10px 0;">Gewichtung über 100%</p>
                        <p style="font-size: 0.9em; color: #ccc;">Bitte reduzieren Sie die Gewichtungen.</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        elif total_weight_for_pie > 0:
            # Gewichtung zwischen 0% und 100% → Pie Chart anzeigen
            pie_fig = plotting.create_weight_pie_chart(st.session_state.assets)
            st.plotly_chart(pie_fig, use_container_width=True, key="weight_pie_chart")
        # Bei 0% Gewichtung → nichts anzeigen (kein else-Block)
    
    with col_main:
        # Wrapper für das gesamte Product-Table Layout mit ARIA
        st.markdown('<div class="product-table" role="table" aria-label="Portfolio-Übersicht">', unsafe_allow_html=True)
        
        # HEADER ROW - Centered via CSS
        st.markdown('<div class="table-header" role="rowgroup" aria-label="Spaltenüberschriften">', unsafe_allow_html=True)
        h1, h2, h3, h4, h5, h6, h7 = st.columns([1.5, 1.5, 1, 1.2, 1.2, 1.2, 0.5])
        
        with h1:
            st.markdown("**Name**")
        with h2:
            st.markdown("**ISIN / Ticker**")
        with h3:
            st.markdown("**Gewichtung (%)**")
        with h4:
            st.markdown("**Einmalbetrag (€)**")
        with h5:
            st.markdown("**Laufender Betrag**")
        with h6:
            st.markdown("**Intervall**")
        with h7:
            st.markdown("")  # Empty for delete button
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ASSET ROWS
        for idx, asset in enumerate(st.session_state.assets):
            name = asset.get('Name', 'Unbekannt')
            ticker = asset.get('ISIN / Ticker', '')
            interval = asset.get("Spar-Intervall", "monatlich")
            
            # Row mit kompaktem Container
            with st.container(border=True):
                c1, c2, c3, c4, c5, c6, c7 = st.columns([1.5, 1.5, 1, 1.2, 1.2, 1.2, 0.5])
                
                with c1:
                    st.markdown(f'<p>{name}</p>', unsafe_allow_html=True)
                
                with c2:
                    st.markdown(f'<p style="color: #ccc; font-size: 0.85em;">{ticker}</p>', unsafe_allow_html=True)
                
                with c3:
                    # Gewichtung als Text-Input (ohne +/-)
                    w_key = f"weight_text_{idx}"
                    current_weight = float(asset.get("Gewichtung (%)", 0.0))
                    
                    # Callback für Gewichtungs-Änderung
                    def on_weight_change(asset_idx=idx):
                        try:
                            new_val = float(st.session_state[f"weight_text_{asset_idx}"].replace(",", ".").strip())
                            st.session_state.assets[asset_idx]["Gewichtung (%)"] = new_val
                            st.session_state.needs_rerun = True
                        except (ValueError, KeyError):
                            pass
                    
                    st.text_input(
                        "%",
                        value=f"{current_weight:.1f}",
                        key=w_key,
                        label_visibility="collapsed",
                        on_change=on_weight_change
                    )
                
                with c4:
                    # Einmalbetrag READ-ONLY: Berechnet aus Gewichtung * Gesamt-Einmalerlag
                    current_weight = st.session_state.assets[idx].get("Gewichtung (%)", 0.0)
                    einmalerlag_val = (st.session_state.editable_einmalerlag * current_weight) / 100
                    
                    # Speichere berechneten Wert im Session State für Simulation
                    st.session_state.assets[idx]["Einmalerlag (€)"] = einmalerlag_val
                    
                    # Markdown mit vertikaler Zentrierung
                    st.markdown(f'<p style="font-weight: bold;">€ {einmalerlag_val:,.0f}</p>', unsafe_allow_html=True)
                
                with c5:
                    # Sparbetrag READ-ONLY: Berechnet aus Gewichtung * Gesamt-Sparrate
                    current_weight = st.session_state.assets[idx].get("Gewichtung (%)", 0.0)
                    sparrate_val = (st.session_state.editable_sparrate * current_weight) / 100
                    
                    # Speichere berechneten Wert im Session State für Simulation
                    st.session_state.assets[idx]["Sparbetrag (€)"] = sparrate_val
                    
                    # Markdown mit vertikaler Zentrierung
                    st.markdown(f'<p style="font-weight: bold;">€ {sparrate_val:,.0f}</p>', unsafe_allow_html=True)

                
                with c6:
                    # Spar-Intervall EDITABLE mit Dropdown
                    interval_options = ["monatlich", "vierteljährlich", "jährlich"]
                    current_idx = interval_options.index(interval) if interval in interval_options else 0
                    
                    # Callback für Intervall-Änderung
                    def on_interval_change(asset_idx=idx):
                        st.session_state.assets[asset_idx]["Spar-Intervall"] = st.session_state[f"interval_{asset_idx}"]
                        st.session_state.needs_rerun = True
                    
                    st.selectbox(
                        "Intervall",
                        interval_options,
                        index=current_idx,
                        key=f"interval_{idx}",
                        label_visibility="collapsed",
                        on_change=on_interval_change
                    )
                
                with c7:
                    # Delete mit Undo-Funktion
                    if st.button("🗑️", key=f"delete_{idx}", help="Titel löschen", use_container_width=False):
                        # Speichere das Asset für Undo statt direktem Löschen
                        deleted_asset = st.session_state.assets.pop(idx)
                        st.session_state.deleted_asset = {
                            "asset": deleted_asset,
                            "index": idx
                        }
                        st.session_state.undo_button_shown = False  # False beim Löschen!
                        st.rerun()  # Expliziter Rerun statt needs_rerun
        
        # Initialize flag for undo button visibility
        if "undo_button_shown" not in st.session_state:
            st.session_state.undo_button_shown = False
        
        # --- UNDO BUTTON (bleibt bis zur nächsten User-Aktion) ---
        if st.session_state.get("deleted_asset"):
            deleted_info = st.session_state.deleted_asset
            deleted_name = deleted_info["asset"].get("Name", "Unbekannt")
            
            # Zeige Button und prüfe Click
            col_undo, _ = st.columns([0.55, 0.45])
            with col_undo:
                undo_clicked = st.button(f'"{deleted_name}" wiederherstellen', key="undo_delete", type="secondary")
            
            if undo_clicked:
                # User hat Undo geklickt → Asset wiederherstellen
                original_idx = min(deleted_info["index"], len(st.session_state.assets))
                st.session_state.assets.insert(original_idx, deleted_info["asset"])
                st.session_state.deleted_asset = None
                st.session_state.undo_button_shown = False
                st.rerun()
            elif st.session_state.undo_button_shown:
                # Button war schon sichtbar, User hat was ANDERES gemacht → aufräumen + rerun
                st.session_state.deleted_asset = None
                st.session_state.undo_button_shown = False
                st.rerun()  # Sofort neuladen damit Button verschwindet
            else:
                # Markiere dass Button jetzt sichtbar ist
                st.session_state.undo_button_shown = True
    
    # --- Gewichtungs-Summe anzeigen (SEHR KOMPAKT, OHNE HINTERGRUND) ---
    total_weight = sum(a.get("Gewichtung (%)", 0) for a in st.session_state.assets)
    
    col_sum, _ = st.columns([0.55, 0.45])
    with col_sum:
        # Kompakte Inline-Anzeige OHNE schwarzen Hintergrund
        delta_val = total_weight - 100
        status_color = "green" if abs(delta_val) < 0.1 else "red"
        status_text = "✅ Punktlandung!" if abs(delta_val) < 0.1 else f"⚠️ {delta_val:+.1f}% vom Ziel"
        
        st.markdown(
            f"<div style='padding:6px 0;'>" 
            f"<span style='font-size:0.85em; color:#ddd;'>Gesamtgewichtung:</span> "
            f"<span style='font-size:1.1em; font-weight:bold;'>{total_weight:.1f}%</span> "
            f"<span style='font-size:0.85em; color:{status_color};'>{status_text}</span>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    # --- GEWICHTUNGS-VALIDIERUNG (Sidebar) ---
    if abs(total_weight - 100) >= 0.1 and len(st.session_state.assets) > 0:
        with st.sidebar:
            st.warning(
                f"### ⚠️ Gewichtung ungültig\n\n"
                f"Aktuelle Summe: **{total_weight:.1f}%**\n\n"
                "Die Gesamtgewichtung muss genau 100% ergeben.",
                icon="📊"
            )

    # --- REACTIVE BUDGET WARNING (Sidebar) ---
    # Simulation dates for budget calculation
    start_date_sim = st.session_state.sim_start_date
    end_date_sim = st.session_state.sim_end_date
    months_sim = ((end_date_sim.year - start_date_sim.year) * 12 + (end_date_sim.month - start_date_sim.month))
    
    # Wir berechnen die projizierte Gesamteinzahlung NACH dem Editor
    # FIX: Lese direkt aus Session State
    proj_total_invest = 0
    for idx, a in enumerate(st.session_state.assets):
        current_w = a.get("Gewichtung (%)", 0)
        init_val = (st.session_state.editable_einmalerlag * current_w) / 100
        rate_val = (st.session_state.editable_sparrate * current_w) / 100
        inter_val = a.get("Spar-Intervall", "monatlich")
        
        asset_total = init_val
        if inter_val == "monatlich": asset_total += rate_val * months_sim
        elif inter_val == "vierteljährlich": asset_total += rate_val * (months_sim // 3)
        elif inter_val == "jährlich": asset_total += rate_val * (months_sim // 12)
        proj_total_invest += asset_total

    if budget_limit > 0 and proj_total_invest > budget_limit:
        with st.sidebar:
            st.error(
                f"### 🚨 Budget-Warnung!\n\n"
                f"**Limit:** € {budget_limit:,.0f}\n"
                f"**Geplant:** € {proj_total_invest:,.0f}\n"
                f"**Überschreitung:** € {proj_total_invest - budget_limit:,.0f}\n\n"
                "Bitte passen Sie die Positionen an, bis die Summe wieder im Rahmen liegt.",
                icon="🚨"
            )
            st.markdown('<div role="status" aria-live="polite" aria-label="Budget Warnung aktiv"></div>', unsafe_allow_html=True)
    
    st.markdown('<div style="margin-bottom: 30px;"></div>', unsafe_allow_html=True)

    # =====================================================================
    # SECTION 2: TOGGLE BUTTONS & FORMS (Below products)
    # =====================================================================
    
    # Toggle state initialization
    if "show_add_form" not in st.session_state:
        st.session_state.show_add_form = False
        
    def toggle_add_form():
        st.session_state.show_add_form = not st.session_state.show_add_form

    if "show_cost_settings" not in st.session_state:
        st.session_state.show_cost_settings = False
        
    def toggle_cost_settings():
        st.session_state.show_cost_settings = not st.session_state.show_cost_settings

    # Beide Buttons nebeneinander (Größer & Kompakt)
    # Ratio [1, 1, 1.5] macht die Buttons ca. 30% breiter als vorher ([0.25...])
    col_add_btn, col_cost_btn, col_spacer = st.columns([1, 1, 1.5])
    
    with col_add_btn:
        btn_label_add = "Titel verbergen" if st.session_state.show_add_form else "Titel hinzufügen"
        st.button(btn_label_add, on_click=toggle_add_form, use_container_width=True, help="Titel zum Portfolio hinzufügen oder verbergen")
    
    with col_cost_btn:
        btn_label_cost = "Kosten verbergen" if st.session_state.show_cost_settings else "Kosten anzeigen"
        st.button(btn_label_cost, on_click=toggle_cost_settings, use_container_width=True, help="Kosten Einstellungen anzeigen oder verbergen")


    # Add Form (wenn sichtbar)
    if st.session_state.show_add_form:
        # Callback für Hinzufügen
        def handle_add_click():
            name_to_add = ""
            isin_to_add = ""
            is_valid = False
            
            # Werte aus dem Formular lesen
            interval = st.session_state.widget_add_interval

            if st.session_state.katalog_auswahl != "Bitte wählen...":
                name_to_add = st.session_state.katalog_auswahl
                isin_to_add = KATALOG[st.session_state.katalog_auswahl]
                is_valid = True
            elif st.session_state.manuelle_isin:
                isin_to_add = st.session_state.manuelle_isin
                with st.spinner(f"Prüfe Ticker {isin_to_add}..."):
                    is_valid, message_or_name = backend_simulation.validate_and_get_info(isin_to_add)
                    if is_valid:
                        name_to_add = message_or_name
                    else:
                        st.session_state.add_error_message = f"Fehler: {message_or_name}"
            
            if is_valid and isin_to_add:
                # Asset hinzufügen mit Gewichtung
                # FIX Bug #5: Kein Auto-Rebalancing mehr, User-Input wird respektiert
                # Neuer Workflow: Assets mit 0% hinzufügen, User passt in Tabelle an
                gesamt_einmalerlag = st.session_state.editable_einmalerlag
                gesamt_sparrate = st.session_state.editable_sparrate
                
                st.session_state.assets.append({
                    "Name": name_to_add,
                    "ISIN / Ticker": isin_to_add,
                    "Gewichtung (%)": 0.0,  # GEÄNDERT: Immer 0% beim Hinzufügen
                    "Einmalerlag (€)": 0.0,
                    "Sparbetrag (€)": 0.0,
                    "Spar-Intervall": interval,
                })
                
                # ENTFERNT: Keine automatische Gleichverteilung mehr (Bug #5 Fix)
                # User setzt Gewichtung selbst in der Tabelle
                
                st.toast(f"'{name_to_add}' erfolgreich hinzugefügt! Bitte Gewichtung in der Tabelle setzen.", icon="✅")
                # Reset der Inputs
                st.session_state.katalog_auswahl = "Bitte wählen..."
                st.session_state.manuelle_isin = ""

        # Formular - PLATZSPARENDES LAYOUT
        with st.container(border=True):
            with st.form(key="add_title_form", clear_on_submit=False):
                
                # Zeile 1: Katalog & ISIN - Nutzt 75% der Breite [1.5, 1.5, 1]
                col_sel1, col_sel2, _ = st.columns([1.5, 1.5, 1])
                with col_sel1:
                    st.selectbox("Titel aus Katalog wählen", KATALOG.keys(), key="katalog_auswahl")
                with col_sel2:
                    st.text_input("Oder ISIN / Ticker manuell eingeben", key="manuelle_isin", placeholder="z.B. US0378331005")
                
                # Zeile 2: Intervall + Button in einer Reihe -> Sehr kompakt (Gewichtung entfernt)
                col_val1, col_val2, col_btn = st.columns([1, 1, 1])
                with col_val1:
                    st.selectbox("Intervall", ["monatlich", "vierteljährlich", "jährlich"], key="widget_add_interval")
                with col_val2:
                    st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
                with col_btn:
                    st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
                    st.form_submit_button("Titel Hinzufügen", use_container_width=True, type="primary", on_click=handle_add_click)
        
        # Fehlermeldung anzeigen (nach Formular, gut sichtbar)
        if "add_error_message" in st.session_state and st.session_state.add_error_message:
            st.error(st.session_state.add_error_message)
            st.session_state.add_error_message = None  # Reset nach Anzeige


    # --- 2. KOSTEN SETTINGS CONTAINER (only shows when toggled) ---

    if st.session_state.show_cost_settings:
        # Container mit Rahmen für bessere Optik
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.session_state.cost_ausgabe = st.number_input(
                    "Ausgabeaufschlag (%)", 0.0, 10.0, 
                    value=st.session_state.cost_ausgabe, step=0.1,
                    help="Einmalige Gebühr beim Kauf eines Fonds, wird vom Anlagebetrag abgezogen."
                )
            with c2:
                st.session_state.cost_management = st.number_input(
                    "Managementgebühr (% p.a.)", 0.0, 10.0, 
                    value=st.session_state.cost_management, step=0.01,
                    help="Jährliche Verwaltungsgebühr, die vom Fondsvermögen abgezogen wird."
                )
            with c3:
                st.session_state.cost_depot = st.number_input(
                    "Depotgebühr (€ p.a.)", 0.0, 
                    value=st.session_state.cost_depot, step=1.0,
                    help="Jährliche Gebühr für die Verwahrung des Depots."
                )


    # --- 3. AUTOMATISCHE BERECHNUNG (HISTORIE) ---
    simulation_successful = False
    
    # Check if calculation is needed (Assets changed, dates changed, or results missing)
    # WICHTIG: Deep Copy der Assets, damit auch Änderungen in Dict-Werten erkannt werden!
    # FIX: Auch editable_einmalerlag und editable_sparrate tracken für Neuberechnung
    calc_relevant_state = {
        "assets": copy.deepcopy(st.session_state.assets),  # Deep Copy für Dict-Änderungen
        "start_date": st.session_state.sim_start_date,
        "end_date": st.session_state.sim_end_date,
        "ausgabe": st.session_state.cost_ausgabe,
        "mgmt": st.session_state.cost_management,
        "depot": st.session_state.cost_depot,
        "einmalerlag": st.session_state.editable_einmalerlag,  # NEU: Trigger bei Änderung
        "sparrate": st.session_state.editable_sparrate  # NEU: Trigger bei Änderung
    }
    
    if "last_calc_state" not in st.session_state:
        st.session_state.last_calc_state = None
        
    needs_recalc = (st.session_state.last_calc_state != calc_relevant_state) or (st.session_state.simulations_daten is None)
    
    assets_to_simulate = [asset for asset in st.session_state.assets if asset.get("ISIN / Ticker")]
    
    # Initialisierung VOR den Bedingungsblöcken (verhindert NameError)
    simulation_successful = False
    
    if assets_to_simulate:
        if needs_recalc:
            with st.spinner("Berechne Portfolio..."):
                 # Historie nutzt automatisch inflation.py via portfolio_logic
                 sim_data, hist_returns, final_values = portfolio_logic.run_portfolio_simulation(
                    assets=assets_to_simulate,
                    start_date=st.session_state.sim_start_date,
                    end_date=st.session_state.sim_end_date,
                    ausgabeaufschlag_pct=st.session_state.cost_ausgabe,
                    managementgebuehr_pa_pct=st.session_state.cost_management,
                    depotgebuehr_pa_eur=st.session_state.cost_depot,
                )
                 if sim_data is not None:
                     st.session_state.simulations_daten = sim_data
                     st.session_state.historical_returns_pa = hist_returns
                     st.session_state.asset_final_values = final_values
                     st.session_state.last_calc_state = calc_relevant_state # Update state nach Erfolg
                     
                     for name, value in hist_returns.items():
                        if name not in st.session_state.prognosis_assumptions_pa:
                            st.session_state.prognosis_assumptions_pa[name] = value
                            
                     # --- AUTOMATISCHE PROGNOSEBERECHNUNG ---
                     start_capital_from_table = sum(
                         asset.get("Einmalerlag (€)", 0.0) 
                         for asset in st.session_state.assets 
                         if asset.get("ISIN / Ticker")
                     )
                     
                     start_vals = {
                         "letzter_tag": date.today(),
                         "nominal": start_capital_from_table,
                         "real": start_capital_from_table,
                         "einzahlung": start_capital_from_table
                     }
                     
                     st.session_state.prognose_daten = prognose_logic.run_forecast(
                         start_values=start_vals,
                         assets=st.session_state.assets,
                         prognose_jahre=st.session_state.prognose_jahre,
                         sparplan_fortfuehren=FIXED_SPARPLAN_ACTIVE,
                         kosten_management_pa_pct=st.session_state.cost_management,
                         kosten_depot_pa_eur=st.session_state.cost_depot,
                         ausgabeaufschlag_pct=st.session_state.cost_ausgabe,
                         expected_asset_returns_pa=st.session_state.prognosis_assumptions_pa,
                         asset_final_values=st.session_state.asset_final_values,
                         expected_volatility_pa=FIXED_VOLATILITY,
                         n_simulations=FIXED_N_SIMULATIONS
                     )
                     
                     st.session_state.last_calc_state = calc_relevant_state
                     simulation_successful = True
        else:
            # Daten sind bereits aktuell im Session State
            simulation_successful = True
    else:
        st.info("Bitte füge Titel zum Portfolio hinzu, um die Simulation zu starten.")


    # --- 4. NAVIGATION TABS (Historie vs. Zukunft) ---
    st.markdown("---")
    
    if simulation_successful:
        
        def update_sub_nav():
            st.session_state.sim_sub_nav_state = st.session_state.sim_sub_nav_widget

        current_idx = 0 if st.session_state.sim_sub_nav_state == "Historische Simulation" else 1
        
        st.radio(
            "Ansicht wählen:", 
            options=["Historische Simulation", "Zukunftsprognose"], 
            index=current_idx,
            key="sim_sub_nav_widget", 
            on_change=update_sub_nav,
            horizontal=True,
            label_visibility="collapsed",
            help="Ansicht: Wählen Sie zwischen Historischer Simulation und Zukunftsprognose"
        )
        
        # --- PDF REPORT LOGIK ---
        # --- PDF REPORT LOGIK ---
        def show_pdf_download_button(key_suffix):
            """Zeigt PDF-Download-Button und handled den Download."""
            from .pdf_report import create_pdf_with_charts
            from . import plotting
            
            if st.session_state.simulations_daten is None:
                return
            
            if st.button("PDF Report erstellen & herunterladen", 
                        key=f"btn_gen_pdf_{key_suffix}", 
                        use_container_width=True, 
                        type="primary"):
                
                with st.spinner("Erstelle PDF Report..."):
                    pdf_bytes = create_pdf_with_charts(
                        assets=st.session_state.assets,
                        simulations_daten=st.session_state.simulations_daten,
                        prognose_daten=st.session_state.prognose_daten,
                        handover_data=st.session_state.handover_data,
                        historical_returns_pa=st.session_state.historical_returns_pa,
                        prognosis_assumptions_pa=st.session_state.prognosis_assumptions_pa,
                        sim_start_date=st.session_state.sim_start_date,
                        sim_end_date=st.session_state.sim_end_date,
                        prognose_jahre=st.session_state.prognose_jahre,
                        cost_ausgabe=st.session_state.cost_ausgabe,
                        cost_management=st.session_state.cost_management,
                        cost_depot=st.session_state.cost_depot,
                        editable_budget=st.session_state.editable_budget,
                        editable_einmalerlag=st.session_state.editable_einmalerlag,
                        editable_sparrate=st.session_state.editable_sparrate,
                        plotting_module=plotting
                    )
                    
                    if pdf_bytes is None:
                        st.toast("⚠️ PDF kann nur bei 100% Gewichtung erstellt werden!", icon="📊")
                        return
                    
                    st.session_state[f"pdf_data_{key_suffix}"] = pdf_bytes
                    st.session_state[f"pdf_trigger_{key_suffix}"] = True
            
            # JS-Download-Trigger (unverändert)
            if st.session_state.get(f"pdf_trigger_{key_suffix}"):
                pdf_data = st.session_state[f"pdf_data_{key_suffix}"]
                b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                filename = f"Gutmann_Report_{date.today()}.pdf"
                
                js_download = f"""
                    <script>
                        var link = document.createElement('a');
                        link.href = 'data:application/pdf;base64,{b64_pdf}';
                        link.download = '{filename}';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                    </script>
                """
                placeholder = st.empty()
                with placeholder:
                    components.html(f"<html><body>{js_download}</body></html>", height=0)
                
                st.session_state[f"pdf_trigger_{key_suffix}"] = False
                st.success("✅ Download gestartet!")
        
        # === SUB-TAB: HISTORISCHE SIMULATION ===
        if st.session_state.sim_sub_nav_state == "Historische Simulation":
                        
            def update_start_date():
                st.session_state.sim_start_date = st.session_state.widget_start_date
            def update_end_date():
                st.session_state.sim_end_date = st.session_state.widget_end_date

            d_col1, d_col2, d_col3, _ = st.columns([1, 1, 1, 3])
            
            with d_col1:
                st.date_input(
                    "Startdatum", 
                    value=st.session_state.sim_start_date,
                    min_value=date(1980, 1, 1), 
                    max_value=date.today(), 
                    key="widget_start_date",
                    on_change=update_start_date
                )
            with d_col2:
                st.date_input(
                    "Enddatum", 
                    value=st.session_state.sim_end_date,
                    max_value=date.today(), 
                    key="widget_end_date",
                    on_change=update_end_date
                )
            
            with d_col3:
                # EIGENES DESIGN: "Segmented Control" statt Toggle
                st.markdown("<p style='font-size: 0.8rem; margin-bottom: 0px;'>📉 Marktphasen anzeigen</p>", unsafe_allow_html=True)
                phases_radio = st.radio(
                    "Marktphasen anzeigen", 
                    options=["Ja", "Nein"], 
                    index=1,
                    horizontal=True,
                    label_visibility="collapsed",
                    key="widget_show_phases",
                    help="Marktphasen im Chart farblich hervorheben (Ja/Nein)"
                )
                show_market_phases = (phases_radio == "Ja")

            hist_returns = st.session_state.historical_returns_pa
            if hist_returns:
                cols = st.columns(len(hist_returns))
                for i, (name, rendite_pa) in enumerate(hist_returns.items()):
                    with cols[i]:
                        st.metric(f"{name}", f"{rendite_pa:,.2f} % p.a.")
            
            chart_col, kpi_col = st.columns([3, 1])
            with chart_col:
                fig = plotting.create_simulation_chart(
                    st.session_state.simulations_daten, 
                    None, 
                    title="Historisches Portfolio",
                    show_crisis_events=show_market_phases
                ) 
                st.plotly_chart(fig, use_container_width=True)
            
            with kpi_col:
                st.markdown('<div style="margin-top: 25px;"></div>', unsafe_allow_html=True)
                last_row = st.session_state.simulations_daten.iloc[-1]
                end_value_nominal = last_row["Portfolio (nominal)"]
                end_value_real = last_row["Portfolio (real)"]
                total_investment = last_row["Einzahlungen (brutto)"]
                rendite_nominal_prozent = ((end_value_nominal / total_investment) - 1) * 100 if total_investment > 0 else 0
                
                st.metric("Gesamteinzahlung", f"€ {total_investment:,.2f}", help="Summe aller getätigten Einzahlungen (Einmalerlag + Sparraten).")
                st.metric("Endkapital (nominal)", f"€ {end_value_nominal:,.2f}", help="Wert des Portfolios ohne Inflationsanpassung.")
                st.metric("Endkapital (real)", f"€ {end_value_real:,.2f}", help="Kaufkraftbereinigt (basierend auf HICP Daten)")
                st.metric("Gesamtrendite (nom.)", f"{rendite_nominal_prozent:,.2f} %", help="Prozentuale Rendite auf Basis des nominalen Endkapitals.")
                
                # Max Drawdown KPI (NEU)
                max_dd, peak_date, trough_date = portfolio_logic.calculate_max_drawdown(st.session_state.simulations_daten)
                if max_dd < 0 and peak_date is not None:
                    dd_range = f"{peak_date.strftime('%d.%m.%Y')} - {trough_date.strftime('%d.%m.%Y')}"
                    st.metric(
                        "Max. Drawdown", 
                        f"{max_dd:,.1f} %",
                        delta=dd_range,
                        delta_color="off",
                        help="Größter Verlust vom Allzeithoch während des Simulationszeitraums."
                    )
                
                st.markdown("---")
                # PDF BUTTON HISTORIE
                show_pdf_download_button("hist")
                
                # CHECKOUT BUTTON (NEU)
                from .checkout_service import render_finish_button
                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                render_finish_button("hist")



        # === SUB-TAB: ZUKUNFTSPROGNOSE ===
        elif st.session_state.sim_sub_nav_state == "Zukunftsprognose":
            
            # Cleanup
            current_active_names = [a.get("Name") for a in st.session_state.assets if a.get("Name")]
            for existing_key in list(st.session_state.prognosis_assumptions_pa.keys()):
                if existing_key not in current_active_names:
                    del st.session_state.prognosis_assumptions_pa[existing_key]

            def update_assumption(asset_name):
                val = st.session_state[f"assumption_{asset_name}"]
                st.session_state.prognosis_assumptions_pa[asset_name] = val
            
            def update_prognose_jahre():
                st.session_state.prognose_jahre = st.session_state.widget_prognose_jahre

            def run_prognose_logic():
                current_assumptions = st.session_state.prognosis_assumptions_pa
                
                start_capital_from_table = 0.0
                for asset in st.session_state.assets:
                    if asset.get("ISIN / Ticker"):
                        start_capital_from_table += asset.get("Einmalerlag (€)", 0.0)
                
                start_vals = {
                    "letzter_tag": date.today(),
                    "nominal": start_capital_from_table,
                    "real": start_capital_from_table,
                    "einzahlung": start_capital_from_table
                }
                
                st.session_state.prognose_daten = prognose_logic.run_forecast(
                    start_values=start_vals,
                    assets=st.session_state.assets,
                    prognose_jahre=st.session_state.prognose_jahre,
                    sparplan_fortfuehren=FIXED_SPARPLAN_ACTIVE, 
                    kosten_management_pa_pct=st.session_state.cost_management,
                    kosten_depot_pa_eur=st.session_state.cost_depot,
                    # inflation_rate_pa=st.session_state.inflation_slider, <-- ENTFERNT
                    ausgabeaufschlag_pct=st.session_state.cost_ausgabe,
                    expected_asset_returns_pa=current_assumptions,
                    asset_final_values=st.session_state.asset_final_values,
                    expected_volatility_pa=FIXED_VOLATILITY,
                    n_simulations=FIXED_N_SIMULATIONS
                )

            # SLIDER ENTFERNT - Nur noch Jahre und Rendite Inputs
            var_col_yr, var_col_ret = st.columns([1, 2])

            with var_col_yr:
                st.markdown('<div role="heading" aria-level="3" style="font-weight: bold; margin-bottom: 5px;">Prognose-Horizont</div>', unsafe_allow_html=True)
                st.slider(
                    "Prognose-Horizont (Jahre)", 
                    min_value=5, max_value=40, value=st.session_state.prognose_jahre, step=1,
                    key="widget_prognose_jahre",
                    on_change=update_prognose_jahre,
                    help="Zeitraum in Jahren für die Zukunftsprognose",
                    label_visibility="collapsed"
                )
                
                # Zukunfts-Jahr berechnen
                target_year = date.today().year + st.session_state.prognose_jahre
                st.caption(f"Prognose bis Jahr: **{target_year}**")

            with var_col_ret:
                st.markdown('<div role="heading" aria-level="3" style="font-weight: bold; margin-bottom: 5px;">Erwartete Rendite (p.a.) je Titel</div>', unsafe_allow_html=True)
                current_asset_names = list(st.session_state.prognosis_assumptions_pa.keys())

                if current_asset_names:
                    cols_per_row = 3
                    grid_cols = st.columns(cols_per_row)
                    
                    for i, name in enumerate(current_asset_names):
                        val = st.session_state.prognosis_assumptions_pa[name]
                        with grid_cols[i % cols_per_row]:
                            st.number_input(
                                f"{name} (%)", 
                                value=val, 
                                key=f"assumption_{name}", 
                                step=0.5,
                                on_change=update_assumption,
                                args=(name,)
                            )
                else:
                    st.info("Keine aktiven Titel für die Prognose.")

            # Berechnung
            run_prognose_logic()

            # Grafik & Ergebnisse
            if st.session_state.prognose_daten is not None:
                
                chart_col, kpi_col = st.columns([3, 1])
                
                with chart_col:
                    fig_prog = plotting.create_simulation_chart(
                        None, 
                        st.session_state.prognose_daten, 
                        title="Prognostizierte Entwicklung (Monte Carlo)"
                    )
                    st.plotly_chart(fig_prog, use_container_width=True)
                    
                    st.markdown(f"""
                    <div style="background-color: {GUTMANN_SECONDARY_DARK}; padding: 15px; border-radius: 5px; border-left: 5px solid {GUTMANN_ACCENT_GREEN}; color: {GUTMANN_LIGHT_TEXT}; font-size: 0.95em;" role="region" aria-label="Lesehilfe zur Grafik">
                        <strong style="color: {GUTMANN_ACCENT_GREEN}; font-size: 1.05em;">ℹ️ Lesehilfe zur Grafik:</strong><br>
                        <ul style="margin-top: 5px; padding-left: 20px; margin-bottom: 0;">
                            <li>Das <b>Optimistische Szenario (95%)</b> zeigt eine Entwicklung, die statistisch nur in besonders guten Marktphasen erreicht wird.</li>
                            <li>Das <b>Pessimistisches Szenario (5%)</b> markiert eine Entwicklung, die selbst in sehr schlechten Phasen nur selten unterschritten wird.</li>
                            <li>Die <b style="color: #1E90FF;">Median-Linie (Blau)</b> ist das statistisch wahrscheinlichste Ergebnis (50/50 Chance).</li>
                            <li><em style="color: cyan;">Hinweis:</em> Die Türkise Linie (Real) ist inflationsbereinigt (basierend auf HICP Daten & Modellannahmen).</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)

                with kpi_col:
                    st.markdown('<div style="margin-top: 25px;"></div>', unsafe_allow_html=True)
                    
                    last_row_prog = st.session_state.prognose_daten.iloc[-1]
                    start_capital_planned = st.session_state.prognose_daten.iloc[0]["Einzahlungen (brutto)"]
                    end_val_nom = last_row_prog["Portfolio (Median)"]
                    end_val_real = last_row_prog["Portfolio (Real_Median)"]
                    total_invest_end = last_row_prog["Einzahlungen (brutto)"]
                    future_savings_sum = total_invest_end - start_capital_planned
                    rendite_nom = ((end_val_nom / total_invest_end) - 1) * 100 if total_invest_end > 0 else 0
                    
                    st.metric("Startkapital (Geplant)", f"€ {start_capital_planned:,.2f}", help="Summe der Einmalerläge aus der Asset-Liste")
                    st.metric("+ Zukünftige Sparraten", f"€ {future_savings_sum:,.2f}", help="Summe der Sparraten in der Prognose-Zeit")
                    st.metric("Endkapital (Median, nom.)", f"€ {end_val_nom:,.2f}", help="Der wahrscheinlichste Endwert (50% Chance höher/niedriger).")
                    st.metric("Rendite (auf Gesamt)", f"{rendite_nom:,.2f} %", help="Rendite bezogen auf Startkapital + Sparraten")
                    st.metric("Endkapital (real)", f"€ {end_val_real:,.2f}", help="Kaufkraftbereinigt nach Inflationsmodell")
                    
                    st.markdown("---")
                    # PDF BUTTON PROGNOSE
                    show_pdf_download_button("prog")

                    # CHECKOUT BUTTON (NEU)
                    from .checkout_service import render_finish_button
                    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                    render_finish_button("prog")
    
    # --- CONDITIONAL RERUN AM ENDE ---
    # Wenn Input-Felder geändert wurden, triggere einen Rerun
    # Dies passiert NACH allen Button-Clicks, sodass Buttons nicht unterbrochen werden
    if st.session_state.needs_rerun:
        st.session_state.needs_rerun = False
        st.rerun()