from fpdf import FPDF
import pandas as pd
from datetime import datetime
import os
import tempfile

# --- HELPER: TEXT BEREINIGUNG ---
def clean_text(text):
    """
    Ersetzt Sonderzeichen, die von der Standard-Schriftart (Latin-1)
    nicht unterstützt werden.
    """
    if text is None:
        return ""
    
    text = str(text)
    
    # Währungen und Typografie
    text = text.replace("€", "EUR")
    text = text.replace("–", "-") 
    text = text.replace("—", "-")
    text = text.replace("„", '"').replace("“", '"')
    text = text.replace("’", "'")
    text = text.replace("%", " %") # Leerzeichen vor % für Lesbarkeit
    
    return text

# Farben (RGB)
COLOR_DARK_GREEN = (37, 52, 47)      # Gutmann Dark
COLOR_ACCENT_GREEN = (179, 212, 99)  # Gutmann Accent
COLOR_TEXT_GREY = (100, 100, 100)
COLOR_LIGHT_GREY = (245, 245, 245)
COLOR_WHITE = (255, 255, 255)

# Pfad zum Logo
LOGO_PATH = "assets/gutmann_logo.png"

# Textbausteine
DISCLAIMER_TEXT = """Für diese Aufstellung werden – soweit entsprechende Daten verfügbar sind – die Börsen- bzw. Marktpreise zum jeweiligen Stichtag als Grundlage herangezogen. Diese Stichtagskurse dienen einer einheitlichen Bewertung zum ausgewiesenen Zeitpunkt und ermöglichen eine vergleichbare Darstellung der enthaltenen Finanzinstrumente.

Bei tatsächlichen Dispositionen, insbesondere bei Kauf- oder Verkaufsvorgängen, können die effektiv erzielten Kurse von den hier angeführten Stichtagswerten abweichen.

Alle ausgewiesenen Kurse und Werte wurden mit größtmöglicher Sorgfalt aus als zuverlässig erachteten Quellen ermittelt. Dennoch erfolgen sämtliche Angaben ohne Gewähr. Sie stellen weder eine Zusicherung bestimmter Kursstände noch eine verbindliche Bewertung dar.

Die Bank Gutmann AG übernimmt keine Haftung für die Richtigkeit, Aktualität oder Vollständigkeit der in dieser Aufstellung enthaltenen Informationen. Eine Haftung für Folgen, die aus der Nutzung dieser Angaben oder aus darauf basierenden Entscheidungen entstehen, ist ausgeschlossen."""

GLOSSAR_TEXT = {
    "Startkapital": "Kapital, das zu Beginn der Simulation einmalig investiert wird.",
    "Sparrate (monatlich)": "Regelmäßiger Betrag, der gemäß Intervall zusätzlich investiert wird.",
    "Historische Simulation": "Rückblickende Berechnung auf Basis historischer Kursdaten im gewählten Zeitraum. Zeigt, wie sich das Portfolio in der Vergangenheit unter realen Marktbedingungen entwickelt hätte.",
    "Zukunftsprognose / Monte Carlo": "Simulation tausender möglicher zukünftiger Entwicklungen basierend auf statistischen Rendite- und Risikoannahmen (Volatilität).",
    "Median Prognose": "Der statistisch wahrscheinlichste Pfad (Median). 50 % der simulierten Szenarien verlaufen besser, 50 % schlechter.",
    "Nominal vs. Real": "Nominal: Reiner Geldwert ohne Berücksichtigung der Inflation.\nReal: Inflationsbereinigter Wert (Kaufkraft) basierend auf historischen Inflationsdaten oder Modellannahmen."
}

class GutmannReport(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.set_auto_page_break(auto=True, margin=20)
        self.total_pages_alias = "{nb}"

    def header(self):
        # Kein Header auf Seite 1 (Deckblatt)
        if self.page_no() > 1:
            if os.path.exists(LOGO_PATH):
                self.image(LOGO_PATH, x=15, y=10, w=40)
            
            self.set_font("Helvetica", size=8)
            self.set_text_color(*COLOR_TEXT_GREY)
            date_str = datetime.now().strftime("%d.%m.%Y")
            self.cell(0, 10, f"Exportdatum: {date_str}", align="R", new_x="LMARGIN", new_y="NEXT")
            
            self.set_draw_color(*COLOR_ACCENT_GREEN)
            self.set_line_width(0.5)
            self.line(15, 25, 195, 25)
            self.ln(10)

    def footer(self):
        # Kein Footer auf Seite 1
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font("Helvetica", size=8)
            self.set_text_color(*COLOR_TEXT_GREY)
            # Seite X-1, da Seite 1 das Deckblatt ist
            current_display_page = self.page_no() - 1
            self.cell(0, 10, f"Seite {current_display_page}", align="C")

    def create_title_page(self):
        self.add_page()
        # Hintergrund
        self.set_fill_color(*COLOR_DARK_GREEN)
        self.rect(0, 0, 210, 297, "F")
        
        # Logo Box
        self.set_fill_color(255, 255, 255)
        self.rect(0, 40, 210, 60, "F")
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=65, y=50, w=80)
        
        self.ln(140)
        
        # Titel
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 32)
        self.multi_cell(0, 15, "Wertpapierplan\nSimulation Report", align="C")
        
        self.ln(20)
        self.set_font("Helvetica", "", 16)
        self.set_text_color(*COLOR_ACCENT_GREEN)
        self.cell(0, 10, "Historische Simulation & Zukunftsprognose", align="C", new_x="LMARGIN", new_y="NEXT")
        
        self.ln(40)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(200, 200, 200)
        now = datetime.now().strftime("%d.%m.%Y, %H:%M Uhr")
        self.cell(0, 10, f"Erstellt am: {now}", align="C", new_x="LMARGIN", new_y="NEXT")

    def create_portfolio_page(self, assets, params):
        self.add_page()
        self._add_section_title("1. Portfolio & Einstellungen")
        
        # Einstellungen (Schönere Tabelle ohne Titel)
        self.set_font("Helvetica", "", 10)
        
        # Box für Global Settings
        self.set_fill_color(*COLOR_LIGHT_GREY)
        self.set_draw_color(200, 200, 200)
        
        # Key-Value Grid
        col_width_key = 60
        col_width_val = 60
        
        for key, val in params.items():
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*COLOR_DARK_GREEN)
            self.cell(col_width_key, 8, clean_text(key), border="B", align="L")
            
            self.set_font("Helvetica", "", 10)
            self.set_text_color(0, 0, 0)
            self.cell(col_width_val, 8, clean_text(val), border="B", align="L", new_x="LMARGIN", new_y="NEXT")
            
        self.ln(15)
        
        # Positionen Tabelle
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*COLOR_DARK_GREEN)
        self.cell(0, 10, "Portfolio Positionen", new_x="LMARGIN", new_y="NEXT")
        
        # Header
        self.set_fill_color(*COLOR_DARK_GREEN)
        self.set_text_color(*COLOR_ACCENT_GREEN)
        self.set_font("Helvetica", "B", 9)
        
        widths = [60, 35, 30, 30, 30]
        headers = ["Name", "ISIN", "Start (EUR)", "Sparrate (EUR)", "Intervall"]
        
        for i, h in enumerate(headers):
            self.cell(widths[i], 9, h, border=1, fill=True, align="C")
        self.ln()
        
        # Body
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", "", 9)
        fill = False
        
        for asset in assets:
            if not asset.get("ISIN / Ticker"): continue
            
            # Zebra-Striping
            self.set_fill_color(*COLOR_LIGHT_GREY)
            fill = not fill
            
            name = clean_text(asset.get("Name", ""))[:32]
            isin = clean_text(asset.get("ISIN / Ticker", ""))
            start_val = f"{asset.get('Einmalerlag (€)', 0):,.2f}"
            spar_val = f"{asset.get('Sparbetrag (€)', 0):,.2f}"
            intervall = clean_text(asset.get("Spar-Intervall", ""))
            
            row_data = [name, isin, start_val, spar_val, intervall]
            aligns = ["L", "L", "R", "R", "C"]
            
            for i, data in enumerate(row_data):
                self.cell(widths[i], 8, data, border=1, fill=fill, align=aligns[i])
            self.ln()

    def create_history_page(self, chart_image_bytes, kpi_data):
        self.add_page()
        self._add_section_title("2. Historische Simulation")
        
        # Chart Image
        if chart_image_bytes:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(chart_image_bytes)
                tmp_path = tmp.name
            try:
                # Bild etwas größer, zentriert
                self.image(tmp_path, x=10, w=190)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        else:
            self.set_text_color(200, 0, 0)
            self.cell(0, 10, "Chart konnte nicht generiert werden.", new_x="LMARGIN", new_y="NEXT")

        self.ln(5)
        
        # KPI Tabelle rendern
        if kpi_data:
            self._render_kpi_table("Ergebnisse (Historie)", kpi_data)
        else:
            self.set_font("Helvetica", "I", 10)
            self.set_text_color(*COLOR_TEXT_GREY)
            self.cell(0, 10, "Keine historischen Leistungsdaten verfügbar.", new_x="LMARGIN", new_y="NEXT")

    def create_forecast_page(self, chart_image_bytes, kpi_data):
        self.add_page()
        self._add_section_title("3. Zukunftsprognose (Monte Carlo)")
        
        if chart_image_bytes:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(chart_image_bytes)
                tmp_path = tmp.name
            try:
                self.image(tmp_path, x=10, w=190)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        else:
            self.set_text_color(*COLOR_TEXT_GREY)
            self.set_font("Helvetica", "I", 10)
            self.multi_cell(0, 10, "Hinweis: Für diesen Report lagen keine Prognose-Daten vor.\nBitte führen Sie die Simulation im Tab 'Zukunftsprognose' einmal aus, bevor Sie das PDF erstellen.", align="C")
            
        self.ln(5)
        
        if kpi_data:
            self._render_kpi_table("Szenario-Analyse (Median)", kpi_data)

    def create_glossary_page(self):
        self.add_page()
        self._add_section_title("4. Glossar & Erklärungen")
        
        self.set_font("Helvetica", "", 10)
        
        for term, definition in GLOSSAR_TEXT.items():
            # Begriff fett
            self.set_text_color(*COLOR_DARK_GREEN)
            self.set_font("Helvetica", "B", 11)
            self.cell(0, 7, clean_text(term), new_x="LMARGIN", new_y="NEXT")
            
            # Definition normal
            self.set_text_color(50, 50, 50)
            self.set_font("Helvetica", "", 10)
            # Bereinigen und Multi-Cell für Umbruch
            self.multi_cell(0, 5, clean_text(definition))
            self.ln(6)

    def create_disclaimer_page(self):
        self.add_page()
        self._add_section_title("Rechtliche Hinweise")
        
        self.set_font("Helvetica", "", 9)
        self.set_text_color(80, 80, 80)
        
        paragraphs = clean_text(DISCLAIMER_TEXT).split('\n\n')
        for p in paragraphs:
            self.multi_cell(0, 5, p)
            self.ln(5)

    def _add_section_title(self, title):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*COLOR_DARK_GREEN)
        self.cell(0, 10, clean_text(title), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*COLOR_ACCENT_GREEN)
        self.set_line_width(0.7)
        self.line(15, self.get_y(), 60, self.get_y())
        self.ln(10)

    def _render_kpi_table(self, title, data_dict):
        """Hilfsfunktion um KPIs schön darzustellen"""
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*COLOR_DARK_GREEN)
        self.cell(0, 10, clean_text(title), new_x="LMARGIN", new_y="NEXT")
        
        self.set_font("Helvetica", "", 10)
        self.set_draw_color(220, 220, 220)
        
        for k, v in data_dict.items():
            # Label
            self.set_font("Helvetica", "", 10)
            self.set_text_color(50, 50, 50)
            self.cell(90, 8, clean_text(k), border="B")
            
            # Value (Fett)
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(0, 0, 0)
            self.cell(0, 8, clean_text(v), border="B", align="R", new_x="LMARGIN", new_y="NEXT")
        
        self.ln(5)


def generate_pdf_report(assets, global_params, hist_fig, hist_kpis, prog_fig, prog_kpis):
    pdf = GutmannReport()
    
    # 1. Titel & Portfolio
    pdf.create_title_page()
    pdf.create_portfolio_page(assets, global_params)
    
    # 2. Historie
    hist_img = None
    if hist_fig:
        img_fig = hist_fig
        # Weißer Hintergrund für Druck
        img_fig.update_layout(template="simple_white", plot_bgcolor="white", paper_bgcolor="white", font_color="black")
        hist_img = img_fig.to_image(format="png", width=1200, height=650, scale=2)
    
    pdf.create_history_page(hist_img, hist_kpis)
    
    # 3. Prognose (Wird immer erstellt, auch wenn leer -> Hinweis erscheint)
    prog_img = None
    if prog_fig:
        p_fig = prog_fig
        p_fig.update_layout(template="simple_white", plot_bgcolor="white", paper_bgcolor="white", font_color="black")
        prog_img = p_fig.to_image(format="png", width=1200, height=650, scale=2)
        
    pdf.create_forecast_page(prog_img, prog_kpis)
    
    # 4. Glossar
    pdf.create_glossary_page()
    
    # 5. Disclaimer
    pdf.create_disclaimer_page()
    
    return bytes(pdf.output())