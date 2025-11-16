import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sys, os
import numpy as np # Import für numpy

st.set_page_config(page_title="Simulation | Gutmann", page_icon="📈", layout="wide")

try:
    from src.style import (
        apply_gutmann_style,
        GUTMANN_LOGO_URL,
        GUTMANN_ACCENT_GREEN,
        GUTMANN_LIGHT_TEXT,
    )
    from src import backend_simulation
    from src import plotting
    from src import portfolio_logic
    from src import prognose_logic
    from src.catalog import KATALOG

    apply_gutmann_style()

except ImportError as e:
    st.error(
        f"**FATALER FEHLER beim Import von `src`:** {e}. Stelle sicher, dass der 'src'-Ordner im selben Verzeichnis wie Startseite.py liegt."
    )
    st.stop()

# --- KORREKTUR: Risikoprofile & Dynamische Labels ---
RISK_PROFILES = {
    "Konservativ": {
        "beschreibung": "Wenig Schwankung, langsam wachsend",
        "volatilitaet_pa": 10.0
    },
    "Ausgewogen": {
        "beschreibung": "Durchschnittliches Risiko",
        "volatilitaet_pa": 17.0
    },
    "Offensiv": {
        "beschreibung": "Starke Schwankung, hohe Chance, aber auch hohe Verlustrisiken",
        "volatilitaet_pa": 25.0
    }
}
# Erstellt ein Mapping von "Label (mit %)" -> "Basis-Key"
# z.B. {"Ausgewogen (17.0% p.a.)": "Ausgewogen"}
RISK_PROFILES_LABELS_MAP = {
    f"{k} ({v['volatilitaet_pa']:.1f}% p.a.)": k 
    for k, v in RISK_PROFILES.items()
}
# Nur die Liste der Labels für die Dropdown-Optionen
RISK_PROFILES_OPTIONS = list(RISK_PROFILES_LABELS_MAP.keys())

DEFAULT_RISK_PROFILE_KEY = "Ausgewogen" # Der Basis-Key
DEFAULT_VOLATILITY = RISK_PROFILES[DEFAULT_RISK_PROFILE_KEY]["volatilitaet_pa"]
DEFAULT_N_SIMULATIONS = 500


# --- SESSION STATE INITIALISIERUNG (ERWEITERT) ---
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "🏠 Startseite"
if "katalog_auswahl" not in st.session_state:
    st.session_state.katalog_auswahl = "Bitte wählen..."
if "assets" not in st.session_state:
    st.session_state.assets = [
        {"Name": "S&P 500 ETF", "ISIN / Ticker": "IE00B5BMR087", "Einmalerlag (€)": 1000.0, "Sparbetrag (€)": 100.0, "Spar-Intervall": "monatlich"},
        {"Name": "Apple Aktie", "ISIN / Ticker": "US0378331005", "Einmalerlag (€)": 500.0, "Sparbetrag (€)": 50.0, "Spar-Intervall": "monatlich"},
    ]
if "cost_ausgabe" not in st.session_state:
    st.session_state.cost_ausgabe = 2.0
if "cost_management" not in st.session_state:
    st.session_state.cost_management = 2.0
if "cost_depot" not in st.session_state:
    st.session_state.cost_depot = 50.0
if "inflation_slider" not in st.session_state:
    st.session_state.inflation_slider = 3.0
if "prognose_jahre" not in st.session_state:
    st.session_state.prognose_jahre = 0
if "prognose_sparplan" not in st.session_state:
    st.session_state.prognose_sparplan = True
if "n_simulations" not in st.session_state:
    st.session_state.n_simulations = DEFAULT_N_SIMULATIONS
if "risk_profile" not in st.session_state:
    st.session_state.risk_profile = DEFAULT_RISK_PROFILE_KEY # Haupt-State nutzt Basis-Key
if "selected_volatility_pa" not in st.session_state:
    st.session_state.selected_volatility_pa = DEFAULT_VOLATILITY

# --- SEPARATE WIDGET-KEYS ---
if "widget_cost_ausgabe" not in st.session_state:
    st.session_state.widget_cost_ausgabe = st.session_state.cost_ausgabe
if "widget_cost_management" not in st.session_state:
    st.session_state.widget_cost_management = st.session_state.cost_management
if "widget_cost_depot" not in st.session_state:
    st.session_state.widget_cost_depot = st.session_state.cost_depot
if "widget_inflation_slider" not in st.session_state:
    st.session_state.widget_inflation_slider = st.session_state.inflation_slider
if "widget_prognose_jahre" not in st.session_state:
    st.session_state.widget_prognose_jahre = st.session_state.prognose_jahre
if "widget_prognose_sparplan_label" not in st.session_state:
    st.session_state.widget_prognose_sparplan_label = "Ja" if st.session_state.prognose_sparplan else "Nein"
if "widget_n_simulations" not in st.session_state:
    st.session_state.widget_n_simulations = st.session_state.n_simulations
if "widget_risk_profile" not in st.session_state:
    # Finde das volle Label (z.B. "Ausgewogen (17.0% p.a.)") basierend auf dem Basis-Key
    default_full_label = [label for label, base_key in RISK_PROFILES_LABELS_MAP.items() if base_key == DEFAULT_RISK_PROFILE_KEY][0]
    st.session_state.widget_risk_profile = default_full_label

# Daten-Container
if "simulations_daten" not in st.session_state:
    st.session_state.simulations_daten = None
if "prognose_daten" not in st.session_state:
    st.session_state.prognose_daten = None
if "historical_returns_pa" not in st.session_state:
    st.session_state.historical_returns_pa = {}
if "asset_final_values" not in st.session_state:
    st.session_state.asset_final_values = {}
if "prognosis_assumptions_pa" not in st.session_state:
    st.session_state.prognosis_assumptions_pa = {}
# --- ENDE SESSION STATE ---


def go_to_setup():
    st.session_state.active_tab = "⚙️ Historische Simulation"

def go_to_prognose():
    st.session_state.active_tab = "📈 Zukunftsprognose"


# --- TAB LOGIK (bleibt gleich) ---
tabs_options = ["🏠 Startseite", "⚙️ Historische Simulation"]
if st.session_state.simulations_daten is not None:
    tabs_options.append("📈 Zukunftsprognose")
st.radio(" ", options=tabs_options, key="active_tab", horizontal=True)



# --- TAB 1: STARTSEITE (bleibt gleich) ---
if st.session_state.active_tab == "🏠 Startseite":
    st.markdown(f"""<div style="display: flex; align-items: center; justify-content: center; margin-top: 20px; margin-bottom: 30px;"><img src="{GUTMANN_LOGO_URL}" alt="Bank Gutmann Logo" style="width: 350px;"></div>""", unsafe_allow_html=True)
    st.title("Willkommen zur Bank Gutmann Wertpapier-Simulation")
    st.markdown("Dies ist ein interaktiver Prototyp zur Simulation von Wertpapier-Portfolios, entwickelt im Rahmen des Studiums 'Digital Technology and Innovation'.")
    st.markdown("### Starten Sie Ihre persönliche Simulation")
    st.button("📈 Zur Simulation starten", on_click=go_to_setup, use_container_width=True, type="primary")
    st.markdown("### Was simuliert dieses Tool?")
    st.markdown("Dieses Tool führt ein **Backtesting** durch. Es nutzt reale, historische Kursdaten von `yfinance`, um die Wertentwicklung eines von dir zusammengestellten Portfolios in der Vergangenheit nachzubilden.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"#### 💸 Einzahlungen")
        st.markdown("- **Einmalerlag:** Ein Startkapital, das Sie zu Beginn investieren.\n- **Sparplan:** Regelmäßige (z.B. monatliche) Einzahlungen, die Ihr Portfolio kontinuierlich aufbauen.")
    with col2:
        st.markdown(f"#### 📉 Inflation & Kosten")
        st.markdown("- **Inflation (Real):** Zeigt die \"echte\" Wertentwicklung nach Abzug der Inflation (Kaufkraftverlust).\n- **Kosten (Nominal):** Berücksichtigt Gebühren wie den Ausgabeaufschlag, die Ihre investierte Summe und somit die Rendite schmälern.")
    with col3:
        st.markdown(f"#### 📈 Rendite (KPIs)")
        st.markdown("- **Nominale Rendite:** Die reine Wertentwicklung Ihres Portfolios in Prozent, ohne Inflation.\n- **Reale Rendite:** Die inflationsbereinigte Rendite. Sie zeigt, wie stark Ihr Vermögen *tatsächlich* an Kaufkraft gewonnen hat.")


# --- TAB 2: Historische Simulation ---
elif st.session_state.active_tab == "⚙️ Historische Simulation":
    
    # --- CALLBACKS FÜR TAB 2 ---
    def callback_inflation_costs():
        # Synchronisiere Widget-Keys zurück zu Haupt-Keys
        st.session_state.inflation_slider = st.session_state.widget_inflation_slider
        st.session_state.cost_ausgabe = st.session_state.widget_cost_ausgabe
        st.session_state.cost_management = st.session_state.widget_cost_management
        st.session_state.cost_depot = st.session_state.widget_cost_depot

    def handle_add_click():
        # ... (Diese Funktion ist unverändert) ...
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
                is_valid, message_or_name = backend_simulation.validate_and_get_info(
                    isin_to_add
                )
                if is_valid:
                    name_to_add = message_or_name
                else:
                    st.toast(f"Ticker/ISIN '{isin_to_add}' nicht gefunden.", icon="❌")
                    st.warning(f"Technischer Grund: {message_or_name}")
        
        if is_valid and isin_to_add:
            st.session_state.assets.append(
                {
                    "Name": name_to_add,
                    "ISIN / Ticker": isin_to_add,
                    "Einmalerlag (€)": 1000.0,
                    "Sparbetrag (€)": 100.0,
                    "Spar-Intervall": "monatlich",
                }
            )
            st.toast(f"Titel '{name_to_add}' hinzugefügt!", icon="✅")
            st.session_state.katalog_auswahl = "Bitte wählen..."
            st.session_state.manuelle_isin = ""
            st.session_state.active_tab = "⚙️ Historische Simulation"
        elif not is_valid and not st.session_state.manuelle_isin:
            st.toast("Bitte Titel auswählen oder ISIN eingeben.", icon="⚠️")
    # --- ENDE CALLBACKS ---

    
    st.subheader("📊 Schritt 1: Simulations-Parameter festlegen")
    col1, col2, col3, col4 = st.columns([1.5, 1.5, 1, 1])
    with col1:
        start_datum = st.date_input("Startdatum", date(2020, 1, 1), key="sim_start_date")
    with col2:
        end_datum = st.date_input("Enddatum", date.today(), key="sim_end_date")
    with col3:
        # KORREKTUR: Angepasst an das Rendite-Muster
        st.slider(
            "Erw. Inflation p.a. (%)",
            0.0,
            10.0,
            value=st.session_state.inflation_slider, # <-- HAUPT-Key
            key="widget_inflation_slider",           # <-- WIDGET-Key
            on_change=callback_inflation_costs,      # <-- SYNC-Callback
            step=0.1,
            help="Wird zur Berechnung der 'realen' Performance verwendet.",
        )
    with col4:
        st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
        with st.popover("💸 Kosten", use_container_width=True):
            # KORREKTUR: Alle Kosten an das Rendite-Muster angepasst
            st.number_input("Ausgabeaufschlag (%)", 0.0, 10.0, 
                            value=st.session_state.cost_ausgabe, 
                            key="widget_cost_ausgabe", 
                            on_change=callback_inflation_costs, 
                            step=0.1)
            st.number_input("Managementgebühr (% p.a.)", 0.0, 10.0, 
                            value=st.session_state.cost_management, 
                            key="widget_cost_management", 
                            on_change=callback_inflation_costs, 
                            step=0.01)
            st.number_input("Depotgebühr (€ p.a.)", 0.0, 
                            value=st.session_state.cost_depot, 
                            key="widget_cost_depot", 
                            on_change=callback_inflation_costs, 
                            step=1.0)
    

    st.subheader("💰 Schritt 2: Titel zum Portfolio hinzufügen")
    edited_assets = st.data_editor(
        st.session_state.assets,
        num_rows="dynamic",
        column_config={
            "Name": st.column_config.TextColumn("Name (Optional)"),
            "ISIN / Ticker": st.column_config.TextColumn("ISIN / Ticker", required=True),
            "Einmalerlag (€)": st.column_config.NumberColumn("Einmalerlag (€)", min_value=0.0),
            "Sparbetrag (€)": st.column_config.NumberColumn("Sparbetrag (€)", min_value=0.0),
            "Spar-Intervall": st.column_config.SelectboxColumn(
                "Spar-Intervall", options=["monatlich", "vierteljährlich", "jährlich"], required=True
            ),
        },
        hide_index=True,
        use_container_width=True,
        key="portfolio_table",
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
    

    st.subheader("🚀 Schritt 3: Historische Simulation starten")
    run_button = st.button(
        "Historische Simulation berechnen", 
        type="primary",
        use_container_width=True,
        key="run_simulation_button",
    )

    if run_button:
        assets_to_simulate = [asset for asset in st.session_state.assets if asset.get("ISIN / Ticker")]
        if not assets_to_simulate:
            st.warning("Bitte füge mindestens einen gültigen Titel zum Portfolio hinzu.")
            st.stop()

        is_valid = True
        with st.spinner("Prüfe Ticker/ISINs aus der Tabelle..."):
            for asset in assets_to_simulate:
                isin = asset.get("ISIN / Ticker")
                valid, message = backend_simulation.validate_and_get_info(isin)
                if not valid:
                    st.error(f"Fehlerhafte Eingabe: Ticker/ISIN '{isin}' ('{asset.get('Name')}') konnte nicht validiert werden.")
                    st.warning(f"👉 Technischer Grund: {message}")
                    is_valid = False
        
        if is_valid:
            st.session_state.simulations_daten = None 
            st.session_state.prognose_daten = None
            st.session_state.historical_returns_pa = {}
            st.session_state.asset_final_values = {}
            st.session_state.prognosis_assumptions_pa = {}
            
            with st.spinner("Lade Daten und berechne Portfolio-Simulation..."):
                sim_data, hist_returns, final_values = portfolio_logic.run_portfolio_simulation(
                    assets=assets_to_simulate,
                    start_date=start_datum,
                    end_date=end_datum,
                    inflation_rate_pa=st.session_state.inflation_slider,
                    ausgabeaufschlag_pct=st.session_state.cost_ausgabe,
                    managementgebuehr_pa_pct=st.session_state.cost_management,
                    depotgebuehr_pa_eur=st.session_state.cost_depot,
                )
            
            if sim_data is None:
                st.error("Simulation konnte nicht durchgeführt werden. Bitte Eingaben prüfen.")
            else:
                st.toast("Historische Simulation erfolgreich!", icon="🎉")
                st.session_state.simulations_daten = sim_data
                st.session_state.historical_returns_pa = hist_returns
                st.session_state.asset_final_values = final_values
                st.session_state.prognosis_assumptions_pa = hist_returns.copy()
                
                # Widget-Keys für den nächsten Tab initialisieren
                for name, value in hist_returns.items():
                    widget_key = f"assumption_{name}"
                    if widget_key not in st.session_state:
                        st.session_state[widget_key] = value

    
    if st.session_state.simulations_daten is not None:

        st.subheader("📊 Ergebnisse: Historische Simulation")
        simulations_daten = st.session_state.simulations_daten
        chart_col, kpi_col = st.columns([3, 1])
        
        with chart_col:
            fig = plotting.create_simulation_chart(simulations_daten, None, title="Historische Portfolio-Entwicklung") 
            st.plotly_chart(fig, use_container_width=True)
        
        with kpi_col:
            st.markdown('<div style="margin-top: 25px;"></div>', unsafe_allow_html=True)
            try:
                last_row = simulations_daten.iloc[-1]
                end_value_nominal = last_row["Portfolio (nominal)"]
                end_value_real = last_row["Portfolio (real)"]
                total_investment = last_row["Einzahlungen (brutto)"]
                if total_investment > 0:
                    rendite_real_prozent = ((end_value_real / total_investment) - 1) * 100
                    rendite_nominal_prozent = ((end_value_nominal / total_investment) - 1) * 100
                else:
                    rendite_real_prozent = 0.0
                    rendite_nominal_prozent = 0.0
                st.metric("Gesamteinzahlung (brutto)", f"€ {total_investment:,.2f}")
                st.metric("Endkapital (nominal)", f"€ {end_value_nominal:,.2f}")
                st.metric("Endkapital (real)", f"€ {end_value_real:,.2f}")
                st.metric("Rendite (nominal)", f"{rendite_nominal_prozent:,.2f} %")
                st.metric("Rendite (real)", f"{rendite_real_prozent:,.2f} %")
            except Exception as e:
                st.error(f"Fehler bei KPI-Berechnung: {e}")


        st.subheader("📈 Berechnete Rendite p.a. (Historisch)")
        hist_returns = st.session_state.historical_returns_pa
        
        if not hist_returns:
            st.info("Keine historischen Renditen berechnet.")
        else:
            num_cols = len(hist_returns)
            cols = st.columns(num_cols)
            for i, (name, rendite_pa) in enumerate(hist_returns.items()):
                with cols[i]:
                    st.metric(f"{name}", f"{rendite_pa:,.2f} % p.a.")
        

        st.button("🔮 Zur Zukunftsprognose wechseln", on_click=go_to_prognose, use_container_width=True)
        with st.expander("🔍 Zeige aggregierte historische Ergebnisdaten (Täglich)"):
            st.dataframe(simulations_daten)


# --- TAB 3: ZUKUNFTSPROGNOSE ---
elif st.session_state.active_tab == "📈 Zukunftsprognose":
    
    simulations_daten = st.session_state.simulations_daten
    if simulations_daten is None:
        st.warning("Bitte führe zuerst eine Simulation im Tab 'Historische Simulation' durch.")
        st.stop()

    
    # --- KERNFUNKTION (wird von Callbacks aufgerufen) ---
    def run_prognose_calculation():
        """
        Führt die Monte-Carlo-Simulation mit den aktuellen
        Werten aus dem session_state aus.
        """
        if st.session_state.prognose_jahre <= 0:
            st.session_state.prognose_daten = None
            return

        last_row = simulations_daten.iloc[-1]
        start_values = {
            "letzter_tag": simulations_daten.index[-1],
            "nominal": last_row["Portfolio (nominal)"],
            "real": last_row["Portfolio (real)"],
            "einzahlung": last_row["Einzahlungen (brutto)"]
        }
        
        # Sicherstellen, dass die Asset-Annahmen synchronisiert sind
        # (falls der Asset-Callback nicht der Auslöser war)
        assumptions_from_widgets = {}
        for asset_name in st.session_state.prognosis_assumptions_pa.keys():
            widget_key = f"assumption_{asset_name}"
            assumptions_from_widgets[asset_name] = st.session_state.get(widget_key, 0.0)
        st.session_state.prognosis_assumptions_pa = assumptions_from_widgets
        
        with st.spinner("Berechne Monte-Carlo-Simulation..."):
            st.session_state.prognose_daten = prognose_logic.run_forecast(
                start_values=start_values,
                assets=st.session_state.assets,
                prognose_jahre=st.session_state.prognose_jahre,
                sparplan_fortfuehren=st.session_state.prognose_sparplan,
                kosten_management_pa_pct=st.session_state.cost_management,
                kosten_depot_pa_eur=st.session_state.cost_depot,
                inflation_rate_pa=st.session_state.inflation_slider,
                ausgabeaufschlag_pct=st.session_state.cost_ausgabe,
                expected_asset_returns_pa=st.session_state.prognosis_assumptions_pa,
                asset_final_values=st.session_state.asset_final_values,
                # MC-Parameter übergeben
                expected_volatility_pa=st.session_state.selected_volatility_pa,
                n_simulations=st.session_state.n_simulations
            )

    # --- CALLBACKS FÜR TAB 3 ---
    
    def callback_global_params_sync():
        """
        Synchronisiert NUR die globalen Widget-States zu den Haupt-States.
        Löst KEINE Neuberechnung aus, das macht callback_mc_params.
        """
        st.session_state.prognose_jahre = st.session_state.widget_prognose_jahre
        st.session_state.prognose_sparplan = (st.session_state.widget_prognose_sparplan_label == "Ja")

    def callback_asset_params():
        """
        Wird NUR von den Rendite-Annahmen-Widgets ausgelöst.
        Synchronisiert und startet die Neuberechnung.
        """
        # 1. Asset-Annahmen synchronisieren (redundant, aber sicher)
        assumptions_from_widgets = {}
        for asset_name in st.session_state.prognosis_assumptions_pa.keys():
             widget_key = f"assumption_{asset_name}"
             assumptions_from_widgets[asset_name] = st.session_state.get(widget_key, 0.0)
        st.session_state.prognosis_assumptions_pa = assumptions_from_widgets
        
        # 2. Neuberechnung auslösen
        run_prognose_calculation()

    def callback_mc_params():
        """
        Wird von ALLEN globalen Prognose-Parametern ausgelöst.
        Synchronisiert ALLES und startet die Neuberechnung.
        """
        # 1. Globale Parameter synchronisieren
        callback_global_params_sync()
        
        # 2. MC-Parameter synchronisieren
        st.session_state.n_simulations = st.session_state.widget_n_simulations
        
        selected_label = st.session_state.widget_risk_profile
        base_profile_name = RISK_PROFILES_LABELS_MAP[selected_label]
        
        st.session_state.risk_profile = base_profile_name
        st.session_state.selected_volatility_pa = RISK_PROFILES[base_profile_name]["volatilitaet_pa"]
        
        # 3. Neuberechnung auslösen
        run_prognose_calculation()


    # --- KORREKTUR: UI-Parameter neu angeordnet (4 Spalten) ---
    st.subheader("🔮 Prognose- & Monte-Carlo-Parameter")
    
    # Obere Zeile für die Haupt-Inputs
    prog_col1, prog_col2, prog_col3, prog_col4 = st.columns(4)
    
    with prog_col1:
        st.number_input(
            "Prognose-Horizont (Jahre)", 
            min_value=0, max_value=50, step=1,
            value=st.session_state.prognose_jahre,
            key="widget_prognose_jahre",       
            help="Wie viele Jahre soll in die Zukunft prognostiziert werden? (0 = keine Prognose).",
            on_change=callback_mc_params # Wichtig: Ruft den MC-Callback auf     
        ) 
        
    with prog_col2:
        st.number_input(
            "Anzahl Simulationen",
            min_value=100, max_value=5000, step=100,
            value=st.session_state.n_simulations,
            key="widget_n_simulations",
            on_change=callback_mc_params,
            help="Mehr Simulationen = genauer, aber langsamer."
        )
        
    with prog_col3:
        # Help-Text für die Risikoprofile
        RISK_PROFILES_HELP = """
        Bestimmt die angenommene Schwankungsbreite (Volatilität) für die Monte-Carlo-Simulation:
        - **Konservativ (10.0% p.a.):** Wenig Schwankung, langsam wachsend
        - **Ausgewogen (17.0% p.a.):** Durchschnittliches Risiko
        - **Offensiv (25.0% p.a.):** Starke Schwankung, hohe Chance, aber auch hohe Verlustrisiken
        """
        
        # Finde den Index des vollen Labels basierend auf dem Haupt-State
        current_base_profile = st.session_state.risk_profile
        try:
            current_full_label = [label for label, base in RISK_PROFILES_LABELS_MAP.items() if base == current_base_profile][0]
            current_index = RISK_PROFILES_OPTIONS.index(current_full_label)
        except Exception:
            current_index = 0 # Fallback

        st.selectbox(
            "Risikoprofil", # KORREKTUR: Titel gekürzt, % im Label
            options=RISK_PROFILES_OPTIONS, # Nutzt die neuen Labels
            index=current_index,
            key="widget_risk_profile",
            on_change=callback_mc_params,
            help=RISK_PROFILES_HELP
        )

    with prog_col4:
        # KORREKTUR: Sparplan in diese Spalte verschoben
        st.selectbox(
            "Sparplan fortführen",
            options=["Ja", "Nein"],
            key="widget_prognose_sparplan_label", # Nutzt den Label-Key
            on_change=callback_mc_params, # Ruft auch den MC-Callback auf
            help="Sollen die Sparpläne (siehe Tab 'Historische Simulation') in der Zukunft weiterlaufen?"
        )
        
    st.caption("Globale Kosten & Inflation werden aus dem 'Historische Simulation'-Tab übernommen.")
    st.caption("Die *Volatilität* (Schwankung) wird oben global über das Risikoprofil für das *gesamte* Portfolio festgelegt.")

    # --- UI FÜR ASSET-ANNAHMEN (Rendite) ---
    st.subheader("📈 Erwartete Rendite p.a. (Ihre Annahmen)")
    
    
    assumptions_source = st.session_state.prognosis_assumptions_pa
    
    if not assumptions_source:
        st.warning("Keine Assets für Annahmen gefunden. Bitte Historie berechnen.")
    else:
        num_cols = len(assumptions_source)
        cols = st.columns(num_cols)
        
        for i, (name, default_rendite_pa) in enumerate(assumptions_source.items()):
            widget_key = f"assumption_{name}"
            # Initialisiere den Widget-Key, falls er fehlt
            if widget_key not in st.session_state:
                st.session_state[widget_key] = assumptions_source.get(name, default_rendite_pa)

            with cols[i]:
                st.number_input(
                    f"{name} (% p.a.)",
                    min_value=-50.0,
                    max_value=50.0,
                    value=st.session_state[widget_key], # Liest vom Widget-Key
                    step=0.5,
                    key=widget_key, # Schreibt auf Widget-Key
                    on_change=callback_asset_params, # Löst Asset-Callback aus
                    help=f"Ihre Annahme für die zukünftige Rendite von {name}."
                )

    # --- "Initialer Check" (wird bei jedem Laden ausgeführt) ---
    if st.session_state.prognose_jahre > 0 and st.session_state.prognose_daten is None:
        # Ruft die Logik auf, um State zu synchronisieren & zu rechnen
        run_prognose_calculation() 

    prognose_daten = st.session_state.prognose_daten
    

    # --- ANZEIGE DER GRAFIK ---
    st.subheader("📊 Ergebnisse: Historie + Monte-Carlo-Prognose")
    fig = plotting.create_simulation_chart(
        simulations_daten, 
        prognose_daten, 
        title="Portfolio-Entwicklung (Historie & Prognose)"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("🔍 Zeige aggregierte historische Ergebnisdaten (Täglich)"):
        st.dataframe(simulations_daten)
    
    if prognose_daten is not None:
        with st.expander("🔮 Zeige aggregierte Prognose-Ergebnisdaten (Täglich)"):
            st.dataframe(prognose_daten)