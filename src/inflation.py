import pandas as pd
import numpy as np

# Statische HICP Daten für Österreich (Jahresdurchschnitt)
# Quelle: Eurostat / Statistik Austria
HISTORICAL_INFLATION_MAP = {
    2010: 1.8,
    2011: 3.3,
    2012: 2.4,
    2013: 2.0,
    2014: 1.7,
    2015: 0.9,
    2016: 0.9,
    2017: 2.1,
    2018: 2.0,
    2019: 1.5,
    2020: 1.14,
    2021: 4.25,
    2022: 10.15,
    2023: 5.60,
    2024: 2.04,
    2025: 4.00,
}

# Standard-Annahme für Jahre, die nicht in der Map stehen (Zukunft ab 2026)
DEFAULT_FUTURE_INFLATION = 2.0

def get_inflation_for_year(year: int) -> float:
    """Gibt die Inflationsrate für ein bestimmtes Jahr zurück."""
    return HISTORICAL_INFLATION_MAP.get(year, DEFAULT_FUTURE_INFLATION)

def calculate_inflation_series(date_index: pd.DatetimeIndex) -> pd.Series:
    """
    Erstellt eine Serie von kumulierten Inflationsfaktoren für einen Datums-Index.
    Nutzt für jedes Jahr den spezifischen (oder Standard-) Wert.
    """
    if date_index.empty:
        return pd.Series(dtype=float)

    # Wir berechnen tägliche Faktoren basierend auf dem Jahr des jeweiligen Datums
    years = date_index.year
    unique_years = np.unique(years)
    
    daily_factors = pd.Series(index=date_index, dtype=float)
    
    for y in unique_years:
        # Jahresrate holen (Map oder Default)
        inf_pa = get_inflation_for_year(y)
        
        # Täglicher Faktor: (1 + rate)^(1/365)
        factor = (1.0 + (inf_pa / 100.0)) ** (1 / 365.0)
        
        # Zuweisung für alle Tage dieses Jahres im Index
        mask = (years == y)
        daily_factors[mask] = factor
        
    # Kumulatives Produkt ergibt den Kaufkraftverlust-Faktor über die Zeit
    cumulative_inflation = daily_factors.cumprod()
    
    # Normierung: Der Startpunkt der übergebenen Serie ist immer die Basis (1.0) Damit zeigen wir die Inflation RELATIV zum Startzeitraum an.
    if not cumulative_inflation.empty:
        start_val = cumulative_inflation.iloc[0]
        cumulative_inflation = cumulative_inflation / start_val
        
    return cumulative_inflation