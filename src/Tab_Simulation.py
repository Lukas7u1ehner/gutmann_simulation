import streamlit as st
from datetime import date
import numpy as np
import yfinance as yf

# Relative Imports innerhalb des src-Pakets
from . import backend_simulation
from . import plotting
from . import portfolio_logic
from . import prognose_logic
from .catalog import KATALOG
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
    
    # --- 1. ASSET HANDLING (GANZ OBEN) ---
    st.subheader("💰 Titel zum Portfolio hinzufügen")
    
    # Callback für Hinzufügen
    def handle_add_click():
        name_to_add = ""
        isin_to_add = ""
        is_valid = False
        
        # Werte aus dem Formular lesen
        start_invest = st.session_state.widget_add_start
        savings_rate = st.session_state.widget_add_savings
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
            st.session_state.assets.append({
                "Name": name_to_add,
                "ISIN / Ticker": isin_to_add,
                "Einmalerlag (€)": start_invest, 
                "Sparbetrag (€)": savings_rate,
                "Spar-Intervall": interval,
            })
            st.toast(f"'{name_to_add}' erfolgreich hinzugefügt!", icon="✅")
            # Reset der Inputs
            st.session_state.katalog_auswahl = "Bitte wählen..."
            st.session_state.manuelle_isin = ""

    # Formular - PLATZSPARENDES LAYOUT
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
            st.number_input("Einmalerlag (€)", min_value=0.0, value=1000.0, step=100.0, key="widget_add_start")
        with col_val2:
            st.number_input("Sparrate (€)", min_value=0.0, value=100.0, step=10.0, key="widget_add_savings")
        with col_val3:
            st.selectbox("Intervall", ["monatlich", "vierteljährlich", "jährlich"], key="widget_add_interval")
        with col_btn:
            st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True) # Spacer zum Ausrichten
            st.form_submit_button("Titel Hinzufügen", use_container_width=True, on_click=handle_add_click)

    st.caption("💡 **Tipp:** Zum Löschen einer Position markieren Sie die Zeile links und drücken die **'Entf'-Taste** (Delete) auf Ihrer Tastatur.")

    edited_assets = st.data_editor(
        st.session_state.assets,
        num_rows="dynamic",
        column_config={
            "Name": st.column_config.TextColumn("Name"),
            "ISIN / Ticker": st.column_config.TextColumn("ISIN / Ticker", required=True),
            "Einmalerlag (€)": st.column_config.NumberColumn("Einmalerlag (€)", min_value=0.0),
            "Sparbetrag (€)": st.column_config.NumberColumn("Sparbetrag (€)", min_value=0.0),
            "Spar-Intervall": st.column_config.SelectboxColumn("Spar-Intervall", options=["monatlich", "vierteljährlich", "jährlich"], required=True),
        },
        hide_index=True,
        use_container_width=True,
        key="portfolio_table_editor"
    )
    st.session_state.assets = edited_assets
    
    st.markdown('<div style="margin-bottom: 10px;"></div>', unsafe_allow_html=True)

    # --- 2. KOSTEN SETTINGS ---
    col_cost_only, _ = st.columns([1, 3])
    
    with col_cost_only:
        with st.popover("💸 Kosten Einstellungen", use_container_width=True):
            st.session_state.cost_ausgabe = st.number_input("Ausgabeaufschlag (%)", 0.0, 10.0, value=st.session_state.cost_ausgabe, step=0.1)
            st.session_state.cost_management = st.number_input("Managementgebühr (% p.a.)", 0.0, 10.0, value=st.session_state.cost_management, step=0.01)
            st.session_state.cost_depot = st.number_input("Depotgebühr (€ p.a.)", 0.0, value=st.session_state.cost_depot, step=1.0)


    # --- 3. AUTOMATISCHE BERECHNUNG (HISTORIE) ---
    simulation_successful = False
    assets_to_simulate = [asset for asset in st.session_state.assets if asset.get("ISIN / Ticker")]
    
    if assets_to_simulate:
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
                 
                 for name, value in hist_returns.items():
                    if name not in st.session_state.prognosis_assumptions_pa:
                        st.session_state.prognosis_assumptions_pa[name] = value
                        
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
                st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
                show_market_phases = st.toggle("📉 Marktphasen anzeigen", value=False)

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