import pandas as pd
import streamlit as st
from datetime import date
import numpy as np

# Importiere die Logik für EIN Asset
# (FIX) Import muss relativ sein (mit Punkt)
from . import backend_simulation


@st.cache_data
def run_portfolio_simulation(
    assets: list[dict],  # Eine Liste von Asset-Wörterbüchern
    start_date: date,
    end_date: date,
    inflation_rate_pa: float,
    ausgabeaufschlag_pct: float,
    managementgebuehr_pa_pct: float,
    depotgebuehr_pa_eur: float,
) -> pd.DataFrame | None:
    """
    Orchestriert die Simulation für ein ganzes Portfolio von Assets.
    """

    individual_simulations = []

    # --- 1. & 2. Einzelsimulationen durchführen ---
    for asset in assets:
        isin = asset.get("ISIN / Ticker")
        lump_sum = asset.get("Einmalerlag (€)", 0)
        periodic = asset.get("Sparbetrag (€)", 0)
        interval = asset.get("Spar-Intervall", "monatlich")

        if not isin or (lump_sum == 0 and periodic == 0):
            continue

        historical_data = backend_simulation.load_data(
            isin=isin, start_date=start_date, end_date=end_date
        )

        if historical_data is None:
            st.error(
                f"Daten für {isin} konnten nicht geladen werden. Asset übersprungen."
            )
            continue

        sim_df = backend_simulation.run_simulation(
            data=historical_data,
            periodic_investment=periodic,
            lump_sum=lump_sum,
            interval=interval,
            inflation_rate_pa=inflation_rate_pa,
            ausgabeaufschlag_pct=ausgabeaufschlag_pct,
            managementgebuehr_pa_pct=managementgebuehr_pa_pct,
        )
        individual_simulations.append(sim_df)

    # --- 3. Aggregation ---
    if not individual_simulations:
        st.warning("Keine gültigen Assets im Portfolio für die Simulation.")
        return None

    portfolio_df = pd.concat(individual_simulations)
    final_portfolio = portfolio_df.groupby(portfolio_df.index).sum()

    # --- 4. (FIX) Globale Depotgebühr korrekt anwenden ---
    if depotgebuehr_pa_eur > 0:
        final_portfolio["Depotgebuehr_Pkt"] = 0.0
        yearly_fee_dates = final_portfolio.resample("YS").first().index
        fee_dates_in_index = yearly_fee_dates.intersection(final_portfolio.index)

        if len(fee_dates_in_index) > 1:
            fee_dates_to_apply = fee_dates_in_index[1:]
            final_portfolio.loc[fee_dates_to_apply, "Depotgebuehr_Pkt"] = (
                depotgebuehr_pa_eur
            )

        final_portfolio["Kumulierte_Depotgebuehr"] = final_portfolio[
            "Depotgebuehr_Pkt"
        ].cumsum()
        final_portfolio["Portfolio (nominal)"] = (
            final_portfolio["Portfolio (nominal)"]
            - final_portfolio["Kumulierte_Depotgebuehr"]
        )
        final_portfolio["Portfolio (nominal)"] = final_portfolio[
            "Portfolio (nominal)"
        ].clip(lower=0)
        final_portfolio = final_portfolio.drop(
            columns=["Depotgebuehr_Pkt", "Kumulierte_Depotgebuehr"]
        )

    # --- 5. Finale Inflationsberechnung (auf dem finalen nominalen Wert) ---
    daily_inflation_factor = (1.0 + (inflation_rate_pa / 100.0)) ** (1 / 365.0)
    inflation_series = pd.Series(
        daily_inflation_factor, index=final_portfolio.index
    ).cumprod()

    final_portfolio["Portfolio (real)"] = (
        final_portfolio["Portfolio (nominal)"] / inflation_series
    )

    return final_portfolio
