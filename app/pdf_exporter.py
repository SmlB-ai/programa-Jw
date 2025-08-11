from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime

def export_schedule_to_pdf(schedule_data, file_path):
    """
    Exports the given schedule data to a PDF file.
    """
    try:
        doc = SimpleDocTemplate(file_path)
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['h1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            spaceAfter=14,
            alignment=TA_CENTER
        )
        week_title_style = ParagraphStyle(
            'WeekTitle',
            parent=styles['h2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            spaceBefore=20,
            spaceAfter=10
        )

        # Main Title
        first_date_str = sorted(schedule_data.keys())[0]
        month_name = datetime.strptime(first_date_str, '%Y-%m-%d').strftime('%B %Y').capitalize()
        story.append(Paragraph(f"Horario de Asignaciones - {month_name}", title_style))

        # Sort dates to ensure chronological order
        sorted_dates = sorted(schedule_data.keys())

        for date_str in sorted_dates:
            # Week Title
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            week_title = date_obj.strftime("Semana del %d de %B de %Y").replace(date_obj.strftime("%B"), date_obj.strftime("%B").capitalize())
            story.append(Paragraph(week_title, week_title_style))

            weekly_assignments = schedule_data[date_str]

            # Prepare data for the table
            table_data = []
            for slot, person in weekly_assignments.items():
                # Make slot names more readable
                clean_slot = slot.replace('_', ' ').replace(':', ': ')
                # Use Paragraphs for word wrapping
                p_slot = Paragraph(clean_slot, styles['BodyText'])
                p_person = Paragraph(str(person), styles['BodyText'])
                table_data.append([p_slot, p_person])

            if not table_data:
                continue

            # Create and style the table
            table = Table(table_data, colWidths=[2.5 * inch, 2.5 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            story.append(table)
            story.append(Spacer(1, 0.2 * inch))

        doc.build(story)
        return True
    except Exception as e:
        print(f"Error al generar PDF: {e}")
        return False
