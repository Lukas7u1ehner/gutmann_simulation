import pandas as pd
import numpy as np
from datetime import timedelta

@staticmethod
def _calculate_total_periodic_investment(assets: list[dict], interval: str) -> float:
    """Berechnet die Summe aller Sparbeträge für ein bestimmtes Intervall."""
    total = 0
    for asset in assets:
        if asset.get('Spar-Intervall') == interval:
            total += asset.get('Sparbetrag (€)', 0)
    return total

@staticmethod
def _get_resample_code(interval: str) -> str:
    """Gibt den pandas Resample-Code für ein Intervall zurück."""
    if interval == "monatlich":
        return "MS"
    elif interval == "vierteljährlich":
        return "QS"
    elif interval == "jährlich":
        return "YS"
    return "MS" # Fallback

def run_forecast(
    historische_daten: pd.DataFrame,
    assets: list[dict],
    prognose_jahre: int,
    sparplan_fortfuehren: bool,
    kosten_management_pa_pct: float,
    kosten_depot_pa_eur: float,
    inflation_rate_pa: float,
    ausgabeaufschlag_pct: float
) -> pd.DataFrame | None:
    """
    Erstellt eine Prognose basierend auf der historischen Entwicklung.
    """
    if prognose_jahre <= 0:
        return None

    # --- 1. Historische Rendite berechnen (Geometrischer Mittelwert) ---
    hist_nominal = historische_daten['Portfolio (nominal)']
    
    # Filtern, um 0-Werte zu vermeiden, die Logarithmus-Fehler verursachen
    hist_nominal_filtered = hist_nominal[hist_nominal > 0]
    
    if hist_nominal_filtered.empty:
        # Fallback, falls das Portfolio 0 wert ist
        avg_daily_log_return = 0.0
    else:
        log_returns = np.log(hist_nominal_filtered / hist_nominal_filtered.shift(1))
        avg_daily_log_return = log_returns.replace([np.inf, -np.inf], np.nan).mean()

    if pd.isna(avg_daily_log_return):
        avg_daily_log_return = 0.0

    # --- 2. Startwerte & Zeitrahmen für Prognose ---
    letzter_tag_hist = historische_daten.index[-1]
    letzter_wert_nominal = historische_daten['Portfolio (nominal)'].iloc[-1]
    letzter_wert_real = historische_daten['Portfolio (real)'].iloc[-1]
    letzte_einzahlung = historische_daten['Einzahlungen (brutto)'].iloc[-1]

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
    
    # (NEU) Kumulativen Inflations-Faktor für reale Berechnungen erstellen
    prognose_df['Inflation_Factor'] = pd.Series(daily_inflation_factor, index=prognose_df.index).cumprod()
    # Der erste Tag der Prognose basiert auf der Inflation *bis zu diesem Tag*
    prognose_df['Inflation_Factor'] *= (historische_daten.iloc[-1]['Portfolio (nominal)'] / historische_daten.iloc[-1]['Portfolio (real)'])


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

    # --- 5. Tägliche Prognose-Schleife (KORRIGIERT) ---
    
    # (FIX) Listen für performantes Speichern erstellen
    nominal_values = []
    real_values = []
    einzahlung_values = []

    # Initialwerte setzen
    current_nominal = letzter_wert_nominal
    current_real = letzter_wert_real
    current_einzahlung = letzte_einzahlung
    
    # Depotgebühr-Stichtage finden
    depotgebuehr_tage = prognose_df.resample('YS').first().index.intersection(prognose_df.index)

    for i, (tag, row) in enumerate(prognose_df.iterrows()):
        
        # 1. Wertsteigerung (basierend auf Historie)
        current_nominal *= np.exp(avg_daily_log_return)
        
        # 2. Sparplan-Einzahlung (Netto)
        current_nominal += row['Sparrate_Netto']
        
        # 3. Kosten anwenden
        # 3a. Managementgebühr (täglich)
        current_nominal *= daily_mgmt_fee_factor
        
        # 3b. Depotgebühr (jährlich)
        if tag in depotgebuehr_tage:
            current_nominal -= kosten_depot_pa_eur
            
        # 4. Wert darf nicht negativ werden
        current_nominal = max(0, current_nominal)
        
        # 5. Reale & Brutto-Werte berechnen
        current_einzahlung += row['Sparrate_Einzahlung']
        # (FIX) Korrekte Real-Berechnung
        current_real = current_nominal / row['Inflation_Factor']
        
        # 6. Werte in Listen speichern
        nominal_values.append(current_nominal)
        real_values.append(current_real)
        einzahlung_values.append(current_einzahlung)

    # (FIX) Listen nach der Schleife den Spalten zuweisen
    prognose_df['Portfolio (nominal)'] = nominal_values
    prognose_df['Portfolio (real)'] = real_values
    prognose_df['Einzahlungen (brutto)'] = einzahlung_values

    return prognose_df

