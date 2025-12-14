from fpdf import FPDF
import pandas as pd
from datetime import datetime
import os
import tempfile

# --- HELPER: TEXT BEREINIGUNG ---
def clean_text(text):
    """
    Ersetzt Sonderzeichen für Latin-1 Encoding (Standard in FPDF).
    """
    if text is None:
        return ""
    text = str(text)
    text = text.replace("€", "EUR")
    text = text.replace("–", "-").replace("—", "-") # Lange Striche korrigieren
    text = text.replace("„", '"').replace("“", '"').replace("’", "'")
    text = text.replace("%", " %")
    return text

# --- KONFIGURATION ---
COLOR_DARK_GREEN = (37, 52, 47)      # Gutmann Dark
COLOR_ACCENT_GREEN = (179, 212, 99)  # Gutmann Accent
COLOR_TEXT_GREY = (80, 80, 80)
COLOR_LIGHT_GREY = (245, 245, 245)
LOGO_PATH = "assets/gutmann_logo.png"

# --- TEXTE ---
DISCLAIMER_TEXT = """Für diese Aufstellung werden – soweit entsprechende Daten verfügbar sind – die Börsen- bzw. Marktpreise zum jeweiligen Stichtag als Grundlage herangezogen. Diese Stichtagskurse dienen einer einheitlichen Bewertung zum ausgewiesenen Zeitpunkt.

Bei tatsächlichen Dispositionen, insbesondere bei Kauf- oder Verkaufsvorgängen, können die effektiv erzielten Kurse von den hier angeführten Stichtagswerten abweichen.

Alle ausgewiesenen Kurse und Werte wurden mit größtmöglicher Sorgfalt aus als zuverlässig erachteten Quellen ermittelt. Dennoch erfolgen sämtliche Angaben ohne Gewähr. Sie stellen weder eine Zusicherung bestimmter Kursstände noch eine verbindliche Bewertung dar.

Die Bank Gutmann AG übernimmt keine Haftung für die Richtigkeit, Aktualität oder Vollständigkeit der in dieser Aufstellung enthaltenen Informationen. Eine Haftung für Folgen, die aus der Nutzung dieser Angaben oder aus darauf basierenden Entscheidungen entstehen, ist ausgeschlossen."""

GLOSSAR_TEXT = {
    "Startkapital": "Kapital, das zu Beginn der Simulation einmalig investiert wird.",
    "Sparrate (monatlich)": "Regelmäßiger Betrag, der gemäß Intervall zusätzlich investiert wird.",
    "Historische Simulation": "Rückblickende Berechnung auf Basis historischer Kursdaten im gewählten Zeitraum. Zeigt, wie sich das Portfolio in der Vergangenheit unter realen Marktbedingungen entwickelt hätte.",
    "Zukunftsprognose / Monte Carlo": "Simulation tausender möglicher zukünftiger Entwicklungen basierend auf statistischen Rendite- und Risikoannahmen (Volatilität).",
    "Median-Prognose": "Der statistisch wahrscheinlichste Pfad (Median). 50 % der simulierten Szenarien verlaufen besser, 50 % schlechter.",
    "Nominal vs. Real": "Nominal: Reiner Geldwert ohne Berücksichtigung der Inflation.\nReal: Inflationsbereinigter Wert (Kaufkraft) basierend auf historischen Inflationsdaten oder Modellannahmen."
}

class GutmannReport(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.set_auto_page_break(auto=True, margin=20)
        self.alias_nb_pages() # Für Gesamtseitenzahl

    def header(self):
        # Header erst ab Seite 2 (logisch Seite 1) anzeigen
        if self.page_no() > 1:
            if os.path.exists(LOGO_PATH):
                self.image(LOGO_PATH, x=15, y=10, w=35)
            
            self.set_font("Helvetica", size=8)
            self.set_text_color(*COLOR_TEXT_GREY)
            date_str = datetime.now().strftime("%d.%m.%Y")
            self.cell(0, 10, f"Exportdatum: {date_str}", align="R", new_x="LMARGIN", new_y="NEXT")
            
            # Grüne Linie
            self.set_draw_color(*COLOR_ACCENT_GREEN)
            self.set_line_width(0.5)
            self.line(15, 25, 195, 25)
            self.ln(10)

    def footer(self):
        # Footer erst ab Seite 2
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font("Helvetica", size=8)
            self.set_text_color(*COLOR_TEXT_GREY)
            
            # Logische Seitennummerierung: Deckblatt zählt nicht mit
            # Seite 2 im PDF = Seite 1 im Report
            current_vis_page = self.page_no() - 1
            # {nb} ist der Platzhalter für Gesamtseiten (muss man ggf. manuell korrigieren, 
            # aber fpdf macht das meist relativ zur physischen Seite. Wir lassen "von X" hier weg oder nutzen nur "Seite X")
            self.cell(0, 10, f"Seite {current_vis_page}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*COLOR_DARK_GREEN)
        self.cell(0, 10, clean_text(title), new_x="LMARGIN", new_y="NEXT")
        
        # Grüner Unterstrich (kurz)
        self.set_draw_color(*COLOR_ACCENT_GREEN)
        self.set_line_width(0.8)
        self.line(15, self.get_y(), 50, self.get_y())
        self.ln(8)

    def create_title_page(self):
        self.add_page()
        # Dunkler Hintergrund
        self.set_fill_color(*COLOR_DARK_GREEN)
        self.rect(0, 0, 210, 297, "F")
        
        # Weißer Balken für Logo
        self.set_fill_color(255, 255, 255)
        self.rect(0, 40, 210, 60, "F")
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=65, y=52, w=80)
        
        self.ln(130)
        
        # Titel
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 36)
        self.multi_cell(0, 18, "Wertpapierplan\nSimulation Report", align="C")
        
        self.ln(10)
        self.set_font("Helvetica", "", 14)
        self.set_text_color(*COLOR_ACCENT_GREEN)
        self.cell(0, 10, clean_text("Historische Simulation & Zukunftsprognose"), align="C", new_x="LMARGIN", new_y="NEXT")
        
        self.ln(40)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(200, 200, 200)
        now = datetime.now().strftime("%d.%m.%Y, %H:%M Uhr")
        self.cell(0, 10, f"Erstellt am: {now}", align="C", new_x="LMARGIN", new_y="NEXT")

    def create_portfolio_page(self, assets, params):
        self.add_page()
        self.section_title("1. Portfolio & Eingaben")
        
        # Settings Block (Schönere Darstellung)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*COLOR_DARK_GREEN)
        self.cell(0, 10, "Einstellungen", new_x="LMARGIN", new_y="NEXT")
        
        self.set_font("Helvetica", "", 10)
        self.set_text_color(0, 0, 0)
        
        # Einfache Liste statt Tabelle für Settings
        for k, v in params.items():
            self.cell(60, 6, clean_text(k), border=0)
            self.set_font("Helvetica", "B", 10)
            self.cell(0, 6, clean_text(v), border=0, new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "", 10)
            
        self.ln(10)
        
        # Positionen Tabelle
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*COLOR_DARK_GREEN)
        self.cell(0, 10, "Portfolio Positionen", new_x="LMARGIN", new_y="NEXT")
        
        # Header
        self.set_fill_color(*COLOR_LIGHT_GREY)
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", "B", 9)
        
        cols = [70, 30, 30, 30, 30] 
        headers = ["Name", "ISIN", "Start (EUR)", "Sparrate", "Intervall"]
        
        for i, h in enumerate(headers):
            self.cell(cols[i], 8, h, border="B", fill=True)
        self.ln()
        
        # Body
        self.set_font("Helvetica", "", 9)
        for asset in assets:
            if not asset.get("ISIN / Ticker"): continue
            
            name = clean_text(asset.get("Name", ""))[:40]
            isin = clean_text(asset.get("ISIN / Ticker", ""))
            start = f"{asset.get('Einmalerlag (€)', 0):,.2f}"
            spar = f"{asset.get('Sparbetrag (€)', 0):,.2f}"
            inter = clean_text(asset.get("Spar-Intervall", ""))[:10]
            
            data = [name, isin, start, spar, inter]
            aligns = ["L", "L", "R", "R", "L"]
            
            for i, d in enumerate(data):
                self.cell(cols[i], 8, d, border="B", align=aligns[i])
            self.ln()

    def create_chart_page(self, title, chart_bytes, kpi_dict, note=None):
        """Generische Seite für Historie & Prognose mit Chart und KPI-Tabelle"""
        self.add_page()
        self.section_title(title)
        
        # Chart
        if chart_bytes:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(chart_bytes)
                tmp_path = tmp.name
            try:
                self.image(tmp_path, x=10, w=190)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        else:
            self.set_text_color(200, 0, 0)
            self.cell(0, 10, "Chart nicht verfügbar.", new_x="LMARGIN", new_y="NEXT")
        
        self.ln(5)
        
        # KPI Tabelle (Grüne Linien Style)
        if kpi_dict:
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*COLOR_DARK_GREEN)
            
            # Titel je nach Kontext erraten oder fix setzen
            table_title = "Ergebnisse & Kennzahlen"
            self.cell(0, 10, table_title, new_x="LMARGIN", new_y="NEXT")
            
            self.set_draw_color(*COLOR_ACCENT_GREEN)
            self.set_line_width(0.4)
            
            for k, v in kpi_dict.items():
                self.set_font("Helvetica", "", 10)
                self.set_text_color(0, 0, 0) # Schwarz
                self.cell(100, 8, clean_text(k), border="B") # Label
                
                self.set_font("Helvetica", "B", 10)
                self.cell(0, 8, clean_text(v), border="B", align="R", new_x="LMARGIN", new_y="NEXT") # Wert
        
        if note:
            self.ln(5)
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(*COLOR_TEXT_GREY)
            self.multi_cell(0, 5, clean_text(note))

    def create_glossary_page(self):
        self.add_page()
        self.section_title("4. Erklärungen")
        
        self.set_font("Helvetica", "", 10)
        self.set_text_color(0, 0, 0)
        
        for term, definition in GLOSSAR_TEXT.items():
            # Begriff fett
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*COLOR_DARK_GREEN)
            self.cell(0, 6, clean_text(term), new_x="LMARGIN", new_y="NEXT")
            
            # Erklärung normal
            self.set_font("Helvetica", "", 10)
            self.set_text_color(60, 60, 60)
            self.multi_cell(0, 5, clean_text(definition))
            self.ln(4)

    def create_disclaimer_page(self):
        self.add_page()
        self.section_title("5. Rechtliche Hinweise")
        
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*COLOR_TEXT_GREY)
        
        paragraphs = clean_text(DISCLAIMER_TEXT).split('\n\n')
        for p in paragraphs:
            self.multi_cell(0, 5, p)
            self.ln(5)


def generate_pdf_report(assets, global_params, hist_fig, hist_kpis, prog_fig, prog_kpis):
    pdf = GutmannReport()
    
    # 1. Deckblatt & Portfolio
    pdf.create_title_page()
    pdf.create_portfolio_page(assets, global_params)
    
    # 2. Historie
    hist_img = None
    if hist_fig:
        img_fig = hist_fig
        img_fig.update_layout(template="simple_white", plot_bgcolor="white", paper_bgcolor="white", font_color="black", showlegend=True)
        # Breiteres Bild für bessere Lesbarkeit im PDF
        hist_img = img_fig.to_image(format="png", width=1400, height=750, scale=2)
    
    pdf.create_chart_page("2. Historische Simulation", hist_img, hist_kpis)
    
    # 3. Prognose
    prog_img = None
    prog_note = None
    if prog_fig:
        p_fig = prog_fig
        p_fig.update_layout(template="simple_white", plot_bgcolor="white", paper_bgcolor="white", font_color="black", showlegend=True)
        prog_img = p_fig.to_image(format="png", width=1400, height=750, scale=2)
    else:
        # Hinweis, falls Daten fehlen (weil nicht berechnet)
        prog_note = "Hinweis: Keine Prognosedaten verfügbar. Bitte 'Zukunftsprognose'-Tab öffnen, um Berechnung zu starten."

    pdf.create_chart_page("3. Zukunftsprognose (Monte Carlo)", prog_img, prog_kpis, note=prog_note)
    
    # 4. Glossar (NEU)
    pdf.create_glossary_page()
    
    # 5. Rechtliches
    pdf.create_disclaimer_page()
    
    return bytes(pdf.output())