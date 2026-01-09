# Portfolio-Templates für Bank Gutmann
# Vordefinierte Szenarien für Demo-Links

PORTFOLIO_TEMPLATES = {
    "szenario1": {
        "display_name": "Szenario 1",
        "description": "ESG & Clean Energy Mix",
        "assets": [
            {"isin": "IE00BYX2JD69", "name": "iShares MSCI World SRI ETF", "weight": 70},
            {"isin": "US88160R1014", "name": "Tesla Aktie", "weight": 10},
            {"isin": "US65339F1012", "name": "NextEra Energy Aktie", "weight": 10},
            {"isin": "DK0061539921", "name": "Vestas Wind Systems Aktie", "weight": 10},
        ]
    },
    "szenario2": {
        "display_name": "Szenario 2",
        "description": "Tech Growth Focus",
        "assets": [
            {"isin": "US9229087369", "name": "Vanguard Growth ETF", "weight": 40},
            {"isin": "US67066G1040", "name": "NVIDIA Aktie", "weight": 15},
            {"isin": "US0231351067", "name": "Amazon Aktie", "weight": 20},
            {"isin": "US92532F1003", "name": "Vertex Pharmaceuticals Aktie", "weight": 25},
        ]
    },
    "szenario3": {
        "display_name": "Szenario 3",
        "description": "Balanced Core",
        "assets": [
            {"isin": "IE00B4L5Y983", "name": "iShares Core MSCI World ETF", "weight": 60},
            {"isin": "IE00BZ163G84", "name": "Vanguard EUR Corp. Bond ETF", "weight": 40},
        ]
    },
    "szenario4": {
        "display_name": "Szenario 4",
        "description": "Diversified Global Mix",
        "assets": [
            {"isin": "IE00B4L5Y983", "name": "iShares Core MSCI World ETF", "weight": 20},
            {"isin": "IE00B5BMR087", "name": "iShares Core S&P 500 ETF", "weight": 20},
            {"isin": "US0378331005", "name": "Apple Aktie", "weight": 10},
            {"isin": "US5949181045", "name": "Microsoft Aktie", "weight": 10},
            {"isin": "NL0010273215", "name": "ASML Aktie", "weight": 15},
            {"isin": "FR0000121014", "name": "LVMH Aktie", "weight": 10},
            {"isin": "CH0038863350", "name": "Nestlé Aktie", "weight": 10},
            {"isin": "DE0007164600", "name": "SAP Aktie", "weight": 5},
        ]
    }
}


def load_portfolio_template(portfolio_type: str, budget: float, savings_rate: float, savings_interval: str = "monatlich"):
    """
    Lädt ein Portfolio-Template und verteilt Budget basierend auf Gewichtungen
    """
    # Case-insensitive matching
    matched_key = None
    norm_type = portfolio_type.lower()
    for key in PORTFOLIO_TEMPLATES.keys():
        if norm_type == key.lower():
            matched_key = key
            break
    
    if not matched_key:
        return []
    
    template = PORTFOLIO_TEMPLATES[matched_key]
    
    loaded_assets = []
    for asset_template in template["assets"]:
        weight = asset_template["weight"]
        
        loaded_assets.append({
            "Name": asset_template["name"],
            "ISIN / Ticker": asset_template["isin"],
            "Gewichtung (%)": weight,
            "Einmalerlag (€)": (budget * weight) / 100,
            "Sparbetrag (€)": (savings_rate * weight) / 100,
            "Spar-Intervall": savings_interval
        })
    
    return loaded_assets


def get_portfolio_display_name(portfolio_type: str) -> str:
    """Gibt den Anzeigenamen eines Portfolio-Typs zurück"""
    # Überprüfen ob es ein bekanntes Szenario ist, sonst leeren String (da wir keine Typen mehr anzeigen wollen)
    norm_type = portfolio_type.lower()
    for key in PORTFOLIO_TEMPLATES.keys():
        if norm_type == key.lower():
            return PORTFOLIO_TEMPLATES[key]["display_name"]
    return ""
