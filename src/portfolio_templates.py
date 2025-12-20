# Portfolio-Templates für Bank Gutmann
# Simuliert die Übergabe von vordefinierten Portfolios aus einem Beratertool

PORTFOLIO_TEMPLATES = {
    "Nachhaltigkeit (ESG)": {
        "display_name": "Nachhaltigkeit (ESG)",
        "description": "Fokus auf nachhaltige Investments und ESG-Kriterien",
        "assets": [
            {"ticker": "LLY", "name": "Eli Lilly"},
            {"ticker": "GOOGL", "name": "Alphabet / Google"},
            {"ticker": "KO", "name": "Coca-Cola"},
            {"ticker": "AAPL", "name": "Apple"}
        ]
    },
    "Quantitativ (Rule-based)": {
        "display_name": "Quantitativ (Rule-based)",
        "description": "Datengetriebene Auswahl nach quantitativen Kriterien",
        "assets": [
            {"ticker": "NVDA", "name": "NVIDIA"},
            {"ticker": "MSFT", "name": "Microsoft"},
            {"ticker": "ADBE", "name": "Adobe"},
            {"ticker": "ORCL", "name": "Oracle"}
        ]
    },
    "Wachstum (Aktienfokus)": {
        "display_name": "Wachstum (Aktienfokus)",
        "description": "Wachstumsorientierte Aktien mit hohem Potenzial",
        "assets": [
            {"ticker": "PSTG", "name": "Pure Storage"},
            {"ticker": "QCOM", "name": "Qualcomm"},
            {"ticker": "MRVL", "name": "Marvell Technology"},
            {"ticker": "CRM", "name": "Salesforce"}
        ]
    },
    "Ausgewogen (Multi-Asset)": {
        "display_name": "Ausgewogen (Multi-Asset)",
        "description": "Ausgewogenes Portfolio mit Blue Chips und Dividendentiteln",
        "assets": [
            {"ticker": "NESN.SW", "name": "Nestlé"},
            {"ticker": "V", "name": "Visa"},
            {"ticker": "JPM", "name": "JPMorgan Chase"},
            {"ticker": "AAPL", "name": "Apple"}
        ]
    }
}


def load_portfolio_template(portfolio_type: str, budget: float, savings_rate: float, savings_interval: str = "monatlich"):
    """
    Lädt ein Portfolio-Template und verteilt Budget gleichmäßig auf alle Assets
    
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
    
    # Gleichmäßige Verteilung
    einmalerlag_per_asset = budget / num_assets
    sparrate_per_asset = savings_rate / num_assets
    
    loaded_assets = []
    for asset_template in template["assets"]:
        loaded_assets.append({
            "Name": asset_template["name"],
            "ISIN / Ticker": asset_template["ticker"],
            "Einmalerlag (€)": round(einmalerlag_per_asset, 2),
            "Sparbetrag (€)": round(sparrate_per_asset, 2),
            "Spar-Intervall": savings_interval
        })
    
    return loaded_assets


def get_portfolio_display_name(portfolio_type: str) -> str:
    """Gibt den Anzeigenamen eines Portfolio-Typs zurück"""
    if portfolio_type in PORTFOLIO_TEMPLATES:
        return PORTFOLIO_TEMPLATES[portfolio_type]["display_name"]
    return portfolio_type
