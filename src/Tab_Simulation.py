import streamlit as st
from datetime import date
import numpy as np
import yfinance as yf
import base64
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
        st.markdown("**👤 BERATER**")
        st.text_input(
            "Name des Beraters", 
            value=handover.get("advisor", "Mag. Anna Berger")[:30],
            disabled=True, 
            key="ro_advisor",
            label_visibility="collapsed"
        )
    
    with header_col2:
        st.markdown("**🤝 KUNDE**")
        st.text_input(
            "Name des Kunden", 
            value=handover.get("client", "Max Mustermann")[:30],
            disabled=True, 
            key="ro_client",
            label_visibility="collapsed"
        )
    
    with header_col3:
        # Header für Portfolio Bereich
        st.markdown("**💼 PORTFOLIO-ÜBERSICHT**")
        
        # Werte aus Handover-Daten (nicht berechnet!)
        budget = handover.get("budget", 0)
        einmalerlag_display = handover.get("einmalerlag", 0)
        sparrate_display = handover.get("savings_rate", 0)
        portfolio_type_display = handover.get("portfolio_type", "Manuell")
        
        # Premium 2x2 Grid mit Rahmen
        with st.container(border=True):
            r1c1, r1c2 = st.columns(2)
            r2c1, r2c2 = st.columns(2)
            
            with r1c1:
                st.metric("Budget", f"€ {budget:,.0f}")
            with r1c2:
                st.metric("Einmalerlag", f"€ {einmalerlag_display:,.0f}")
            
            with r2c1:
                st.metric("Sparrate", f"€ {sparrate_display:,.0f}")
            with r2c2:
                # Truncate portfolio name if too long
                trunc_type = str(portfolio_type_display) if portfolio_type_display else "Manuell"
                if len(trunc_type) > 15:
                    # Suche nach Klammer oder kürze hart
                    if "(" in trunc_type:
                        trunc_type = trunc_type.split("(")[0].strip()
                    else:
                        trunc_type = trunc_type[:12] + "..."
                
                st.metric("Portfolio Type", trunc_type)
    
    st.markdown("---")

    # Budget Limit für spätere Verwendung (Sidebar Warnung)
    budget_limit = handover.get("budget", 0)
    
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
    
    st.subheader("Empfohlene Produkte")
    
    # Hilfsfunktion: Gewichte neu berechnen wenn sich etwas ändert
    gesamt_einmalerlag = handover.get("einmalerlag", 0)
    gesamt_sparrate = handover.get("savings_rate", 0)
    
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

    /* Special compacting for text inputs in the table */
    div[data-testid="stTextInput"] input {
        padding: 4px 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Layout für Tabelle (Links 55%, Rechts für Hilfe/Info 45%)
    col_main, col_spacer = st.columns([0.55, 0.45])
    
    with col_main:
        # Wrapper für das gesamte Product-Table Layout
        st.markdown('<div class="product-table">', unsafe_allow_html=True)
        
        # HEADER ROW - Centered via CSS
        st.markdown('<div class="table-header">', unsafe_allow_html=True)
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
            st.markdown("**Sparbetrag (€)**")
        with h6:
            st.markdown("**Spar-Intervall**")
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
                    st.markdown(f"{name}")
                
                with c2:
                    st.caption(ticker)
                
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
                    # Einmalbetrag editierbar
                    current_weight = st.session_state.assets[idx].get("Gewichtung (%)", 0.0)
                    einmalerlag_val = (gesamt_einmalerlag * current_weight) / 100
                    e_key = f"einmal_text_{idx}"
                    
                    # Callback für Einmalbetrag-Änderung
                    def on_einmal_change(asset_idx=idx, gesamt=gesamt_einmalerlag):
                        try:
                            e_clean = st.session_state[f"einmal_text_{asset_idx}"].replace(".", "").replace(",", ".").replace("€", "").strip()
                            new_e = float(e_clean)
                            if gesamt > 0:
                                st.session_state.assets[asset_idx]["Gewichtung (%)"] = (new_e / gesamt) * 100
                                st.session_state.needs_rerun = True
                        except (ValueError, KeyError):
                            pass
                    
                    st.text_input(
                        "€ Einmal",
                        value=f"{einmalerlag_val:,.0f}".replace(",", "."),
                        key=e_key,
                        label_visibility="collapsed",
                        on_change=on_einmal_change
                    )
                
                with c5:
                    # Sparbetrag editierbar
                    current_weight = st.session_state.assets[idx].get("Gewichtung (%)", 0.0)
                    sparrate_val = (gesamt_sparrate * current_weight) / 100
                    s_key = f"spar_text_{idx}"
                    
                    # Callback für Sparbetrag-Änderung
                    def on_spar_change(asset_idx=idx, gesamt=gesamt_sparrate):
                        try:
                            s_clean = st.session_state[f"spar_text_{asset_idx}"].replace(".", "").replace(",", ".").replace("€", "").strip()
                            new_s = float(s_clean)
                            if gesamt > 0:
                                st.session_state.assets[asset_idx]["Gewichtung (%)"] = (new_s / gesamt) * 100
                                st.session_state.needs_rerun = True
                        except (ValueError, KeyError):
                            pass
                    
                    st.text_input(
                        "€ Spar",
                        value=f"{sparrate_val:,.0f}".replace(",", "."),
                        key=s_key,
                        label_visibility="collapsed",
                        on_change=on_spar_change
                    )
                
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
                    # Delete als plain emoji (kein Button-Style)
                    if st.button("🗑️", key=f"delete_{idx}", help="Titel löschen", use_container_width=False):
                        st.session_state.assets.pop(idx)
                        # KEINE automatische Neuverteilung - User behält Kontrolle!
                        st.session_state.needs_rerun = True
        
        st.markdown('</div>', unsafe_allow_html=True)
    
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
            f"<span style='font-size:0.85em; color:gray;'>Gesamtgewichtung:</span> "
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
    proj_total_invest = 0
    for idx, a in enumerate(st.session_state.assets):
        current_w = a.get("Gewichtung (%)", 0)
        init_val = (gesamt_einmalerlag * current_w) / 100
        rate_val = (gesamt_sparrate * current_w) / 100
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
            if "last_warn_val" not in st.session_state or st.session_state.last_warn_val != proj_total_invest:
                st.toast(f"⚠️ Budget um € {proj_total_invest - budget_limit:,.0f} überschritten!", icon="🚨")
                st.session_state.last_warn_val = proj_total_invest
    
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

    # Beide Buttons nebeneinander
    col_add_btn, col_cost_btn, col_spacer = st.columns([1.5, 1.5, 1])
    
    with col_add_btn:
        btn_label_add = "💰 Titel verbergen" if st.session_state.show_add_form else "💰 Titel zum Portfolio hinzufügen"
        st.button(btn_label_add, use_container_width=True, on_click=toggle_add_form)
    
    with col_cost_btn:
        btn_label_cost = "💸 Kosten verbergen" if st.session_state.show_cost_settings else "💸 Kosten Einstellungen anzeigen"
        st.button(btn_label_cost, use_container_width=True, on_click=toggle_cost_settings)


    # Add Form (wenn sichtbar)
    if st.session_state.show_add_form:
        # Callback für Hinzufügen
        def handle_add_click():
            name_to_add = ""
            isin_to_add = ""
            is_valid = False
            
            # Werte aus dem Formular lesen
            weight_input = st.session_state.widget_add_weight
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
                        st.toast(f"Fehler: {message_or_name}", icon="❌")
            
            if is_valid and isin_to_add:
                # Asset hinzufügen mit Gewichtung
                gesamt_einmalerlag = st.session_state.handover_data.get("einmalerlag", 0)
                gesamt_sparrate = st.session_state.handover_data.get("savings_rate", 0)
                
                st.session_state.assets.append({
                    "Name": name_to_add,
                    "ISIN / Ticker": isin_to_add,
                    "Gewichtung (%)": weight_input,
                    "Einmalerlag (€)": (gesamt_einmalerlag * weight_input) / 100,
                    "Sparbetrag (€)": (gesamt_sparrate * weight_input) / 100,
                    "Spar-Intervall": interval,
                })
                
                # GLEICHVERTEILUNG: Alle Gewichte neu verteilen
                num_assets = len(st.session_state.assets)
                if num_assets > 0:
                    equal_weight = 100.0 / num_assets
                    for asset in st.session_state.assets:
                        asset["Gewichtung (%)"] = equal_weight
                        asset["Einmalerlag (€)"] = (gesamt_einmalerlag * equal_weight) / 100
                        asset["Sparbetrag (€)"] = (gesamt_sparrate * equal_weight) / 100
                
                st.toast(f"'{name_to_add}' erfolgreich hinzugefügt!", icon="✅")
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
                
                # Zeile 2: Beträge + Button in einer Reihe -> Sehr kompakt
                col_val1, col_val2, col_val3, col_btn = st.columns([1, 1, 1, 1])
                with col_val1:
                    # DEFAULT-Gewichtung berechnen
                    if len(st.session_state.assets) > 0:
                        default_weight = 100.0 / (len(st.session_state.assets) + 1)
                    else:
                        default_weight = 100.0
                    st.number_input("Gewichtung (%)", min_value=0.0, max_value=100.0, value=float(default_weight), step=1.0, key="widget_add_weight")
                with col_val2:
                    st.selectbox("Intervall", ["monatlich", "vierteljährlich", "jährlich"], key="widget_add_interval")
                with col_val3:
                    st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
                with col_btn:
                    st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
                    st.form_submit_button("Titel Hinzufügen", use_container_width=True, type="primary", on_click=handle_add_click)




    # --- 2. KOSTEN SETTINGS CONTAINER (only shows when toggled) ---

    if st.session_state.show_cost_settings:
        # Container mit Rahmen für bessere Optik
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.session_state.cost_ausgabe = st.number_input("Ausgabeaufschlag (%)", 0.0, 10.0, value=st.session_state.cost_ausgabe, step=0.1)
            with c2:
                st.session_state.cost_management = st.number_input("Managementgebühr (% p.a.)", 0.0, 10.0, value=st.session_state.cost_management, step=0.01)
            with c3:
                st.session_state.cost_depot = st.number_input("Depotgebühr (€ p.a.)", 0.0, value=st.session_state.cost_depot, step=1.0)


    # --- 3. AUTOMATISCHE BERECHNUNG (HISTORIE) ---
    simulation_successful = False
    
    # Check if calculation is needed (Assets changed, dates changed, or results missing)
    # WICHTIG: list(...) Erzeugt eine Kopie, damit Änderungen erkannt werden!
    calc_relevant_state = {
        "assets": list(st.session_state.assets), 
        "start_date": st.session_state.sim_start_date,
        "end_date": st.session_state.sim_end_date,
        "ausgabe": st.session_state.cost_ausgabe,
        "mgmt": st.session_state.cost_management,
        "depot": st.session_state.cost_depot
    }
    
    if "last_calc_state" not in st.session_state:
        st.session_state.last_calc_state = None
        
    needs_recalc = (st.session_state.last_calc_state != calc_relevant_state) or (st.session_state.simulations_daten is None)
    
    assets_to_simulate = [asset for asset in st.session_state.assets if asset.get("ISIN / Ticker")]
    
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
            label_visibility="collapsed"
        )
        
        # --- PDF REPORT LOGIK ---
        # --- PDF REPORT LOGIK ---
        def show_pdf_download_button(key_suffix):
            # Prüfen ob überhaupt Daten da sind
            if st.session_state.simulations_daten is None:
                return

            # A) KPIs für Historie sammeln
            hist_kpis_dict = {}
            if st.session_state.simulations_daten is not None:
                last_row = st.session_state.simulations_daten.iloc[-1]
                total_invest = last_row['Einzahlungen (brutto)']
                end_val = last_row['Portfolio (nominal)']
                profit = end_val - total_invest
                rendite_abs = (profit / total_invest * 100) if total_invest > 0 else 0
                
                # Dictionary für die PDF-Tabelle
                hist_kpis_dict = {
                    "Gesamteinzahlung": f"EUR {total_invest:,.2f}",
                    "Endkapital (nominal)": f"EUR {end_val:,.2f}",
                    "Gewinn/Verlust": f"EUR {profit:,.2f}",
                    "Rendite (absolut)": f"{rendite_abs:.2f} %",
                    "Endkapital (real)": f"EUR {last_row['Portfolio (real)']:,.2f}"
                }

            # B) KPIs für Prognose sammeln (nur wenn vorhanden!)
            prog_kpis_dict = {}
            if st.session_state.prognose_daten is not None:
                last_row_p = st.session_state.prognose_daten.iloc[-1]
                start_cap = st.session_state.prognose_daten.iloc[0]['Einzahlungen (brutto)']
                end_median = last_row_p['Portfolio (Median)']
                # Rendite auf Gesamtinvest
                rendite_prog = ((end_median / last_row_p['Einzahlungen (brutto)']) - 1) * 100
                
                prog_kpis_dict = {
                    "Startkapital (Ist-Stand)": f"EUR {start_cap:,.2f}",
                    "Geplante Sparraten (Summe)": f"EUR {(last_row_p['Einzahlungen (brutto)'] - start_cap):,.2f}",
                    "Endkapital (Median, nominal)": f"EUR {end_median:,.2f}",
                    "Rendite Erwartungswert": f"{rendite_prog:.2f} %",
                    "Endkapital (Real, Median)": f"EUR {last_row_p['Portfolio (Real_Median)']:,.2f}"
                }
            
            # Globale Params für Seite 1
            global_params = {
                "Prognose-Horizont": f"{st.session_state.prognose_jahre} Jahre",
                "Ausgabeaufschlag": f"{st.session_state.cost_ausgabe} %",
                "Managementgebühr": f"{st.session_state.cost_management} % p.a.",
                "Depotgebühr": f"{st.session_state.cost_depot} EUR p.a."
            }

            # Funktion zum Generieren der PDF
            def generate_pdf_for_download():
                # VALIDIERUNG: Nur bei 100% Gewichtung
                total_w = sum(a.get("Gewichtung (%)", 0) for a in st.session_state.assets)
                if abs(total_w - 100) > 0.1:
                    st.toast("⚠️ PDF kann nur bei einer Gesamtgewichtung von 100% erstellt werden!", icon="📊")
                    return

                # 1. Historie Chart neu erstellen (für sauberen Look)
                fig_hist = plotting.create_simulation_chart(
                    st.session_state.simulations_daten, 
                    None, 
                    title="Historische Entwicklung",
                    show_crisis_events=False
                )
                
                # 2. Prognose Chart neu erstellen (nur wenn Daten da)
                fig_prog = None
                if st.session_state.prognose_daten is not None:
                    fig_prog = plotting.create_simulation_chart(
                        None,
                        st.session_state.prognose_daten,
                        title="Zukunftsprognose"
                    )
                
                try:
                    pdf_bytes = generate_pdf_report(
                        assets=st.session_state.assets,
                        global_params=global_params,
                        hist_fig=fig_hist,
                        hist_kpis=hist_kpis_dict,
                        prog_fig=fig_prog,
                        prog_kpis=prog_kpis_dict
                    )
                    st.session_state[f"pdf_data_{key_suffix}"] = pdf_bytes
                    st.session_state[f"pdf_trigger_{key_suffix}"] = True
                except Exception as e:
                    st.error(f"Fehler bei der PDF-Erstellung: {e}")
            
            # Button zum Starten der Generierung
            if st.button("📄 PDF Report erstellen & herunterladen", key=f"btn_gen_pdf_{key_suffix}", use_container_width=True, type="primary"):
                with st.spinner("Erstelle PDF Report..."):
                    generate_pdf_for_download()
            
            # Automatischer JS-Trigger für den Download
            if st.session_state.get(f"pdf_trigger_{key_suffix}"):
                pdf_data = st.session_state[f"pdf_data_{key_suffix}"]
                b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                filename = f"Gutmann_Report_{date.today()}.pdf"
                
                # JavaScript zum automatischen Download
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
                # Nutze st.empty() um Platz zu sparen und Layout-Shifts zu minimieren
                placeholder = st.empty()
                with placeholder:
                    components.html(f"<html><body>{js_download}</body></html>", height=0)
                
                # Trigger zurücksetzen
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
                    key="widget_show_phases"
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
                
                st.metric("Gesamteinzahlung", f"€ {total_investment:,.2f}")
                st.metric("Endkapital (nominal)", f"€ {end_value_nominal:,.2f}")
                st.metric("Endkapital (real)", f"€ {end_value_real:,.2f}", help="Kaufkraftbereinigt (basierend auf HICP Daten)")
                st.metric("Gesamtrendite (nom.)", f"{rendite_nominal_prozent:,.2f} %")
                
                st.markdown("---")
                # PDF BUTTON HISTORIE
                show_pdf_download_button("hist")



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
                st.markdown("**Prognose-Horizont**")
                st.slider(
                    "Jahre", 
                    min_value=5, max_value=30, 
                    value=st.session_state.prognose_jahre, 
                    key="widget_prognose_jahre",
                    on_change=update_prognose_jahre,
                    label_visibility="collapsed"
                )

            with var_col_ret:
                st.markdown("**Erwartete Rendite (p.a.) je Titel**")
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
                    <div style="background-color: {GUTMANN_SECONDARY_DARK}; padding: 15px; border-radius: 5px; border-left: 5px solid {GUTMANN_ACCENT_GREEN}; color: {GUTMANN_LIGHT_TEXT}; font-size: 0.95em;">
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
                    st.metric("Endkapital (Median, nom.)", f"€ {end_val_nom:,.2f}")
                    st.metric("Rendite (auf Gesamt)", f"{rendite_nom:,.2f} %", help="Rendite bezogen auf Startkapital + Sparraten")
                    st.metric("Endkapital (real)", f"€ {end_val_real:,.2f}", help="Kaufkraftbereinigt nach Inflationsmodell")
                    
                    st.markdown("---")
                    # PDF BUTTON PROGNOSE
                    show_pdf_download_button("prog")
    
    # --- CONDITIONAL RERUN AM ENDE ---
    # Wenn Input-Felder geändert wurden, triggere einen Rerun
    # Dies passiert NACH allen Button-Clicks, sodass Buttons nicht unterbrochen werden
    if st.session_state.needs_rerun:
        st.session_state.needs_rerun = False
        st.rerun()