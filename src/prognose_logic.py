import pandas as pd
import numpy as np
from datetime import timedelta, date

from . import inflation  # Import der zentralen Inflations-Logik

@staticmethod
def _calculate_total_periodic_investment(assets: list[dict], interval: str) -> float:
    total = 0
    for asset in assets:
        if asset.get('Spar-Intervall') == interval:
            total += asset.get('Sparbetrag (€)', 0)
    return total

@staticmethod
def _get_resample_code(interval: str) -> str:
    if interval == "monatlich":
        return "MS"
    elif interval == "vierteljährlich":
        return "QS"
    elif interval == "jährlich":
        return "YS"
    return "MS"

def run_forecast(
    start_values: dict,
    assets: list[dict],
    prognose_jahre: int,
    sparplan_fortfuehren: bool,
    kosten_management_pa_pct: float,
    kosten_depot_pa_eur: float,
    ausgabeaufschlag_pct: float,
    expected_asset_returns_pa: dict[str, float],
    asset_final_values: dict[str, float],
    expected_volatility_pa: float,
    n_simulations: int
) -> pd.DataFrame | None:
    
    if prognose_jahre <= 0:
        return None

    #  1. Gewichtete p.a. Rendite (Erwartungswert) berechnen 
    total_portfolio_value = sum(asset_final_values.values())
    weighted_avg_return_pa = 0.0
    
    if total_portfolio_value > 0:
        for asset_name, final_value in asset_final_values.items():
            weight = final_value / total_portfolio_value
            asset_return_assumption = expected_asset_returns_pa.get(asset_name, 0.0)
            weighted_avg_return_pa += weight * asset_return_assumption
    
    #  2. Tägliche stochastische Parameter 
    trading_days = 365.25
    daily_mu = (weighted_avg_return_pa / 100.0) / trading_days
    daily_sigma = (expected_volatility_pa / 100.0) / np.sqrt(trading_days)

    #  3. Zeitrahmen 
    letzter_tag_hist = start_values['letzter_tag']
    letzter_wert_nominal = start_values['nominal']
    letzter_wert_real_basis = start_values['real']
    letzte_einzahlung = start_values['einzahlung']

    start_datum_prognose = letzter_tag_hist + timedelta(days=1)
    end_datum_prognose = start_datum_prognose + timedelta(days=int(prognose_jahre * trading_days))
    
    prognose_zeitraum = pd.date_range(start=start_datum_prognose, end=end_datum_prognose, freq='D')
    num_days = len(prognose_zeitraum)
    
    if prognose_zeitraum.empty or num_days <= 0:
        return None

    prognose_df = pd.DataFrame(index=prognose_zeitraum)

    #  4. Deterministische Faktoren 
    
    # A) INFLATION 
    inflation_series = inflation.calculate_inflation_series(prognose_zeitraum)
    
    # Anpassung an Basis (falls Simulation nahtlos fortgesetzt wird)
    inflation_basis = 1.0
    if letzter_wert_real_basis > 0:
        inflation_basis = letzter_wert_nominal / letzter_wert_real_basis
    
    # Zuweisung ins DataFrame
    prognose_df['Inflation_Factor'] = inflation_series * inflation_basis

    # B) KOSTEN
    daily_mgmt_fee_factor = (1.0 - (kosten_management_pa_pct / 100.0)) ** (1 / trading_days)
    cost_factor_sparrate = (1.0 - (ausgabeaufschlag_pct / 100.0))

    # C) Sparpläne
    prognose_df['Sparrate_Einzahlung'] = 0.0
    prognose_df['Sparrate_Netto'] = 0.0
    
    if sparplan_fortfuehren:
        for interval in ['monatlich', 'vierteljährlich', 'jährlich']:
            total_periodic = _calculate_total_periodic_investment(assets, interval)
            if total_periodic > 0:
                resample_code = _get_resample_code(interval)
                spartage = prognose_df.resample(resample_code).first().index
                spartage_im_index = spartage.intersection(prognose_df.index)
                
                prognose_df.loc[spartage_im_index, 'Sparrate_Einzahlung'] = total_periodic
                prognose_df.loc[spartage_im_index, 'Sparrate_Netto'] = total_periodic * cost_factor_sparrate
    
    depotgebuehr_tage = prognose_df.resample('YS').first().index.intersection(prognose_df.index)
    prognose_df['Einzahlungen (brutto)'] = prognose_df['Sparrate_Einzahlung'].cumsum() + letzte_einzahlung

    #  5. Monte Carlo Simulation 
    random_returns = np.random.normal(
        loc=daily_mu, 
        scale=daily_sigma, 
        size=(num_days, n_simulations)
    )
    
    sim_matrix = np.zeros((num_days, n_simulations))
    sim_matrix[0] = letzter_wert_nominal 
    
    sparrate_netto_vektor = prognose_df['Sparrate_Netto'].values
    depotgebuehr_vektor = np.zeros(num_days)
    depotgebuehr_indices = [prognose_df.index.get_loc(tag) for tag in depotgebuehr_tage if tag in prognose_df.index]
    if depotgebuehr_indices:
        depotgebuehr_vektor[depotgebuehr_indices] = kosten_depot_pa_eur

    for i in range(1, num_days):
        prev_values = sim_matrix[i-1]
        current_values = prev_values * (1 + random_returns[i])
        current_values += sparrate_netto_vektor[i]
        current_values *= daily_mgmt_fee_factor
        current_values -= depotgebuehr_vektor[i]
        current_values = np.maximum(0, current_values)
        sim_matrix[i] = current_values

    #  6. Aggregation 
    prognose_df['Portfolio (Median)'] = np.quantile(sim_matrix, 0.50, axis=1)
    prognose_df['Portfolio (BestCase)'] = np.quantile(sim_matrix, 0.95, axis=1)
    prognose_df['Portfolio (WorstCase)'] = np.quantile(sim_matrix, 0.05, axis=1)
    
    prognose_df['Portfolio (Real_Median)'] = prognose_df['Portfolio (Median)'] / prognose_df['Inflation_Factor']
    prognose_df['Portfolio (Real_BestCase)'] = prognose_df['Portfolio (BestCase)'] / prognose_df['Inflation_Factor']
    prognose_df['Portfolio (Real_WorstCase)'] = prognose_df['Portfolio (WorstCase)'] / prognose_df['Inflation_Factor']

    final_columns = [
        'Einzahlungen (brutto)',
        'Portfolio (Median)',
        'Portfolio (BestCase)',
        'Portfolio (WorstCase)',
        'Portfolio (Real_Median)',
        'Portfolio (Real_BestCase)',
        'Portfolio (Real_WorstCase)'
    ]
    
    return prognose_df[final_columns]