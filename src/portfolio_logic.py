import pandas as pd
import streamlit as st
from datetime import date
import numpy as np

from . import backend_simulation
# NEU: Import für echte Inflationsdaten
from . import inflation

def _calculate_annualized_return(sim_df: pd.DataFrame, num_years: float) -> float:
    """Berechnet die annualisierte Rendite (vereinfacht als ROI p.a.)"""
    if sim_df.empty or num_years == 0:
        return 0.0
        
    end_value = sim_df['Portfolio (nominal)'].iloc[-1]
    total_investment = sim_df['Einzahlungen (brutto)'].iloc[-1]
    
    if total_investment == 0:
        # Fall: Nur Einmalerlag am Starttag, der nicht in 'Einzahlungen (brutto)' auftaucht
        if end_value > 0:
            first_day_investment = sim_df['Portfolio (nominal)'].iloc[0]
            if first_day_investment > 0:
                return ((end_value / first_day_investment) ** (1 / num_years)) - 1
        return 0.0

    if end_value <= 0 or total_investment <= 0:
        return -1.0 

    try:
        return ((end_value / total_investment) ** (1 / num_years)) - 1
    except Exception:
        return 0.0 


@st.cache_data
def run_portfolio_simulation(
    assets: list[dict],
    start_date: date,
    end_date: date,
    # inflation_rate_pa entfernt -> wir nutzen jetzt echte Historie!
    ausgabeaufschlag_pct: float,
    managementgebuehr_pa_pct: float,
    depotgebuehr_pa_eur: float,
) -> tuple[pd.DataFrame | None, dict, dict]:
    
    individual_simulations = []
    historical_returns_pa = {}
    individual_final_values = {}
    
    num_years = (end_date - start_date).days / 365.25

    # --- NEU: ECHTE INFLATIONSDATEN VORBEREITEN ---
    full_date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    historical_inflation_series = inflation.calculate_inflation_series(full_date_range)

    for asset in assets:
        isin = asset.get("ISIN / Ticker")
        name = asset.get("Name") or isin
        lump_sum = asset.get("Einmalerlag (€)", 0)
        periodic = asset.get("Sparbetrag (€)", 0)
        interval = asset.get("Spar-Intervall", "monatlich")

        if not isin or (lump_sum == 0 and periodic == 0):
            continue

        historical_data = backend_simulation.load_data(
            isin=isin, start_date=start_date, end_date=end_date
        )

        if historical_data is None:
            st.error(f"Daten für {isin} konnten nicht geladen werden.")
            continue

        sim_df = backend_simulation.run_simulation(
            data=historical_data,
            periodic_investment=periodic,
            lump_sum=lump_sum,
            interval=interval,
            inflation_input=historical_inflation_series, # Hier übergeben wir die Serie!
            ausgabeaufschlag_pct=ausgabeaufschlag_pct,
            managementgebuehr_pa_pct=managementgebuehr_pa_pct,
        )
        
        if sim_df.empty:
            continue
            
        individual_simulations.append(sim_df)
        
        # Berechne p.a. Rendite
        return_pa_pct = _calculate_annualized_return(sim_df, num_years) * 100
        historical_returns_pa[name] = return_pa_pct
        individual_final_values[name] = sim_df['Portfolio (nominal)'].iloc[-1]


    if not individual_simulations:
        return None, {}, {}

    # FIX: Synchronisiere alle Simulationen auf den vollen Zeitraum
    # Verhindert, dass Assets am Ende "aussteigen" und die Summe droppt.
    aligned_simulations = []
    full_index = pd.date_range(start=start_date, end=end_date, freq="D")
    
    for df in individual_simulations:
        # 1. Reindex auf vollen Zeitraum
        # 2. ffill() -> Werte fortschreiben (wichtig für Delistings oder Datenlücken am Ende)
        # 3. bfill(limit=10) -> Kleine Lücken am Anfang (Feiertage, Wochenende) schließen
        # 4. fillna(0) -> Vor dem Startdatum (wenn länger als Limit) ist alles 0
        df_aligned = df.reindex(full_index).ffill().bfill(limit=10).fillna(0.0)
        aligned_simulations.append(df_aligned)

    if not aligned_simulations:
         return None, {}, {}

    # Summiere die angeglichenen DataFrames
    # Da alle denselben Index haben, können wir einfach sum() auf die Liste anwenden (oder concat + groupby)
    # pd.concat + groupby(level=0).sum() ist robust
    portfolio_df = pd.concat(aligned_simulations)
    final_portfolio = portfolio_df.groupby(portfolio_df.index).sum()

    # Depotgebühren Logik (Nachträglich auf Gesamtportfolio)
    if depotgebuehr_pa_eur > 0:
        final_portfolio["Depotgebuehr_Pkt"] = 0.0
        yearly_fee_dates = final_portfolio.resample("YS").first().index
        fee_dates_in_index = yearly_fee_dates.intersection(final_portfolio.index)

        if len(fee_dates_in_index) > 1:
            fee_dates_to_apply = fee_dates_in_index[1:]
            final_portfolio.loc[fee_dates_to_apply, "Depotgebuehr_Pkt"] = depotgebuehr_pa_eur

        final_portfolio["Kumulierte_Depotgebuehr"] = final_portfolio["Depotgebuehr_Pkt"].cumsum()
        final_portfolio["Portfolio (nominal)"] = (
            final_portfolio["Portfolio (nominal)"] - final_portfolio["Kumulierte_Depotgebuehr"]
        ).clip(lower=0)
        final_portfolio = final_portfolio.drop(columns=["Depotgebuehr_Pkt", "Kumulierte_Depotgebuehr"])

    # Realwert Berechnung (Konsistent mit Inflation auf Gesamtportfolio)
    # Reindexieren der Inflation auf das finale Portfolio
    final_inflation_series = historical_inflation_series.reindex(final_portfolio.index, method='ffill').fillna(1.0)
    
    final_portfolio["Portfolio (real)"] = final_portfolio["Portfolio (nominal)"] / final_inflation_series

    return final_portfolio, historical_returns_pa, individual_final_values