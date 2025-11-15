import yfinance as yf
import pandas as pd
from datetime import date, timedelta
import streamlit as st
import numpy as np  # Importiere numpy für die Faktorberechnung


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


# (UPDATE) Funktion zur Validierung UND zum Abrufen des Namens
@st.cache_data
def validate_and_get_info(ticker: str) -> (bool, str | None):
    """
    Prüft, ob ein Ticker gültig ist und holt den Namen.
    (NEU) Gibt (True, "Ticker Name") oder (False, "Genaue Fehlermeldung") zurück.
    """
    if not ticker:
        return (False, "Kein Ticker/ISIN angegeben.")
    try:
        ticker_obj = yf.Ticker(ticker)
        
        # (DEBUG) Versuche, .info abzurufen. Dies schlägt bei ISINs oft fehl.
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
        # (DEBUG) Gib die genaue yfinance-Exception zurück
        print(f"Validierungs-Exception für {ticker}: {e}")
        # Gib die Fehlermeldung als String zurück, damit sie im Frontend angezeigt werden kann
        return (False, f"yfinance Exception: {e}")


# Caching für die Berechnungs-Funktion
@st.cache_data
def run_simulation(
    data: pd.DataFrame,
    periodic_investment: float,
    lump_sum: float,
    interval: str,
    inflation_rate_pa: float,
    ausgabeaufschlag_pct: float,
    managementgebuehr_pa_pct: float,
) -> pd.DataFrame:
    """
    Führt eine Sparplan-Simulation durch,
    basierend auf Einmalerlag, variablem Sparintervall, Inflation und Kosten.
    """

    # --- 1. KOSTENFAKTOREN ---
    # Ausgabeaufschlag (einmalig bei Kauf)
    cost_factor = 1.0 - (ausgabeaufschlag_pct / 100.0)

    # TÄGLICHER Inflationsfaktor
    daily_inflation_factor = (1.0 + (inflation_rate_pa / 100.0)) ** (1 / 365.0)

    # TÄGLICHER Managementgebühr-Faktor
    daily_mgmt_fee_factor = (1.0 - (managementgebuehr_pa_pct / 100.0)) ** (1 / 365.0)

    # --- 2. INTERVALL-LOGIK ---
    if interval == "monatlich":
        resample_code = "MS"  # 'Month Start'
    elif interval == "vierteljährlich":
        resample_code = "QS"  # 'Quarter Start'
    elif interval == "jährlich":
        resample_code = "YS"  # 'Year Start'
    else:
        resample_code = "MS"  # Fallback

    # --- DATEN VORBEREITUNG (Fix für Lücken und Spikes) ---
    full_date_range = pd.date_range(
        start=data.index.min(), end=data.index.max(), freq="D"
    )
    data = data.reindex(full_date_range)
    data["Close"] = data["Close"].ffill()
    data = data.dropna(subset=["Close"])

    if data.empty:
        return pd.DataFrame()  # Frühzeitiger Abbruch

    # 3. Erstelle die periodischen Daten (Zeitpunkte der Sparrate)
    periodic_data = data.resample(resample_code).first()
    periodic_data = periodic_data.rename(columns={"Close": "Price"})
    periodic_data = periodic_data.dropna(subset=["Price"])

    # Die Investitionssumme pro Periode (mit Ausgabeaufschlag)
    periodic_data["Investment"] = periodic_investment
    periodic_data["NetInvestment"] = periodic_data["Investment"] * cost_factor

    # 4. Berechne die laufenden Käufe (OHNE Einmalerlag)
    periodic_data["Shares_Bought"] = 0.0
    
    # 4a. TotalInvestment_Periodic enthält die Brutto-Einzahlung des Sparplans
    periodic_data["TotalInvestment_Periodic"] = 0.0
    
    # (FIX) Initialisiere die 'TotalShares_Periodic' Spalte VOR der Schleife
    periodic_data["TotalShares_Periodic"] = 0.0
    
    for i in range(len(periodic_data)):
        current_price = periodic_data.iloc[i]["Price"]

        # Die erste Rate (i=0) ist 0, die Sparplan-Zahlung beginnt erst danach
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

        # Kumuliere die Brutto-Einzahlungen des Sparplans
        if i == 0:
            periodic_data.iloc[i, periodic_data.columns.get_loc("TotalInvestment_Periodic")] = 0.0
            periodic_data.iloc[i, periodic_data.columns.get_loc("TotalShares_Periodic")] = 0.0
        else:
            periodic_data.iloc[i, periodic_data.columns.get_loc("TotalInvestment_Periodic")] = periodic_data.iloc[i-1]["TotalInvestment_Periodic"] + gross_inv
            periodic_data.iloc[i, periodic_data.columns.get_loc("TotalShares_Periodic")] = periodic_data.iloc[i-1]["TotalShares_Periodic"] + shares_bought

    # --- 5. ÜBERTRAGUNG AUF TÄGLICHE BASIS ---
    daily_data_with_portfolio = data.copy()

    # Füge den laufenden Anteilsbesitz (periodic) und den Brutto-Einzahlungsstand hinzu
    daily_data_with_portfolio = pd.merge_asof(
        daily_data_with_portfolio,
        periodic_data[["TotalShares_Periodic", "TotalInvestment_Periodic"]],
        left_index=True,
        right_index=True,
        direction="backward",
    )

    # Fülle NaNs am Anfang mit 0
    daily_data_with_portfolio["TotalShares_Periodic"] = daily_data_with_portfolio["TotalShares_Periodic"].fillna(0)
    daily_data_with_portfolio["TotalInvestment_Periodic"] = daily_data_with_portfolio["TotalInvestment_Periodic"].fillna(0)

    # --- 6. ADDITION DES EINMALERLAGS (LUMP SUM) ---
    lump_sum_shares = 0.0
    if lump_sum > 0 and not data.empty:
        first_day_price = data.iloc[0]["Close"]
        net_lump_sum = lump_sum * cost_factor

        if first_day_price > 0:
            lump_sum_shares = net_lump_sum / first_day_price

    # Die Gesamtanteile sind die Summe aus Einmalerlag-Anteilen (konstant) und periodischen Anteilen
    daily_data_with_portfolio["TotalShares"] = daily_data_with_portfolio["TotalShares_Periodic"] + lump_sum_shares

    # --- (FIX) Korrekte Berechnung der Gesamteinzahlung (Brutto) ---
    # Die Brutto-Einzahlung ist die konstante Einmalzahlung + die kumulierte Sparrate
    daily_data_with_portfolio["TotalInvestment"] = daily_data_with_portfolio["TotalInvestment_Periodic"] + lump_sum
    
    # --- 7. BERECHNE FINALEN WERT & WENDE GEBÜHREN AN ---

    # 7a. Berechne den TÄGLICHEN Portfolio-Wert (Nominal, vor Managementgebühr)
    daily_data_with_portfolio["Portfolio (nominal)"] = daily_data_with_portfolio["TotalShares"] * daily_data_with_portfolio["Close"]

    # 7b. Wende den täglichen Managementgebühr-Abzug an (kumulativ)
    mgmt_fee_series = pd.Series(
        daily_mgmt_fee_factor, index=daily_data_with_portfolio.index
    ).cumprod()
    daily_data_with_portfolio["Portfolio (nominal)"] = (
        daily_data_with_portfolio["Portfolio (nominal)"] * mgmt_fee_series
    )

    # 7c. Berechne die Inflation und den realen Wert
    inflation_series = pd.Series(
        daily_inflation_factor, index=daily_data_with_portfolio.index
    ).cumprod()
    daily_data_with_portfolio["Portfolio (real)"] = (
        daily_data_with_portfolio["Portfolio (nominal)"] / inflation_series
    )

    # 8. Finales DataFrame mit TÄGLICHEN Werten zurückgeben
    final_daily_df = daily_data_with_portfolio[
        ["TotalInvestment", "Portfolio (nominal)", "Portfolio (real)"]
    ].copy()
    final_daily_df = final_daily_df.rename(
        columns={"TotalInvestment": "Einzahlungen (brutto)"}
    )

    return final_daily_df