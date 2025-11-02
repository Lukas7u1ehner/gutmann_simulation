import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sys, os

# --- DEBUGGING-BLOCK START ---
# Wir finden jetzt den exakten Fehler.

st.error("DEBUGGING-MODUS AKTIV")

# 1. Definiere den Root-Pfad
# __file__ ist der Pfad zu '1_Simulation.py'
# os.path.dirname(__file__) ist 'pages'
# os.path.join(..., "..") ist 'pages/..' -> das Hauptverzeichnis
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

st.write(f"**Debug 1:** Aktuelle Datei (`__file__`): `{__file__}`")
st.write(f"**Debug 2:** Berechneter Root-Pfad: `{root_path}`")

# 2. Füge den Root-Pfad zum sys.path hinzu (MANDATORY)
if root_path not in sys.path:
    sys.path.append(root_path)
    st.write(f"**Debug 3:** Root-Pfad wurde zum sys.path hinzugefügt.")
else:
    st.write(f"**Debug 3:** Root-Pfad war bereits im sys.path.")

st.write(f"**Debug 4:** Aktueller `sys.path`:")
st.json(sys.path)

# 3. Teste jeden Import einzeln
try:
    from src.style import (
        apply_gutmann_style,
        GUTMANN_LOGO_URL,
        GUTMANN_ACCENT_GREEN,
        GUTMANN_LIGHT_TEXT,
    )

    st.success("Debug: `src.style` erfolgreich importiert.")
    apply_gutmann_style()
except ImportError as e:
    st.error(f"**FATALER FEHLER beim Import von `src.style`:** {e}")
    st.write("Mögliche Lösung: Prüfe, ob `src/__init__.py` existiert.")
    st.stop()

try:
    from src import backend_simulation

    st.success("Debug: `src.backend_simulation` erfolgreich importiert.")
except ImportError as e:
    st.error(f"**FATALER FEHLER beim Import von `src.backend_simulation`:** {e}")
    st.write("Mögliche Lösung: Prüfe `src/backend_simulation.py` auf Importfehler.")
    st.stop()

try:
    from src import plotting

    st.success("Debug: `src.plotting` erfolgreich importiert.")
except ImportError as e:
    st.error(f"**FATALER FEHLER beim Import von `src.plotting`:** {e}")
    st.write(
        "Mögliche Lösung: Prüfe `src/plotting.py`. Importiert es `style` mit `from .style import ...` (mit Punkt)?"
    )
    st.stop()

try:
    from src import portfolio_logic

    st.success("Debug: `src.portfolio_logic` erfolgreich importiert.")
except ImportError as e:
    st.error(f"**FATALER FEHLER beim Import von `src.portfolio_logic`:** {e}")
    st.write(
        "Mögliche Lösung: Prüfe `src/portfolio_logic.py`. Importiert es `backend_simulation` mit `from .backend_simulation import ...` (mit Punkt)?"
    )
    st.stop()

try:
    from src import prognose_logic

    st.success("Debug: `src.prognose_logic` erfolgreich importiert.")
except ImportError as e:
    st.error(f"**FATALER FEHLER beim Import von `src.prognose_logic`:** {e}")
    st.write("Mögliche Lösung: Prüfe `src/prognose_logic.py` auf Importfehler.")
    st.stop()

try:
    from src.catalog import KATALOG

    st.success("Debug: `src.catalog` erfolgreich importiert.")
except ImportError as e:
    st.error(f"**FATALER FEHLER beim Import von `src.catalog`:** {e}")
    st.write("Mögliche Lösung: Prüfe `src/catalog.py`.")
    st.stop()

st.success("--- DEBUGGING ABGESCHLOSSEN: Alle Module geladen. ---")
# --- DEBUGGING-BLOCK ENDE ---


st.set_page_config(page_title="Simulation | Gutmann", page_icon="📈", layout="wide")

# --- (UPDATE) Logo im Hauptbereich (Zentriert & Größer) ---
st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 20px;">
        <a href="/" target="_self" style="text-decoration: none;">
            <img src="{GUTMANN_LOGO_URL}" alt="Bank Gutmann Logo" style="width: 350px;">
        </a>
    </div>
    <div>
        <h1 style="color: {GUTMANN_ACCENT_GREEN}; margin: 0; font-size: 2.5em;">Wertpapier-Simulation</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Initialisiere session_state für die Eingabefelder ---
if "katalog_auswahl" not in st.session_state:
    st.session_state.katalog_auswahl = "Bitte wählen..."
if "manuelle_isin" not in st.session_state:
    st.session_state.manuelle_isin = ""
if "assets" not in st.session_state:
    st.session_state.assets = [
        {
            "Name": "S&P 500 ETF",
            "ISIN / Ticker": "IE00B5BMR087",
            "Einmalerlag (€)": 1000.0,
            "Sparbetrag (€)": 100.0,
            "Spar-Intervall": "monatlich",
        },
        {
            "Name": "Apple Aktie",
            "ISIN / Ticker": "US0378331005",
            "Einmalerlag (€)": 500.0,
            "Sparbetrag (€)": 50.0,
            "Spar-Intervall": "monatlich",
        },
    ]
# (NEU) Initialisiere die Kosten als einzelne Schlüssel
if "cost_ausgabe" not in st.session_state:
    st.session_state.cost_ausgabe = 3.0
if "cost_management" not in st.session_state:
    st.session_state.cost_management = 0.85
if "cost_depot" not in st.session_state:
    st.session_state.cost_depot = 25.0

# (NEU) Initialisiere Prognose-Werte im session_state
if "prognose_jahre" not in st.session_state:
    # --- (FIX 1: DEFAULT-WERT) ---
    # Standardwert für Prognose ist 0 (keine Prognose)
    st.session_state.prognose_jahre = 0
if "prognose_sparplan" not in st.session_state:
    st.session_state.prognose_sparplan = True

# --- (FIX 1: STATE MANAGEMENT) ---
# Initialisiere die Ergebnis-DataFrames im session_state
if "simulations_daten" not in st.session_state:
    st.session_state.simulations_daten = None
if "prognose_daten" not in st.session_state:
    st.session_state.prognose_daten = None


# --- (Callback-Fix) Definiere die Callback-Funktion ---
def handle_add_click():
    name_to_add = ""
    isin_to_add = ""
    is_valid = False

    if st.session_state.katalog_auswahl != "Bitte wählen...":
        # Fall 1: Titel aus Katalog gewählt
        name_to_add = st.session_state.katalog_auswahl
        isin_to_add = KATALOG[st.session_state.katalog_auswahl]
        is_valid = True

    elif st.session_state.manuelle_isin:
        # Fall 2: Manuelle ISIN/Ticker Eingabe
        with st.spinner(f"Prüfe Ticker {st.session_state.manuelle_isin}..."):
            is_valid, ticker_name = backend_simulation.validate_and_get_info(
                st.session_state.manuelle_isin
            )

            if is_valid:
                name_to_add = ticker_name
                isin_to_add = st.session_state.manuelle_isin
            else:
                # (UPDATE) Fehler als Toast anzeigen
                st.toast(
                    f"Ticker/ISIN '{st.session_state.manuelle_isin}' nicht gefunden oder ungültig.",
                    icon="❌",
                )

    if is_valid and isin_to_add:
        # Erfolgreich validiert und hinzugefügt
        st.session_state.assets.append(
            {
                "Name": name_to_add,
                "ISIN / Ticker": isin_to_add,
                "Einmalerlag (€)": 1000.0,
                "Sparbetrag (€)": 100.0,
                "Spar-Intervall": "monatlich",
            }
        )
        st.toast(f"Titel '{name_to_add}' zum Portfolio hinzugefügt!", icon="✅")

        # (UPDATE) Beide Felder zurücksetzen
        st.session_state.katalog_auswahl = "Bitte wählen..."
        st.session_state.manuelle_isin = ""

    elif not is_valid and not st.session_state.manuelle_isin:
        # Weder Katalog noch Text eingegeben
        st.toast("Bitte einen Titel auswählen oder ISIN eingeben.", icon="⚠️")


# --- SEKTION 1: GLOBALE PARAMETER & AUSFÜHRUNG ---
st.subheader("📊 Simulations-Parameter")

col1, col2, col3, col4 = st.columns([1.5, 1.5, 1, 1])  # Layout angepasst

with col1:
    start_datum = st.date_input("Startdatum", date(2020, 1, 1), key="sim_start_date")

with col2:
    end_datum = st.date_input("Enddatum", date.today(), key="sim_end_date")

with col3:
    inflation_rate_input = st.slider(
        "Erw. Inflation p.a. (%)",
        min_value=0.0,
        max_value=10.0,
        value=2.5,
        step=0.1,
        help="Wird zur Berechnung der 'realen' Performance verwendet.",
        key="inflation_slider",
    )

with col4:
    # (FIX) Ersetze Button und Modal durch st.popover
    st.markdown(
        '<div style="margin-top: 28px;"></div>', unsafe_allow_html=True
    )  # (UPDATE) Präziser Abstandshalter
    with st.popover("💸 Kosten", use_container_width=True):
        st.write(
            "Lege hier die globalen Kosten fest, die auf dein Portfolio angewendet werden."
        )

        # Binde die Inputs direkt an den session_state
        st.number_input(
            "Ausgabeaufschlag (%)",
            min_value=0.0,
            max_value=10.0,
            key="cost_ausgabe",  # Bindet an st.session_state.cost_ausgabe
            step=0.1,
            help="Eine einmalige Gebühr, die bei jedem Kauf (Einmalerlag und Sparrate) anfällt.",
        )
        st.number_input(
            "Managementgebühr (% p.a.)",
            min_value=0.0,
            max_value=10.0,
            key="cost_management",  # Bindet an st.session_state.cost_management
            step=0.01,
            help="Eine laufende Gebühr, die jährlich auf deinen Depotwert berechnet wird.",
        )
        st.number_input(
            "Depotgebühr (€ p.a.)",
            min_value=0.0,
            key="cost_depot",  # Bindet an st.session_state.cost_depot
            step=1.0,
            help="Eine fixe, jährliche Gebühr für die Führung deines Depots.",
        )
        # Kein "Übernehmen"-Button nötig, die Werte sind live im session_state

st.divider()

# --- SEKTION 2: INVESTMENT-PARAMETER (Dynamische Tabelle) ---
st.subheader("💰 Ausgewählte Titel (Portfolio)")

edited_assets = st.data_editor(
    st.session_state.assets,
    num_rows="dynamic",
    column_config={
        "Name": st.column_config.TextColumn(
            "Name (Optional)", help="Ein Name für deine Referenz"
        ),
        "ISIN / Ticker": st.column_config.TextColumn(
            "ISIN / Ticker (Erforderlich)", required=True
        ),
        "Einmalerlag (€)": st.column_config.NumberColumn(
            "Einmalerlag (€)", min_value=0.0, step=100.0
        ),
        "Sparbetrag (€)": st.column_config.NumberColumn(
            "Sparbetrag (€)", min_value=0.0, step=10.0
        ),
        "Spar-Intervall": st.column_config.SelectboxColumn(
            "Spar-Intervall",
            options=["monatlich", "vierteljährlich", "jährlich"],
            required=True,
        ),
    },
    hide_index=True,
    use_container_width=True,
    key="portfolio_table",
)

st.session_state.assets = edited_assets

st.divider()

# --- SEKTION 3: TITEL HINZUFÜGEN (Katalog) ---
st.subheader("➕ Titel zum Portfolio hinzufügen")

with st.form(key="add_title_form", clear_on_submit=False):
    kat_col1, kat_col2, kat_col3 = st.columns([2, 2, 1])

    with kat_col1:
        katalog_auswahl_widget = st.selectbox(
            "Titel aus Katalog wählen", options=KATALOG.keys(), key="katalog_auswahl"
        )

    with kat_col2:
        manuelle_isin_widget = st.text_input(
            "Oder ISIN / Ticker manuell eingeben",
            help="Wird ignoriert, wenn ein Titel aus dem Katalog gewählt wurde.",
            key="manuelle_isin",
        )

    with kat_col3:
        st.markdown(
            '<div style="margin-top: 28px;"></div>', unsafe_allow_html=True
        )  # (UPDATE) Präziser Abstandshalter
        add_form_submitted = st.form_submit_button(
            "Hinzufügen", use_container_width=True, on_click=handle_add_click
        )


st.divider()

# --- SEKTION 4: GLOBALE KOSTEN & BERECHNUNG ---
# (NEU) Nur noch der Berechnen-Button
st.subheader("🚀 Ausführung")

run_button = st.button(
    "Portfolio neu berechnen",
    type="primary",
    use_container_width=True,
    key="run_simulation_button",
)

# --- (FIX 1: STATE MANAGEMENT) ---
# Der run_button löst nur die Berechnung und Speicherung im session_state aus.
if run_button:

    # --- Validierungs-Schleife ---
    assets_to_simulate = [
        asset for asset in st.session_state.assets if asset.get("ISIN / Ticker")
    ]

    if not assets_to_simulate:
        st.warning("Bitte füge mindestens einen gültigen Titel zum Portfolio hinzu.")
        st.stop()

    is_valid = True
    with st.spinner("Prüfe Ticker/ISINs aus der Tabelle..."):
        for asset in assets_to_simulate:
            isin = asset.get("ISIN / Ticker")
            valid, _ = backend_simulation.validate_and_get_info(isin)
            if not valid:
                st.error(
                    f"Fehlerhafte Eingabe im Portfolio: Ticker/ISIN '{isin}' (in Zeile '{asset.get('Name')}') konnte nicht validiert werden. Bitte korrigiere die Tabelle."
                )
                is_valid = False

    # Nur wenn alle Ticker gültig sind, die Simulation starten
    if is_valid:
        
        # Setze die Ergebnisse im State zurück, bevor neu berechnet wird
        st.session_state.simulations_daten = None
        st.session_state.prognose_daten = None
        
        with st.spinner("Lade Daten und berechne Portfolio-Simulation..."):
            # Speichere direkt im session_state
            st.session_state.simulations_daten = portfolio_logic.run_portfolio_simulation(
                assets=assets_to_simulate,
                start_date=start_datum,
                end_date=end_datum,
                inflation_rate_pa=inflation_rate_input,
                ausgabeaufschlag_pct=st.session_state.cost_ausgabe,
                managementgebuehr_pa_pct=st.session_state.cost_management,
                depotgebuehr_pa_eur=st.session_state.cost_depot,
            )

        if st.session_state.simulations_daten is None:
            st.error(
                "Simulation konnte nicht durchgeführt werden. Bitte Eingaben prüfen."
            )
        else:
            st.toast("Portfolio-Simulation erfolgreich!", icon="🎉")
            # (LOGIK-FIX) Prognose wird jetzt unten, außerhalb dieses Blocks, berechnet
            # Damit wird sie reaktiv, wenn man die Prognose-Jahre ändert


# --- SEKTION 5: ERGEBNISSE (Charts & KPIs) ---
# (FIX 1: STATE MANAGEMENT)
# Dieser Block wird jetzt immer angezeigt, wenn Daten vorhanden sind,
# nicht nur, wenn der Button *gerade* gedrückt wurde.
if st.session_state.simulations_daten is not None:

    # --- (LOGIK-FIX) Reaktive Prognose-Berechnung ---
    # Dieser Block wird *jedes Mal* ausgeführt, wenn sich ein Widget ändert
    # (z.B. der "prognose_jahre"-Input)
    if st.session_state.prognose_jahre > 0:
        
        # Hole die "assets_to_simulate" aus dem session_state,
        # da wir nicht mehr im "run_button" Block sind
        assets_to_simulate = [
            asset for asset in st.session_state.assets if asset.get("ISIN / Ticker")
        ]
        
        st.session_state.prognose_daten = prognose_logic.run_forecast(
            historische_daten=st.session_state.simulations_daten,
            assets=assets_to_simulate,
            prognose_jahre=st.session_state.prognose_jahre,
            sparplan_fortfuehren=st.session_state.prognose_sparplan,
            kosten_management_pa_pct=st.session_state.cost_management,
            kosten_depot_pa_eur=st.session_state.cost_depot,
            inflation_rate_pa=inflation_rate_input,
            ausgabeaufschlag_pct=st.session_state.cost_ausgabe
        )
    else:
         # (FIX 3: AXIS) Stelle sicher, dass die Prognose leer ist, wenn Jahre = 0
         st.session_state.prognose_daten = None

    # Lade die Daten aus dem session_state, um sie anzuzeigen
    simulations_daten = st.session_state.simulations_daten
    prognose_daten = st.session_state.prognose_daten

    # --- (LAYOUT-FIX) Nur noch EIN Spalten-Block ---
    chart_col, kpi_col = st.columns([3, 1])

    with chart_col:
        # (NEU) Übergebe beide DataFrames an die Plot-Funktion
        fig = plotting.create_simulation_chart(simulations_daten, prognose_daten)
        st.plotly_chart(fig, use_container_width=True)
        
        # --- (FIX 4: UI-PLATZIERUNG) ---
        # UI wird hier platziert (links, unter dem Chart)
        st.divider()
        st.subheader("🔮 Prognose-Parameter")
        st.number_input(
            "Prognose-Horizont (Jahre)",
            min_value=0,
            max_value=50,
            step=1,
            key="prognose_jahre", # Bindet an st.session_state
            help="Wie viele Jahre soll in die Zukunft prognostiziert werden? (0 = keine Prognose). Die Grafik aktualisiert sich live."
        )
        st.checkbox(
            "Sparplan in Prognose fortführen",
            key="prognose_sparplan", # Bindet an st.session_state
            help="Sollen die Sparpläne (siehe Tabelle oben) in der Zukunft weiterlaufen? Die Grafik aktualisiert sich live."
        )
        st.caption("Änderungen hier aktualisieren die Prognose im Chart live. Klicken Sie 'Portfolio neu berechnen', um die *historische* Simulation neu zu starten.")


    with kpi_col:
        # (FIX) Überschrift hier platziert
        st.subheader("✨ Portfolio-Kennzahlen")

        # (FIX & ANPASSUNG) Spacer auf deine 25px geändert
        st.markdown('<div style="margin-top: 25px;"></div>', unsafe_allow_html=True)
        
        try:
            # --- (FIX 2: KPI-Logik) ---
            # KPIs basieren jetzt IMMER auf den historischen Daten
            daten_fuer_kpi = simulations_daten
            kpi_label_suffix = " (Historisch)" # Zeigt klar, was es ist
            
            last_row = daten_fuer_kpi.iloc[-1]
            end_value_nominal = last_row["Portfolio (nominal)"]
            end_value_real = last_row["Portfolio (real)"]
            total_investment = last_row["Einzahlungen (brutto)"]

            if total_investment > 0:
                rendite_real_prozent = (
                    (end_value_real / total_investment) - 1
                ) * 100
                rendite_nominal_prozent = (
                    (end_value_nominal / total_investment) - 1
                ) * 100
            else:
               rendite_real_prozent = 0.0
               rendite_nominal_prozent = 0.0


            st.metric(f"Gesamteinzahlung (brutto){kpi_label_suffix}", f"€ {total_investment:,.2f}")
            st.metric(f"Endkapital (nominal){kpi_label_suffix}", f"€ {end_value_nominal:,.2f}")
            st.metric(f"Endkapital (real){kpi_label_suffix}", f"€ {end_value_real:,.2f}")
            st.metric(f"Rendite (nominal){kpi_label_suffix}", f"{rendite_nominal_prozent:,.2f} %")
            st.metric(f"Rendite (real){kpi_label_suffix}", f"{rendite_real_prozent:,.2f} %")

        except Exception as e:
            st.error(f"Fehler bei KPI-Berechnung: {e}")

    # (FIX 4: UI-PLATZIERUNG) Expander kommen nach den Spalten, damit sie volle Breite haben
    with st.expander("🔍 Zeige aggregierte Simulations-Ergebnisdaten (Täglich)"):
        st.dataframe(simulations_daten)
    
    # (NEU) Expander für Prognose-Daten, falls vorhanden
    if prognose_daten is not None:
        with st.expander("🔮 Zeige aggregierte Prognose-Ergebnisdaten (Täglich)"):
            st.dataframe(prognose_daten)

