# Portfolio-Templates für Bank Gutmann
# Simuliert die Übergabe von vordefinierten Portfolios aus einem Beratertool

PORTFOLIO_TEMPLATES = {
    "Nachhaltigkeit (ESG)": {
        "display_name": "Nachhaltigkeit (ESG)",
        "description": "Fokus auf nachhaltige Investments und ESG-Kriterien",
        "assets": [
            {"ticker": "LLY", "name": "Eli Lilly", "weight": 35},
            {"ticker": "GOOGL", "name": "Alphabet / Google", "weight": 30},
            {"ticker": "KO", "name": "Coca-Cola", "weight": 20},
            {"ticker": "AAPL", "name": "Apple", "weight": 15}
        ]
    },
    "Quantitativ (Rule-based)": {
        "display_name": "Quantitativ (Rule-based)",
        "description": "Datengetriebene Auswahl nach quantitativen Kriterien",
        "assets": [
            {"ticker": "NVDA", "name": "NVIDIA", "weight": 40},
            {"ticker": "MSFT", "name": "Microsoft", "weight": 30},
            {"ticker": "ADBE", "name": "Adobe", "weight": 20},
            {"ticker": "ORCL", "name": "Oracle", "weight": 10}
        ]
    },
    "Wachstum (Aktienfokus)": {
        "display_name": "Wachstum (Aktienfokus)",
        "description": "Wachstumsorientierte Aktien mit hohem Potenzial",
        "assets": [
            {"ticker": "PSTG", "name": "Pure Storage", "weight": 30},
            {"ticker": "QCOM", "name": "Qualcomm", "weight": 30},
            {"ticker": "MRVL", "name": "Marvell Technology", "weight": 25},
            {"ticker": "CRM", "name": "Salesforce", "weight": 15}
        ]
    },
    "Ausgewogen (Multi-Asset)": {
        "display_name": "Ausgewogen (Multi-Asset)",
        "description": "Ausgewogenes Portfolio mit Blue Chips und Dividendentiteln",
        "assets": [
            {"ticker": "NESN.SW", "name": "Nestlé", "weight": 30},
            {"ticker": "V", "name": "Visa", "weight": 30},
            {"ticker": "JPM", "name": "JPMorgan Chase", "weight": 25},
            {"ticker": "AAPL", "name": "Apple", "weight": 15}
        ]
    }
}


def load_portfolio_template(portfolio_type: str, budget: float, savings_rate: float, savings_interval: str = "monatlich"):
    """
    Lädt ein Portfolio-Template und verteilt Budget basierend auf Gewichtungen
    
    Args:
        portfolio_type: Name des Portfolio-Typs (z.B. "Nachhaltigkeit (ESG)")
        budget: Gesamtbudget für Einmalerläge
        savings_rate: Gesamtsparrate pro Intervall
        savings_interval: Sparintervall (monatlich, vierteljährlich, jährlich)
    
    Returns:
        List of asset dictionaries ready for st.session_state.assets
    """
    if portfolio_type not in PORTFOLIO_TEMPLATES:
        return []
    
    template = PORTFOLIO_TEMPLATES[portfolio_type]
    num_assets = len(template["assets"])
    
    loaded_assets = []
    for asset_template in template["assets"]:
        # Gewicht aus Template, Fallback zu Gleichverteilung
        weight = asset_template.get("weight", 100.0 / num_assets)
        
        loaded_assets.append({
            "Name": asset_template["name"],
            "ISIN / Ticker": asset_template["ticker"],
            "Gewichtung (%)": weight,
            "Einmalerlag (€)": (budget * weight) / 100,
            "Sparbetrag (€)": (savings_rate * weight) / 100,
            "Spar-Intervall": savings_interval
        })
    
    return loaded_assets


def get_portfolio_display_name(portfolio_type: str) -> str:
    """Gibt den Anzeigenamen eines Portfolio-Typs zurück"""
    if portfolio_type in PORTFOLIO_TEMPLATES:
        return PORTFOLIO_TEMPLATES[portfolio_type]["display_name"]
    return portfolio_type
