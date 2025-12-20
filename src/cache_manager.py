import yfinance as yf
import pandas as pd
from datetime import date
import os
import time
from .catalog import KATALOG
from . import backend_simulation

def preload_all_data(start_year=2000):
    """
    Lädt alle Daten für die Ticker/ISINs im Katalog ab dem Jahr 2000
    und speichert sie im lokalen CSV-Cache.
    """
    start_date = date(start_year, 1, 1)
    end_date = date.today()
    
    tickers = [v for k, v in KATALOG.items() if v]
    total = len(tickers)
    
    print(f"Starte Pre-loading für {total} Ticker...")
    
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{total}] Verarbeite {ticker}...")
        
        # Nutzen der bestehenden load_data Logik (die jetzt automatisch speichert)
        try:
            data = backend_simulation.load_data(ticker, start_date, end_date)
            if data is not None:
                print(f"  -> OK")
            else:
                print(f"  -> FEHLGESCHLAGEN (keine Daten)")
        except Exception as e:
            print(f"  -> FEHLER: {e}")
            
        # Kurze Pause um Rate-Limits zu vermeiden
        time.sleep(0.5)

if __name__ == "__main__":
    # Dieser Teil ermöglicht das manuelle Starten via Terminal
    # Da wir relative Imports nutzen, muss es als Modul gestartet werden:
    # python -m src.cache_manager
    preload_all_data()
