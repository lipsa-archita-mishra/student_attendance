import csv
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime

# ReportLab imports for professional PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from utils.logger import logger

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and draw total page count
    along with running header/footer.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#7F8C8D"))
        
        # Header
        self.drawString(54, 750, "Attendance Management System - Reports Service")
        self.setStrokeColor(colors.HexColor("#BDC3C7"))
        self.setLineWidth(0.5)
        self.line(54, 742, letter[0] - 54, 742)
        
        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 36, page_text)
        self.drawString(54, 36, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.line(54, 48, letter[0] - 54, 48)
        
        self.restoreState()

def export_to_csv(data: List[Dict[str, Any]], filepath: Path) -> bool:
    """Exports a list of flat dictionaries to a CSV file."""
    if not data:
        logger.warning("No data provided to export_to_csv.")
        return False
    try:
        keys = data[0].keys()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        return True
    except Exception as e:
        logger.error(f"Failed to export CSV: {e}")
        return False

def export_to_excel(data: List[Dict[str, Any]], filepath: Path) -> bool:
    """Exports a list of flat dictionaries to an Excel file using pandas."""
    if not data:
        logger.warning("No data provided to export_to_excel.")
        return False
    try:
        df = pd.DataFrame(data)
        # Use openpyxl engine
        df.to_excel(filepath, index=False, engine="openpyxl")
        return True
    except Exception as e:
        logger.error(f"Failed to export Excel: {e}")
        return False

def export_to_pdf(
    title: str,
    headers: List[str],
    data: List[List[Any]],
    filepath: Path,
    subtitle: str = ""
) -> bool:
    """
    Generates a highly styled, corporate PDF report.
    - headers: Column names
    - data: 2D array matching the columns in headers
    - filepath: Where to save the output PDF
    """
    try:
        # Create doc template (54pt = 0.75in margins)
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=72,
            bottomMargin=72
        )
        
        styles = getSampleStyleSheet()
        
        # Define Custom Styles
        title_style = ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#2C3E50"),
            alignment=0, # Left-aligned
            spaceAfter=6
        )
        
        subtitle_style = ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#7F8C8D"),
            spaceAfter=20
        )
        
        cell_style = ParagraphStyle(
            name="TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#34495E")
        )
        
        header_style = ParagraphStyle(
            name="TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.white
        )

        elements = []
        
        # Document Title and Subtitle
        elements.append(Paragraph(title, title_style))
        if subtitle:
            elements.append(Paragraph(subtitle, subtitle_style))
        elements.append(Spacer(1, 10))

        # Format Table Data (wrap inside Paragraph flowables to support auto-wrapping)
        table_data = []
        
        # Header Row
        header_row = [Paragraph(h, header_style) for h in headers]
        table_data.append(header_row)
        
        # Value Rows
        for row in data:
            row_cells = []
            for cell in row:
                cell_text = str(cell) if cell is not None else ""
                row_cells.append(Paragraph(cell_text, cell_style))
            table_data.append(row_cells)

        # Compute optimal column widths based on 504 pt available (612 page width - 108 margins)
        num_cols = len(headers)
        col_width = 504.0 / num_cols if num_cols > 0 else 504.0
        col_widths = [col_width] * num_cols

        # Table instantiation
        report_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Table Styling
        t_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2C3E50")), # Primary header color
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ])
        
        # Alternate row background coloring
        for i in range(1, len(data) + 1):
            if i % 2 == 0:
                t_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor("#F8FAFC"))
                
        report_table.setStyle(t_style)
        elements.append(report_table)

        # Build Document
        doc.build(elements, canvasmaker=NumberedCanvas)
        return True
    except Exception as e:
        logger.error(f"Failed to generate PDF report: {e}")
        return False
