from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime

def export_schedule_to_pdf(dates, schedule_grid, file_path):
    """
    Exports the given grid-based schedule data to a PDF file.
    """
    try:
        doc = SimpleDocTemplate(file_path, pagesize=(11*inch, 8.5*inch)) # Landscape
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle('Title', parent=styles['h1'], alignment=TA_CENTER, spaceAfter=14)
        week_title_style = ParagraphStyle('WeekTitle', parent=styles['h2'], spaceBefore=12, spaceAfter=6)

        # Main Title
        month_name = dates[0].strftime('%B %Y').capitalize()
        story.append(Paragraph(f"Horario de Asignaciones - {month_name}", title_style))

        for week_idx, weekly_data in enumerate(schedule_grid):
            # Week Title
            week_title = dates[week_idx].strftime("Semana del %d de %B de %Y")
            story.append(Paragraph(week_title, week_title_style))

            # Prepare data for the table
            table_data = []
            for row in weekly_data:
                # Use Paragraphs for word wrapping in cells
                p_col1 = Paragraph(str(row[0]), styles['BodyText'])
                p_col2 = Paragraph(str(row[1]), styles['BodyText'])
                table_data.append([p_col1, p_col2])

            if not table_data:
                continue

            # Create and style the table for the week
            table = Table(table_data, colWidths=[4.5 * inch, 4.5 * inch])
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ]))

            story.append(table)
            story.append(Spacer(1, 0.2 * inch))

        doc.build(story)
        return True
    except Exception as e:
        print(f"Error al generar PDF: {e}")
        return False
