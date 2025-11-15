import pandas as pd
import numpy as np
from datetime import timedelta, date

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
    inflation_rate_pa: float,
    ausgabeaufschlag_pct: float,
    expected_asset_returns_pa: dict[str, float],
    asset_final_values: dict[str, float]
) -> pd.DataFrame | None:
    
    if prognose_jahre <= 0:
        return None

    # --- 1. Gewichtete p.a. Rendite basierend auf User-Annahmen berechnen ---
    total_portfolio_value = sum(asset_final_values.values())
    weighted_avg_return_pa = 0.0
    
    if total_portfolio_value > 0:
        for asset_name, final_value in asset_final_values.items():
            weight = final_value / total_portfolio_value
            # Hole Annahme, falle zurück auf 0 wenn nicht im dict
            asset_return_assumption = expected_asset_returns_pa.get(asset_name, 0.0)
            weighted_avg_return_pa += weight * asset_return_assumption
    
    daily_return_factor = (1.0 + (weighted_avg_return_pa / 100.0)) ** (1 / 365.25)

    # --- 2. Startwerte & Zeitrahmen für Prognose ---
    letzter_tag_hist = start_values['letzter_tag']
    letzter_wert_nominal = start_values['nominal']
    letzter_wert_real_basis = start_values['real'] # Basis für Inflationsfaktor
    letzte_einzahlung = start_values['einzahlung']

    start_datum_prognose = letzter_tag_hist + timedelta(days=1)
    end_datum_prognose = start_datum_prognose + timedelta(days=int(prognose_jahre * 365.25))
    
    prognose_zeitraum = pd.date_range(start=start_datum_prognose, end=end_datum_prognose, freq='D')
    
    if prognose_zeitraum.empty:
        return None

    prognose_df = pd.DataFrame(index=prognose_zeitraum)

    # --- 3. Tägliche Faktoren berechnen ---
    daily_inflation_factor = (1.0 + (inflation_rate_pa / 100.0)) ** (1 / 365.25)
    daily_mgmt_fee_factor = (1.0 - (kosten_management_pa_pct / 100.0)) ** (1 / 365.25)
    cost_factor_sparrate = (1.0 - (ausgabeaufschlag_pct / 100.0))
    
    # Kumulativen Inflations-Faktor erstellen
    prognose_df['Inflation_Factor'] = pd.Series(daily_inflation_factor, index=prognose_df.index).cumprod()
    
    # Inflationsfaktor-Basis vom letzten historischen Tag holen
    inflation_basis = 1.0
    if letzter_wert_real_basis > 0:
        inflation_basis = letzter_wert_nominal / letzter_wert_real_basis
        
    prognose_df['Inflation_Factor'] *= inflation_basis


    # --- 4. Zukünftige Sparpläne vorbereiten ---
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

    # --- 5. Tägliche Prognose-Schleife ---
    nominal_values = []
    real_values = []
    einzahlung_values = []

    current_nominal = letzter_wert_nominal
    current_einzahlung = letzte_einzahlung
    
    depotgebuehr_tage = prognose_df.resample('YS').first().index.intersection(prognose_df.index)

    for i, (tag, row) in enumerate(prognose_df.iterrows()):
        
        # 1. Wertsteigerung (basierend auf User-Annahmen)
        current_nominal *= daily_return_factor
        
        # 2. Sparplan-Einzahlung (Netto)
        current_nominal += row['Sparrate_Netto']
        
        # 3. Kosten anwenden
        # 3a. Managementgebühr (täglich)
        current_nominal *= daily_mgmt_fee_factor
        
        # 3b. Depotgebühr (jährlich)
        if tag in depotgebuehr_tage:
            current_nominal -= kosten_depot_pa_eur
            
        current_nominal = max(0, current_nominal)
        
        # 5. Reale & Brutto-Werte berechnen
        current_einzahlung += row['Sparrate_Einzahlung']
        current_real = current_nominal / row['Inflation_Factor']
        
        nominal_values.append(current_nominal)
        real_values.append(current_real)
        einzahlung_values.append(current_einzahlung)

    prognose_df['Portfolio (nominal)'] = nominal_values
    prognose_df['Portfolio (real)'] = real_values
    prognose_df['Einzahlungen (brutto)'] = einzahlung_values

    return prognose_df