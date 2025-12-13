import yfinance as yf
import pandas as pd
from datetime import date, timedelta
import streamlit as st
import numpy as np

@st.cache_data
def load_data(isin: str, start_date: date, end_date: date) -> pd.DataFrame | None:
    """
    Holt die historischen Kursdaten für eine gegebene ISIN (oder Ticker)
    in einem bestimmten Zeitraum.
    """
    print(f"Lade Daten für {isin} von {start_date} bis {end_date}...")

    try:
        data = yf.download(isin, start=start_date, end=end_date)

        if data.empty:
            print(f"Keine Daten gefunden für Ticker: {isin}")
            return None

        print("Daten erfolgreich geladen.")

        # --- FIX FÜR MULTI-INDEX SPALTEN (z.B. bei ISINs) ---
        if isinstance(data.columns, pd.MultiIndex):
            # Finde die 'Close'-Spalte
            close_col_name = [col for col in data.columns if col[0] == "Close"][0]
            close_data = data[[close_col_name]].copy()
            close_data.columns = ["Close"]
        else:
            # Normaler Index (z.B. bei Ticker 'AAPL')
            close_data = data[["Close"]].copy()

        # Stelle sicher, dass das Datum ein 'datetime' Objekt ist
        close_data.index = pd.to_datetime(close_data.index)

        # Fülle fehlende 'Close' Preise (Wochenenden, Feiertage)
        close_data["Close"] = close_data["Close"].ffill()

        return close_data

    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        return None


@st.cache_data
def validate_and_get_info(ticker: str) -> (bool, str | None):
    """
    Prüft, ob ein Ticker gültig ist und holt den Namen.
    Gibt (True, "Ticker Name") oder (False, "Fehlermeldung") zurück.
    """
    if not ticker:
        return (False, "Kein Ticker/ISIN angegeben.")
    try:
        ticker_obj = yf.Ticker(ticker)
        
        # (DEBUG) Versuche, .info abzurufen.
        info = ticker_obj.info

        # (DEBUG) Prüfe, ob .history() leer ist.
        history_data = ticker_obj.history(period="1d")
        
        if history_data.empty:
            print(f"Validierung fehlgeschlagen: Keine Daten für {ticker}")
            return (False, f"yfinance fand keine 'history'-Daten für '{ticker}'.")

        # Versuche, den Namen zu bekommen
        name = info.get("longName", info.get("shortName"))

        # Wenn kein Name da ist, aber der Ticker gültig, nimm den Ticker selbst
        if not name:
            name = ticker

        print(f"Validierung erfolgreich for {ticker}, Name: {name}")
        return (True, name)

    except Exception as e:
        print(f"Validierungs-Exception für {ticker}: {e}")
        return (False, f"yfinance Exception: {e}")


@st.cache_data
def run_simulation(
    data: pd.DataFrame,
    periodic_investment: float,
    lump_sum: float,
    interval: str,
    # GEÄNDERT: Akzeptiert jetzt float (Prognose) ODER Series (Historie)
    inflation_input: float | pd.Series,
    ausgabeaufschlag_pct: float,
    managementgebuehr_pa_pct: float,
) -> pd.DataFrame:
    """
    Führt eine Sparplan-Simulation durch.
    inflation_input: Entweder ein Float (p.a. %) für Prognosen
                     ODER eine pd.Series (Index=Date, Value=Factor) für exakte Historie.
    """

    # --- 1. KOSTENFAKTOREN ---
    cost_factor = 1.0 - (ausgabeaufschlag_pct / 100.0)

    # TÄGLICHER Managementgebühr-Faktor
    daily_mgmt_fee_factor = (1.0 - (managementgebuehr_pa_pct / 100.0)) ** (1 / 365.0)

    # --- 2. INTERVALL-LOGIK ---
    if interval == "monatlich":
        resample_code = "MS"
    elif interval == "vierteljährlich":
        resample_code = "QS"
    elif interval == "jährlich":
        resample_code = "YS"
    else:
        resample_code = "MS"

    # --- DATEN VORBEREITUNG ---
    full_date_range = pd.date_range(
        start=data.index.min(), end=data.index.max(), freq="D"
    )
    data = data.reindex(full_date_range)
    data["Close"] = data["Close"].ffill()
    data = data.dropna(subset=["Close"])

    if data.empty:
        return pd.DataFrame()

    # 3. Erstelle die periodischen Daten (Zeitpunkte der Sparrate)
    periodic_data = data.resample(resample_code).first()
    periodic_data = periodic_data.rename(columns={"Close": "Price"})
    periodic_data = periodic_data.dropna(subset=["Price"])

    # Die Investitionssumme pro Periode (mit Ausgabeaufschlag)
    periodic_data["Investment"] = periodic_investment
    periodic_data["NetInvestment"] = periodic_data["Investment"] * cost_factor

    # 4. Berechne die laufenden Käufe
    periodic_data["Shares_Bought"] = 0.0
    periodic_data["TotalInvestment_Periodic"] = 0.0
    periodic_data["TotalShares_Periodic"] = 0.0
    
    for i in range(len(periodic_data)):
        current_price = periodic_data.iloc[i]["Price"]

        if i == 0:
            net_inv = 0.0
            gross_inv = 0.0
        else:
            net_inv = periodic_data.iloc[i]["NetInvestment"]
            gross_inv = periodic_data.iloc[i]["Investment"]

        if current_price > 0:
            shares_bought = net_inv / current_price
        else:
            shares_bought = 0

        periodic_data.iloc[i, periodic_data.columns.get_loc("Shares_Bought")] = shares_bought

        if i == 0:
            periodic_data.iloc[i, periodic_data.columns.get_loc("TotalInvestment_Periodic")] = 0.0
            periodic_data.iloc[i, periodic_data.columns.get_loc("TotalShares_Periodic")] = 0.0
        else:
            periodic_data.iloc[i, periodic_data.columns.get_loc("TotalInvestment_Periodic")] = periodic_data.iloc[i-1]["TotalInvestment_Periodic"] + gross_inv
            periodic_data.iloc[i, periodic_data.columns.get_loc("TotalShares_Periodic")] = periodic_data.iloc[i-1]["TotalShares_Periodic"] + shares_bought

    # --- 5. ÜBERTRAGUNG AUF TÄGLICHE BASIS ---
    daily_data_with_portfolio = data.copy()

    daily_data_with_portfolio = pd.merge_asof(
        daily_data_with_portfolio,
        periodic_data[["TotalShares_Periodic", "TotalInvestment_Periodic"]],
        left_index=True,
        right_index=True,
        direction="backward",
    )

    daily_data_with_portfolio["TotalShares_Periodic"] = daily_data_with_portfolio["TotalShares_Periodic"].fillna(0)
    daily_data_with_portfolio["TotalInvestment_Periodic"] = daily_data_with_portfolio["TotalInvestment_Periodic"].fillna(0)

    # --- 6. ADDITION DES EINMALERLAGS (LUMP SUM) ---
    lump_sum_shares = 0.0
    if lump_sum > 0 and not data.empty:
        first_day_price = data.iloc[0]["Close"]
        net_lump_sum = lump_sum * cost_factor

        if first_day_price > 0:
            lump_sum_shares = net_lump_sum / first_day_price

    daily_data_with_portfolio["TotalShares"] = daily_data_with_portfolio["TotalShares_Periodic"] + lump_sum_shares
    daily_data_with_portfolio["TotalInvestment"] = daily_data_with_portfolio["TotalInvestment_Periodic"] + lump_sum
    
    # --- 7. BERECHNE FINALEN WERT & GEBÜHREN ---

    # 7a. Nominalwert
    daily_data_with_portfolio["Portfolio (nominal)"] = daily_data_with_portfolio["TotalShares"] * daily_data_with_portfolio["Close"]

    # 7b. Managementgebühr
    mgmt_fee_series = pd.Series(
        daily_mgmt_fee_factor, index=daily_data_with_portfolio.index
    ).cumprod()
    daily_data_with_portfolio["Portfolio (nominal)"] = (
        daily_data_with_portfolio["Portfolio (nominal)"] * mgmt_fee_series
    )

    # 7c. Inflation / Realwert (NEU ANGEPASST)
    if isinstance(inflation_input, pd.Series):
        # Fall A: Historische Zeitreihe übergeben -> Reindex auf Daten-Index
        # ffill füllt Lücken (z.B. Wochenenden), fillna(1.0) für Startwerte
        inflation_series = inflation_input.reindex(daily_data_with_portfolio.index, method='ffill').fillna(1.0)
    else:
        # Fall B: Fixer Float Wert (Prognose) -> Alte Berechnung
        daily_inflation_factor = (1.0 + (inflation_input / 100.0)) ** (1 / 365.0)
        inflation_series = pd.Series(
            daily_inflation_factor, index=daily_data_with_portfolio.index
        ).cumprod()

    daily_data_with_portfolio["Portfolio (real)"] = (
        daily_data_with_portfolio["Portfolio (nominal)"] / inflation_series
    )

    # 8. Rückgabe
    final_daily_df = daily_data_with_portfolio[
        ["TotalInvestment", "Portfolio (nominal)", "Portfolio (real)"]
    ].copy()
    final_daily_df = final_daily_df.rename(
        columns={"TotalInvestment": "Einzahlungen (brutto)"}
    )

    return final_daily_df