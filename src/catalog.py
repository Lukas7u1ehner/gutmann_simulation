# Dies ist dein zentraler Wertpapier-Katalog (nur ISINs)
# Du kannst diese Liste jederzeit erweitern.

KATALOG = {
    "Bitte wählen...": "",
    
    # --- US Aktien (Tech & Blue Chip) ---
    "Apple Aktie": "US0378331005",
    "Microsoft Aktie": "US5949181045",
    "NVIDIA Aktie": "US67066G1040",
    "Amazon Aktie": "US0231351067",
    "Alphabet A Aktie": "US02079K3059",
    "Meta Platforms Aktie": "US30303M1027",
    "Tesla Aktie": "US88160R1014",
    "Broadcom Aktie": "US11135F1012",
    "Berkshire Hathaway B Aktie": "US0846707026",
    "Eli Lilly Aktie": "US5324571083",
    "JPMorgan Chase Aktie": "US46625H1005",
    "Visa Aktie": "US92826C8394",
    "Mastercard Aktie": "US57636Q1040",
    "Walmart Aktie": "US9311421039",
    "Exxon Mobil Aktie": "US30231G1022",
    "Johnson & Johnson Aktie": "US4781601046",
    "Procter & Gamble Aktie": "US7427181091",
    "Costco Aktie": "US22160K1051",
    "PepsiCo Aktie": "US7134481081",
    "Netflix Aktie": "US64110L1061",
    "Adobe Aktie": "US00724F1012",
    "Salesforce Aktie": "US79466L3024",
    "Vertex Pharmaceuticals Aktie": "US92532F1003",
    "NextEra Energy Aktie": "US65339F1012",
    
    # --- Europäische Aktien ---
    "ASML Aktie": "NL0010273215",
    "LVMH Aktie": "FR0000121014",
    "Novo Nordisk B Aktie": "DK0060534915",
    "SAP Aktie": "DE0007164600",
    "Nestlé Aktie": "CH0038863350",
    "Roche Holding Aktie": "CH0012032048",
    "Shell Aktie": "GB00BP6MXD84",
    "AstraZeneca Aktie": "GB0009895292",
    "Siemens Aktie": "DE0007236101",
    "L'Oréal Aktie": "FR0000120321",
    "Allianz Aktie": "DE0008404005",
    "Schneider Electric Aktie": "FR0000121972",
    "Airbus Aktie": "NL0000235190",
    "TotalEnergies Aktie": "FR0000120271",
    "Iberdrola Aktie": "ES0144580Y14",
    "Vestas Wind Systems Aktie": "DK0061539921",
    "Mercedes-Benz Aktie": "DE0007100000",
    "BMW Aktie": "DE0005190003",
    "Volkswagen Vz Aktie": "DE0007664039",
    "Infineon Aktie": "DE0006231004",
    
    # --- ETFs & Fonds ---
    "iShares Core MSCI World ETF": "IE00B4L5Y983",
    "Vanguard FTSE All-World ETF": "IE00BK5BQT80",
    "iShares Core S&P 500 ETF": "IE00B5BMR087",
    "Vanguard S&P 500 ETF": "IE00B3XXRP09",
    "iShares NASDAQ 100 ETF": "IE00B53SZB19",
    "Invesco EQQQ Nasdaq-100 ETF": "IE0032077012",
    "iShares Core MSCI EM IMI ETF": "IE00BKM4GZ66",
    "iShares STOXX Europe 600 ETF": "DE0002635307",
    "Xtrackers MSCI World ETF": "IE00BJ0KDQ92",
    "Vanguard FTSE North America ETF": "IE00BK5BQW10",
    "iShares MSCI World SRI ETF": "IE00BYX2JD69",
    "iShares Global Clean Energy ETF": "IE00B1XNHC34",
    "Vanguard Growth ETF": "US9229087369",
    "Vanguard EUR Corp. Bond ETF": "IE00BZ163G84",
    "Xtrackers DAX ETF": "LU0274211480",
    "Amundi MSCI World Fonds": "LU1681043599",
    "DWS Top Dividende Fonds": "DE0009848119", 
    "Flossbach von Storch Multiple Opportunities Fonds": "LU0323578657", 
}

# --- INTERNES MAPPING: ISIN -> TICKER (für yfinance) ---
ISIN_TO_TICKER = {
    # US Tech & Blue Chip
    "US0378331005": "AAPL",   # Apple
    "US5949181045": "MSFT",   # Microsoft
    "US67066G1040": "NVDA",   # Nvidia
    "US0231351067": "AMZN",   # Amazon
    "US02079K3059": "GOOGL",  # Alphabet A
    "US30303M1027": "META",   # Meta
    "US88160R1014": "TSLA",   # Tesla
    "US11135F1012": "AVGO",   # Broadcom
    "US0846707026": "BRK-B",  # Berkshire B
    "US5324571083": "LLY",    # Eli Lilly
    "US46625H1005": "JPM",    # JPMorgan
    "US92826C8394": "V",      # Visa
    "US57636Q1040": "MA",     # Mastercard
    "US9311421039": "WMT",    # Walmart
    "US30231G1022": "XOM",    # Exxon Mobil
    "US4781601046": "JNJ",    # Johnson & Johnson
    "US7427181091": "PG",     # Procter & Gamble
    "US22160K1051": "COST",   # Costco
    "US7134481081": "PEP",    # PepsiCo
    "US64110L1061": "NFLX",   # Netflix
    "US00724F1012": "ADBE",   # Adobe
    "US79466L3024": "CRM",    # Salesforce
    "US92532F1003": "VRTX",   # Vertex
    "US65339F1012": "NEE",    # NextEra
    
    # Europäische Aktien (oft via Xetra .DE oder Heimatbörse)
    "NL0010273215": "ASML.AS",   # ASML
    "FR0000121014": "MC.PA",     # LVMH
    "DK0060534915": "NOVO-B.CO", # Novo Nordisk
    "DE0007164600": "SAP.DE",    # SAP
    "CH0038863350": "NESN.SW",   # Nestlé
    "CH0012032048": "ROG.SW",    # Roche
    "GB00BP6MXD84": "SHEL.L",    # Shell
    "GB0009895292": "AZN.L",     # AstraZeneca
    "DE0007236101": "SIE.DE",    # Siemens
    "FR0000120321": "OR.PA",     # L'Oréal
    "DE0008404005": "ALV.DE",    # Allianz
    "FR0000121972": "SU.PA",     # Schneider Electric
    "NL0000235190": "AIR.PA",    # Airbus
    "FR0000120271": "TTE.PA",    # TotalEnergies
    "ES0144580Y14": "IBE.MC",    # Iberdrola
    "DK0061539921": "VWS.CO",    # Vestas
    "DE0007100000": "MBG.DE",    # Mercedes-Benz
    "DE0005190003": "BMW.DE",    # BMW
    "DE0007664039": "VOW3.DE",   # VW Vz
    "DE0006231004": "IFX.DE",    # Infineon

    # ETFs & Fonds (Mapping auf liquide Börsenplätze)
    "IE00B4L5Y983": "EUNL.DE",   # Core MSCI World
    "IE00BK5BQT80": "VWCE.DE",   # FTSE All-World
    "IE00B5BMR087": "SXR8.DE",   # S&P 500 Acc
    "IE00B3XXRP09": "VUSA.DE",   # S&P 500 Dist
    "IE00B53SZB19": "SXRV.DE",   # Nasdaq 100
    "IE0032077012": "EQQQ.DE",   # EQQQ Nasdaq 100
    "IE00BKM4GZ66": "IS3N.DE",   # MSCI EM IMI
    "DE0002635307": "EXSA.DE",   # Stoxx 600
    "IE00BJ0KDQ92": "XDWD.DE",   # Xtrackers MSCI World
    "IE00BK5BQW10": "VNRA.DE",   # FTSE North America
    "IE00BYX2JD69": "2B7K.DE",   # MSCI World SRI
    "IE00B1XNHC34": "IQQH.DE",   # Clean Energy
    "US9229087369": "VUG",       # Vanguard Growth (US-Ticker)
    "IE00BZ163G84": "VECP.DE",   # Corp Bond
    "LU0274211480": "DBX1.DE",   # DAX
    "LU1681043599": "CW8.PA",    # Amundi MSCI World (Beispiel für Fonds-Proxy, oft ETF)
    "DE0009848119": "0P00000S6R.F", # DWS Top Dividende (Symbol via Frankfurt)
    "LU0323578657": "0P00000XBT.F", # Flossbach Multiple Opp. (Symbol via Frankfurt)
}
