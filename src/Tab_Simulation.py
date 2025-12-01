import streamlit as st
from datetime import date
import numpy as np

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
    
    # 1. GLOBALE EINGABEN
    st.subheader("📋 Simulations-Parameter festlegen")

    # Callbacks für Datum-Update
    def update_start_date():
        st.session_state.sim_start_date = st.session_state.widget_start_date
    def update_end_date():
        st.session_state.sim_end_date = st.session_state.widget_end_date

    col1, col2, col3, col4 = st.columns([1.5, 1.5, 1, 1])
    with col1:
        st.date_input(
            "Startdatum (Historie)", 
            value=st.session_state.sim_start_date,
            max_value=date.today(), 
            key="widget_start_date",
            on_change=update_start_date
        )
    with col2:
        st.date_input(
            "Enddatum (Historie)", 
            value=st.session_state.sim_end_date,
            max_value=date.today(), 
            key="widget_end_date",
            on_change=update_end_date
        )
    with col3:
        st.session_state.inflation_slider = st.slider(
            "Erw. Inflation p.a. (%)", 0.0, 10.0, 
            value=st.session_state.inflation_slider, 
            step=0.1
        )
    with col4:
        st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
        with st.popover("💸 Kosten Einstellungen", use_container_width=True):
            st.session_state.cost_ausgabe = st.number_input("Ausgabeaufschlag (%)", 0.0, 10.0, value=st.session_state.cost_ausgabe, step=0.1)
            st.session_state.cost_management = st.number_input("Managementgebühr (% p.a.)", 0.0, 10.0, value=st.session_state.cost_management, step=0.01)
            st.session_state.cost_depot = st.number_input("Depotgebühr (€ p.a.)", 0.0, value=st.session_state.cost_depot, step=1.0)

    # Asset Handling
    def handle_add_click():
        name_to_add = ""
        isin_to_add = ""
        is_valid = False
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
                "Einmalerlag (€)": 1000.0,
                "Sparbetrag (€)": 100.0,
                "Spar-Intervall": "monatlich",
            })
            st.toast(f"'{name_to_add}' hinzugefügt!", icon="✅")
            st.session_state.katalog_auswahl = "Bitte wählen..."
            st.session_state.manuelle_isin = ""

    st.subheader("💰 Titel zum Portfolio hinzufügen")
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

    with st.form(key="add_title_form", clear_on_submit=False):
        kat_col1, kat_col2, kat_col3 = st.columns([2, 2, 1])
        with kat_col1:
            st.selectbox("Titel aus Katalog wählen", KATALOG.keys(), key="katalog_auswahl")
        with kat_col2:
            st.text_input("Oder ISIN / Ticker manuell eingeben", key="manuelle_isin")
        with kat_col3:
            st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
            st.form_submit_button("Hinzufügen", use_container_width=True, on_click=handle_add_click)

    # 2. AUTOMATISCHE BERECHNUNG (Historie)
    simulation_successful = False
    assets_to_simulate = [asset for asset in st.session_state.assets if asset.get("ISIN / Ticker")]
    
    if assets_to_simulate:
        with st.spinner("Berechne Portfolio..."):
             sim_data, hist_returns, final_values = portfolio_logic.run_portfolio_simulation(
                assets=assets_to_simulate,
                start_date=st.session_state.sim_start_date,
                end_date=st.session_state.sim_end_date,
                inflation_rate_pa=st.session_state.inflation_slider,
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


    # 3. TOGGLE (Historie vs. Zukunft)
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
            
            st.markdown("##### 📈 Berechnete Rendite p.a. (Historisch)")
            hist_returns = st.session_state.historical_returns_pa
            if hist_returns:
                cols = st.columns(len(hist_returns))
                for i, (name, rendite_pa) in enumerate(hist_returns.items()):
                    with cols[i]:
                        st.metric(f"{name}", f"{rendite_pa:,.2f} % p.a.")
            
            st.subheader("Entwicklung in der Vergangenheit")
            chart_col, kpi_col = st.columns([3, 1])
            with chart_col:
                fig = plotting.create_simulation_chart(st.session_state.simulations_daten, None, title="Historisches Portfolio") 
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
                st.metric("Endkapital (real)", f"€ {end_value_real:,.2f}", help="Kaufkraftbereinigt")
                st.metric("Gesamtrendite (nom.)", f"{rendite_nominal_prozent:,.2f} %")


        # === SUB-TAB: ZUKUNFTSPROGNOSE ===
        elif st.session_state.sim_sub_nav_state == "Zukunftsprognose":
            
            def update_assumption(asset_name):
                val = st.session_state[f"assumption_{asset_name}"]
                st.session_state.prognosis_assumptions_pa[asset_name] = val
            
            def update_prognose_jahre():
                st.session_state.prognose_jahre = st.session_state.widget_prognose_jahre

            def run_prognose_logic():
                current_assumptions = st.session_state.prognosis_assumptions_pa
                last_row = st.session_state.simulations_daten.iloc[-1]
                start_vals = {
                    "letzter_tag": st.session_state.simulations_daten.index[-1],
                    "nominal": last_row["Portfolio (nominal)"],
                    "real": last_row["Portfolio (real)"],
                    "einzahlung": last_row["Einzahlungen (brutto)"]
                }
                
                st.session_state.prognose_daten = prognose_logic.run_forecast(
                    start_values=start_vals,
                    assets=st.session_state.assets,
                    prognose_jahre=st.session_state.prognose_jahre,
                    sparplan_fortfuehren=FIXED_SPARPLAN_ACTIVE, 
                    kosten_management_pa_pct=st.session_state.cost_management,
                    kosten_depot_pa_eur=st.session_state.cost_depot,
                    inflation_rate_pa=st.session_state.inflation_slider,
                    ausgabeaufschlag_pct=st.session_state.cost_ausgabe,
                    expected_asset_returns_pa=current_assumptions,
                    asset_final_values=st.session_state.asset_final_values,
                    expected_volatility_pa=FIXED_VOLATILITY,
                    n_simulations=FIXED_N_SIMULATIONS
                )

            st.subheader("🔮 Prognose- & Monte-Carlo-Parameter")
            
            # --- FIXE SETTINGS ---
            st.markdown(f"""
            <div class="fixed-settings-container">
                <span class="fixed-label-main">⚙️ Fixe Einstellungen:</span>
                <span class="fixed-val">Simulationen: <strong>{FIXED_N_SIMULATIONS}</strong></span>
                <span class="fixed-val">Profil: <strong>{FIXED_RISK_PROFILE_KEY} ({FIXED_VOLATILITY}%)</strong></span>
                <span class="fixed-val">Sparplan: <strong>{'Ja' if FIXED_SPARPLAN_ACTIVE else 'Nein'}</strong></span>
            </div>
            """, unsafe_allow_html=True)

            # --- VARIABLE SETTINGS ---
            var_col1, var_col2 = st.columns([1, 3])
            
            with var_col1:
                st.markdown("**Prognose-Horizont**")
                st.slider(
                    "Jahre", 
                    min_value=5, max_value=30, 
                    value=st.session_state.prognose_jahre, 
                    key="widget_prognose_jahre",
                    on_change=update_prognose_jahre,
                    label_visibility="collapsed"
                )
                st.caption(f"Aktuell: {st.session_state.prognose_jahre} Jahre")

            with var_col2:
                st.markdown("**Erwartete Rendite (p.a.) je Titel**")
                current_asset_names = list(st.session_state.prognosis_assumptions_pa.keys())
                
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

            # Berechnung
            run_prognose_logic()

            # Grafik & Ergebnisse
            if st.session_state.prognose_daten is not None:
                st.subheader("📊 Ergebnisse: Zukunftsprognose")
                
                chart_col, kpi_col = st.columns([3, 1])
                
                with chart_col:
                    fig_prog = plotting.create_simulation_chart(
                        None, 
                        st.session_state.prognose_daten, 
                        title="Prognostizierte Entwicklung (Monte Carlo)"
                    )
                    st.plotly_chart(fig_prog, use_container_width=True)

                with kpi_col:
                    st.markdown('<div style="margin-top: 25px;"></div>', unsafe_allow_html=True)
                    
                    last_row_prog = st.session_state.prognose_daten.iloc[-1]
                    
                    end_val_nom = last_row_prog["Portfolio (Median)"]
                    end_val_real = last_row_prog["Portfolio (Real_Median)"]
                    total_invest = last_row_prog["Einzahlungen (brutto)"]
                    
                    rendite_nom = ((end_val_nom / total_invest) - 1) * 100 if total_invest > 0 else 0
                    rendite_real = ((end_val_real / total_invest) - 1) * 100 if total_invest > 0 else 0

                    st.metric("Gesamteinzahlung (Prognose-Ende)", f"€ {total_invest:,.2f}")
                    st.metric("Endkapital (nominal)", f"€ {end_val_nom:,.2f}")
                    st.metric("Endkapital (real)", f"€ {end_val_real:,.2f}")
                    st.metric("Rendite (nominal)", f"{rendite_nom:,.2f} %")
                    st.metric("Rendite (real)", f"{rendite_real:,.2f} %")