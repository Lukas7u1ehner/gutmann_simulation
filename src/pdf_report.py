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
LOGO_PATH = "assets/gutmann_logo-removebg-preview.png"

# --- TEXTE ---
DISCLAIMER_TEXT = """Für diese Aufstellung werden – soweit entsprechende Daten verfügbar sind – die Börsen- bzw. Marktpreise zum jeweiligen Stichtag als Grundlage herangezogen. Diese Stichtagskurse dienen einer einheitlichen Bewertung zum ausgewiesenen Zeitpunkt.

Bei tatsächlichen Dispositionen, insbesondere bei Kauf- oder Verkaufsvorgängen, können die effektiv erzielten Kurse von den hier angeführten Stichtagswerten abweichen.

Alle ausgewiesenen Kurse und Werte wurden mit größtmöglicher Sorgfalt aus als zuverlässig erachteten Quellen ermittelt. Dennoch erfolgen sämtliche Angaben ohne Gewähr. Sie stellen weder eine Zusicherung bestimmter Kursstände noch eine verbindliche Bewertung dar.

Die Bank Gutmann AG übernimmt keine Haftung für die Richtigkeit, Aktualität oder Vollständigkeit der in dieser Aufstellung enthaltenen Informationen. Eine Haftung für Folgen, die aus der Nutzung dieser Angaben oder aus darauf basierenden Entscheidungen entstehen, ist ausgeschlossen."""

GLOSSAR_TEXT = {
    "Startkapital": "Das Kapital, welches zu Beginn der Simulation einmalig in das Portfolio investiert wird.",
    "Sparrate (monatlich)": "Ein regelmäßiger Investitionsbetrag, der im gewählten Intervall (z.B. monatlich) zum Portfolio hinzugefügt wird.",
    "Historische Simulation": "Eine Analyse, die zeigt, wie sich das definierte Portfolio in einem vergangenen Zeitraum entwickelt hätte. Dabei werden reale, historische Marktdaten verwendet, um die Performance unter echten Marktbedingungen zu veranschaulichen.",
    "Zukunftsprognose (Monte Carlo)": "Eine statistische Simulationstechnik, die tausende möglicher zukünftiger Marktentwicklungen berechnet. Sie basiert auf den erwarteten Renditen und der Volatilität (Schwankungsbreite) der Portfolio-Bausteine.",
    "Median-Prognose": "Der mittlere Entwicklungspfad der Zukunftssimulation. Das bedeutet, dass die Wahrscheinlichkeit für ein besseres oder schlechteres Ergebnis jeweils bei 50 % liegt. Dies ist das statistisch wahrscheinlichste Szenario.",
    "Nominal vs. Real": "Nominal bezeichnet den reinen Geldwert ohne Berücksichtigung der Geldentwertung (Inflation).\nReal bezeichnet den um die Inflation bereinigten Wert, der die tatsächliche Kaufkraft widerspiegelt.",
    "Volatilität": "Ein Maß für die Schwankungsbreite eines Wertpapierkurses. Eine höhere Volatilität bedeutet größere Kursschwankungen und damit potenziell höheres Risiko, aber auch höhere Chancen.",
    "Rendite": "Der Gesamtertrag einer Kapitalanlage, ausgedrückt in Prozent pro Jahr (p.a.) oder als absoluter Wert, unter Berücksichtigung von Kursgewinnen und Ausschüttungen.",
    "Gewichtung": "Der prozentuale Anteil einer einzelnen Position am Gesamtportfolio. Die Summe aller Gewichtungen ergibt idealerweise 100 %.",
    "ISIN": "International Securities Identification Number. Eine zwölftstellige Buchstaben- und Zahlenkombination, die ein Wertpapier eindeutig identifiziert."
}
# Sortieren nach Alphabet
GLOSSAR_TEXT = dict(sorted(GLOSSAR_TEXT.items()))

class GutmannReport(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.set_auto_page_break(auto=True, margin=20)
        # CRITICAL FIX: Kompression deaktivieren, damit Placeholder im Byte-Stream gefunden wird
        self.set_compression(False)
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
            

            # Logische Seitennummerierung: Deckblatt zählt nicht mit (Start bei 1 auf physischer Seite 2)
            current_vis_page = self.page_no() - 1
            
            # {nb_true} ist unser eigener Placeholder, den wir am Ende ersetzen
            self.cell(0, 10, f"Seite {current_vis_page} von {{nb_true}}", align="C")

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
        # Voller Hintergrund (kein weißer Balken mehr)
        self.set_fill_color(*COLOR_DARK_GREEN)
        self.rect(0, 0, 210, 297, "F")
        
        # Logo zentriert im oberen Drittel
        if os.path.exists(LOGO_PATH):
            # Wir nehmen an, dass das Logo transparent ist oder auf dunklem Grund gut aussieht.
            # Falls es einen weißen Rand hat, wäre ein transparentes PNG besser.
            self.image(LOGO_PATH, x=55, y=50, w=100)
        
        self.ln(130)
        
        # Titel
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 34)
        self.multi_cell(0, 16, clean_text("Wertpapierplan\nSimulation Report"), align="C")
        
        # Trennlinie
        self.set_draw_color(*COLOR_ACCENT_GREEN)
        self.set_line_width(1)
        self.line(70, self.get_y() + 5, 140, self.get_y() + 5)
        
        self.ln(20)
        self.set_font("Helvetica", "", 14)
        self.set_text_color(*COLOR_ACCENT_GREEN)
        self.cell(0, 10, clean_text("Historische Simulation & Zukunftsprognose"), align="C", new_x="LMARGIN", new_y="NEXT")
        
        self.ln(45)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(180, 180, 180)
        now = datetime.now().strftime("%d.%m.%Y, %H:%M Uhr")
        self.cell(0, 10, f"Erstellt am: {now}", align="C", new_x="LMARGIN", new_y="NEXT")

    def create_portfolio_page(self, assets, params, handover_data=None):
        self.add_page()
        self.section_title("1. Portfolio & Eingaben")
        
        # --- ZENTRALISIERTES INFO-COCKPIT ---
        if handover_data:
            self.set_font("Helvetica", "", 11)
            self.set_text_color(0, 0, 0)
            
            # Daten vorbereiten
            client = handover_data.get('client', '-')
            advisor = handover_data.get('advisor', '-')
            budget_v = f"{handover_data.get('budget', 0):,.2f}"
            einmal_v = f"{handover_data.get('einmalerlag', 0):,.2f}"
            spar_v   = f"{handover_data.get('savings_rate', 0):,.2f}"
            portfolio_type = handover_data.get('portfolio_type') # FIX: Define variable
            
            # 2-Spalten Layout: Links Personen, Rechts Zahlen
            col_w = 90
            start_x = 15
            
            # Erste Zeile
            y_start = self.get_y()
            
            # Labels fett, Werte normal
            def print_key_val(label, value, x_offset):
                self.set_x(x_offset)
                self.set_font("Helvetica", "B", 10)
                self.set_text_color(*COLOR_DARK_GREEN)
                self.cell(40, 6, label, 0)
                self.set_font("Helvetica", "", 10)
                self.set_text_color(0, 0, 0)
                self.cell(50, 6, value, 0)

            # Block 1 (Links)
            print_key_val("Kunde:", clean_text(client), start_x)
            # Block 2 (Rechts)
            print_key_val("Budget:", f"EUR {budget_v}", start_x + col_w + 10)
            self.ln(6)
            
            # Zweite Zeile
            print_key_val("Berater:", clean_text(advisor), start_x)
            print_key_val("Einmalerlag:", f"EUR {einmal_v}", start_x + col_w + 10)
            self.ln(6)
            
            # Dritte Zeile
            print_key_val("Sparrate (Gesamt):", f"EUR {spar_v}", start_x + col_w + 10)
            print_key_val("Portfolio Typ:", clean_text(portfolio_type) if portfolio_type else "Manuell", start_x) # NEW V4
            self.ln(12)

        # Settings Block (Kompakter & Vertikal)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*COLOR_DARK_GREEN)
        # RENAMED HEADER
        self.cell(0, 8, "Kosten", new_x="LMARGIN", new_y="NEXT")
        
        self.set_font("Helvetica", "", 10)
        self.set_text_color(0, 0, 0)
        
        # Parameter UNTEREINANDER (Vertical List)
        # Filtern: Prognose-Horizont raus
        for k, v in params.items():
            if "Prognose-Horizont" in k:
                continue
            # Bullet point style
            self.cell(5, 6, "-", border=0) 
            self.cell(0, 6, f"{clean_text(k)}: {clean_text(v)}", border=0, new_x="LMARGIN", new_y="NEXT")
            
        self.ln(8)
        
        # Positionen Tabelle
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*COLOR_DARK_GREEN)
        self.cell(0, 10, "Portfolio Positionen", new_x="LMARGIN", new_y="NEXT")
        
        # Header
        self.set_fill_color(*COLOR_LIGHT_GREY)
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", "B", 9)
        
        # Breiten angepasst für Gewichtung
        cols = [60, 30, 25, 25, 25, 25] 
        headers = ["Name", "ISIN", "Gewichtung", "Start (EUR)", "Sparrate", "Intervall"]
        
        for i, h in enumerate(headers):
            # ZENTRIERT (außer Name)
            align = "C" if i > 0 else "L"
            self.cell(cols[i], 8, clean_text(h), border="B", fill=True, align=align)
        self.ln()
        
        # Body
        self.set_font("Helvetica", "", 9)
        for asset in assets:
            if not asset.get("ISIN / Ticker"): continue
            
            name = clean_text(asset.get("Name", ""))[:35]
            isin = clean_text(asset.get("ISIN / Ticker", ""))
            weight = f"{asset.get('Gewichtung (%)', 0):.1f} %"
            start = f"{asset.get('Einmalerlag (€)', 0):,.2f}"
            spar = f"{asset.get('Sparbetrag (€)', 0):,.2f}"
            inter = clean_text(asset.get("Spar-Intervall", ""))[:10]
            
            data = [name, isin, weight, start, spar, inter]
            # ZENTRIERT (außer Name)
            aligns = ["L", "C", "C", "C", "C", "C"]
            
            for i, d in enumerate(data):
                self.cell(cols[i], 8, d, border="B", align=aligns[i])
            self.ln()

    def create_returns_table(self, title, returns_data, suffix_label="(p.a.)"):
        """Erstellt eine Tabelle für Renditen (Historisch oder Prognose)"""
        if not returns_data:
            return
            
        self.ln(10)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*COLOR_DARK_GREEN)
        self.cell(0, 8, clean_text(title), new_x="LMARGIN", new_y="NEXT")
        
        # Einfache Tabelle - TIGHT LAYOUT (Schmäler)
        col_name_w = 90  # War 120
        col_val_w = 30   # War 40
        
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(*COLOR_LIGHT_GREY)
        self.cell(col_name_w, 7, "Asset / Position", border="B", fill=True)
        self.cell(col_val_w, 7, f"Rendite {suffix_label}", border="B", fill=True, align="R")
        self.ln()
        
        self.set_font("Helvetica", "", 9)
        self.set_text_color(0, 0, 0)
        
        for name, val in returns_data.items():
            val_str = f"{val:.2f} %"
            self.cell(col_name_w, 7, clean_text(name)[:60], border="B")
            self.cell(col_val_w, 7, val_str, border="B", align="R")
            self.ln()

    def create_chart_page(self, title, chart_bytes, kpi_dict, note=None, detailed_returns=None, detailed_returns_title="Rendite-Details", date_range=None):
        """Generische Seite für Historie & Prognose mit Chart und KPI-Tabelle"""
        self.add_page()
        self.section_title(title)
        
        # Chart
        if chart_bytes:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(chart_bytes)
                tmp_path = tmp.name
            try:
                self.image(tmp_path, x=10, w=190, h=95) # Fixierte Höhe für Layout-Konsistenz
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        else:
            self.set_text_color(200, 0, 0)
            self.cell(0, 10, "Chart nicht verfügbar.", new_x="LMARGIN", new_y="NEXT")
        
        self.ln(5)
        
        # 2-Spalten Layout: Links KPIs, Rechts Details (falls vorhanden)
        y_start = self.get_y()
        
        # KPI Tabelle (Grüne Linien Style)
        if kpi_dict:
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*COLOR_DARK_GREEN)
            
            # Titel je nach Kontext erraten oder fix setzen
            table_title = "Ergebnisse & Kennzahlen"
            self.cell(0, 8, table_title, new_x="LMARGIN", new_y="NEXT")
            
            # DATE RANGE SUBTITLE (falls vorhanden)
            if date_range:
                self.set_font("Helvetica", "I", 10)
                self.set_text_color(100, 100, 100)
                self.cell(0, 6, date_range, new_x="LMARGIN", new_y="NEXT")
                self.ln(2)
            
            self.set_draw_color(*COLOR_ACCENT_GREEN)
            self.set_line_width(0.4)
            
            for k, v in kpi_dict.items():
                self.set_font("Helvetica", "", 10)
                self.set_text_color(0, 0, 0) # Schwarz
                self.cell(100, 7, clean_text(k), border="B") # Label
                
                self.set_font("Helvetica", "B", 10)
                self.cell(0, 7, clean_text(v), border="B", align="R", new_x="LMARGIN", new_y="NEXT") # Wert
                
        # Wenn detaillierte Renditen im Argument sind, Tabelle anzeigen
        if detailed_returns:
            self.create_returns_table(detailed_returns_title, detailed_returns)
        
        if note:
            self.ln(10)
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
        
        # Größere Schrift (10pt statt 9pt)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*COLOR_TEXT_GREY)
        
        paragraphs = clean_text(DISCLAIMER_TEXT).split('\n\n')
        for p in paragraphs:
            self.multi_cell(0, 6, p) # Mehr Zeilenhöhe
            self.ln(6)


def generate_pdf_report(assets, global_params, hist_fig, hist_kpis, prog_fig, prog_kpis, handover_data=None, hist_returns=None, prog_returns=None, date_range_hist=None, date_range_prog=None):
    pdf = GutmannReport()
    
    # 1. Deckblatt & Portfolio
    pdf.create_title_page()
    pdf.create_portfolio_page(assets, global_params, handover_data)
    
    # 2. Historie
    hist_img = None
    if hist_fig:
        img_fig = hist_fig
        img_fig.update_layout(template="simple_white", plot_bgcolor="white", paper_bgcolor="white", font_color="black", showlegend=True)
        # Breiteres Bild für bessere Lesbarkeit im PDF
        hist_img = img_fig.to_image(format="png", width=1400, height=750, scale=2)
    
    pdf.create_chart_page("2. Historische Simulation", hist_img, hist_kpis, detailed_returns=hist_returns, detailed_returns_title="Historische Renditen (Positionen)", date_range=date_range_hist)
    
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

    prog_title = "3. Zukunftsprognose (Monte Carlo)"

    pdf.create_chart_page(
        prog_title, 
        prog_img, 
        prog_kpis, 
        note=prog_note, 
        detailed_returns=prog_returns,
        detailed_returns_title="Erwartete Renditen (Annahmen p.a.)",
        date_range=date_range_prog
    )
    
    # 4. Glossar (NEU)
    pdf.create_glossary_page()
    
    # 5. Rechtliches
    pdf.create_disclaimer_page()
    
    # --- PAGE COUNT POST-PROCESSING ---
    # Ersetze den Platzhalter {nb_true} mit der tatsächlichen Seitenanzahl minus 1 (Deckblatt)
    final_content_pages = pdf.page_no() - 1
    
    # pdf.output(dest='S') liefert in fpdf2/modernem fpdf meist bytes zurück
    output_bytes = pdf.output(dest='S')
    
    # Platzhalter auf Byte-Ebene ersetzen, um TypeError zu vermeiden
    placeholder = "{nb_true}".encode('latin-1')
    replacement = str(final_content_pages).encode('latin-1')
    
    if isinstance(output_bytes, str):
        # Fallback falls es doch ein String ist
        output_bytes = output_bytes.replace("{nb_true}", str(final_content_pages)).encode('latin-1')
    else:
        output_bytes = output_bytes.replace(placeholder, replacement)
    
    return output_bytes


# --- NEUE HELPER FUNKTIONEN (Refactoring für Tab_Simulation) ---

def build_history_kpis(simulations_daten: pd.DataFrame) -> dict:
    """Erstellt KPI-Dictionary für historische Simulation."""
    if simulations_daten is None:
        return {}
    
    last_row = simulations_daten.iloc[-1]
    total_invest = last_row['Einzahlungen (brutto)']
    end_val = last_row['Portfolio (nominal)']
    profit = end_val - total_invest
    rendite_abs = (profit / total_invest * 100) if total_invest > 0 else 0
    
    return {
        "Gesamteinzahlung": f"EUR {total_invest:,.2f}",
        "Endkapital (nominal)": f"EUR {end_val:,.2f}",
        "Gewinn/Verlust": f"EUR {profit:,.2f}",
        "Rendite (absolut)": f"{rendite_abs:.2f} %",
        "Endkapital (real)": f"EUR {last_row['Portfolio (real)']:,.2f}"
    }

def build_prognose_kpis(prognose_daten: pd.DataFrame) -> dict:
    """Erstellt KPI-Dictionary für Zukunftsprognose."""
    if prognose_daten is None:
        return {}
    
    last_row_p = prognose_daten.iloc[-1]
    start_cap = prognose_daten.iloc[0]['Einzahlungen (brutto)']
    end_median = last_row_p['Portfolio (Median)']
    rendite_prog = ((end_median / last_row_p['Einzahlungen (brutto)']) - 1) * 100
    
    return {
        "Startkapital (Ist-Stand)": f"EUR {start_cap:,.2f}",
        "Geplante Sparraten (Summe)": f"EUR {(last_row_p['Einzahlungen (brutto)'] - start_cap):,.2f}",
        "Endkapital (Median, nominal)": f"EUR {end_median:,.2f}",
        "Rendite Erwartungswert": f"{rendite_prog:.2f} %",
        "Endkapital (Real, Median)": f"EUR {last_row_p['Portfolio (Real_Median)']:,.2f}",
        "Endkapital (Optimistisch)": f"EUR {last_row_p.get('Portfolio (BestCase)', 0):,.2f}",
        "Endkapital (Pessimistisch)": f"EUR {last_row_p.get('Portfolio (WorstCase)', 0):,.2f}"
    }

def build_global_params(prognose_jahre: int, cost_ausgabe: float, 
                        cost_management: float, cost_depot: float) -> dict:
    """Erstellt globales Parameter-Dictionary für PDF."""
    return {
        "Prognose-Horizont": f"{prognose_jahre} Jahre",
        "Ausgabeaufschlag": f"{cost_ausgabe} %",
        "Managementgebühr": f"{cost_management} % p.a.",
        "Depotgebühr": f"{cost_depot} EUR p.a."
    }

def create_pdf_with_charts(
    assets: list,
    simulations_daten,
    prognose_daten,
    handover_data: dict,
    historical_returns_pa: dict,
    prognosis_assumptions_pa: dict,
    sim_start_date,
    sim_end_date,
    prognose_jahre: int,
    cost_ausgabe: float,
    cost_management: float,
    cost_depot: float,
    editable_budget: float,
    editable_einmalerlag: float,
    editable_sparrate: float,
    plotting_module  # Übergeben um Circular Import zu vermeiden
) -> bytes | None:
    """
    Erstellt kompletten PDF-Report mit Charts.
    Gibt PDF als Bytes zurück oder None bei Fehler.
    """
    from datetime import date
    
    # Gewichtungs-Validierung
    total_w = sum(a.get("Gewichtung (%)", 0) for a in assets)
    if abs(total_w - 100) > 0.1:
        return None  # Ungültige Gewichtung
    
    # Datums-Bereiche formatieren
    range_hist_str = f"Zeitraum: {sim_start_date.strftime('%d.%m.%Y')} - {sim_end_date.strftime('%d.%m.%Y')}"
    
    today = date.today()
    end_prog = today.replace(year=today.year + prognose_jahre)
    range_prog_str = f"Zeitraum: {today.strftime('%d.%m.%Y')} - {end_prog.strftime('%d.%m.%Y')}"
    
    # Charts erstellen
    fig_hist = plotting_module.create_simulation_chart(
        simulations_daten, None, 
        title="Historische Entwicklung",
        show_crisis_events=False
    )
    
    fig_prog = None
    if prognose_daten is not None:
        fig_prog = plotting_module.create_simulation_chart(
            None, prognose_daten,
            title="Zukunftsprognose"
        )
    
    # KPIs bauen
    hist_kpis = build_history_kpis(simulations_daten)
    prog_kpis = build_prognose_kpis(prognose_daten)
    global_params = build_global_params(prognose_jahre, cost_ausgabe, cost_management, cost_depot)
    
    # Handover-Data mit editierten Werten
    updated_handover = dict(handover_data) if handover_data else {}
    updated_handover['budget'] = editable_budget
    updated_handover['einmalerlag'] = editable_einmalerlag
    updated_handover['savings_rate'] = editable_sparrate
    
    # PDF generieren
    return generate_pdf_report(
        assets=assets,
        global_params=global_params,
        hist_fig=fig_hist,
        hist_kpis=hist_kpis,
        prog_fig=fig_prog,
        prog_kpis=prog_kpis,
        handover_data=updated_handover,
        hist_returns=historical_returns_pa,
        prog_returns=prognosis_assumptions_pa,
        date_range_hist=range_hist_str,
        date_range_prog=range_prog_str
    )