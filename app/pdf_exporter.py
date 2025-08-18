from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

def export_schedule_to_pdf(dates, schedule_grid, file_path, theme_overrides={}):
    """
    Exports the schedule to a PDF file with a layout that mimics Programa.png.
    """
    try:
        doc = SimpleDocTemplate(file_path, pagesize=(11*inch, 8.5*inch), topMargin=0.5*inch, bottomMargin=0.5*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()

        # --- Custom Paragraph Styles ---
        styles.add(ParagraphStyle(name='WeekHeader', fontSize=14, fontName='Helvetica-Bold', alignment=TA_LEFT, leading=16))
        styles.add(ParagraphStyle(name='President', fontSize=11, fontName='Helvetica-Bold', alignment=TA_RIGHT))
        styles.add(ParagraphStyle(name='SectionHeader', fontSize=11, fontName='Helvetica-Bold', alignment=TA_CENTER, textColor=colors.white))
        styles.add(ParagraphStyle(name='AssignmentTitle', fontSize=9, fontName='Helvetica-Bold', leading=10))
        styles.add(ParagraphStyle(name='AssignmentName', fontSize=9, fontName='Helvetica', leading=10))
        styles.add(ParagraphStyle(name='AssignmentTheme', fontSize=9, fontName='Helvetica-Oblique', leading=10))

        for week_idx, weekly_data in enumerate(schedule_grid):
            week_date = dates[week_idx]

            # --- Handle Special Weeks ---
            if isinstance(weekly_data, dict) and weekly_data.get('is_special'):
                try:
                    start_date_str = week_date.strftime("%-d").lstrip("0")
                except ValueError:
                    start_date_str = week_date.strftime("%#d").lstrip("0")
                end_date_str = week_date.addDays(6).strftime("%B %Y")
                week_range_str = f"{start_date_str} - {week_date.addDays(6).day} de {end_date_str}"

                story.append(Paragraph(week_range_str, styles['WeekHeader']))
                reason = weekly_data.get('reason', 'Sin motivo especificado')
                story.append(Paragraph(reason, styles['AssignmentTheme']))
                story.append(Spacer(1, 0.25 * inch))
                continue

            # --- Prepare data for the table ---
            # This mapping needs to be identical to the one in WeekScheduleWidget
            table_data = [
                # Row 0: Header
                ['', '', '', '', '', '', '', ''],
                # Row 1: Oracion Inicio
                ['', '', '', '', '', '', '', ''],
                # Row 2: Separator
                ['', '', '', '', '', '', '', ''],
                # Row 3-6: Tesoros
                ['', '', '', '', '', '', '', ''],
                ['', '', '', '', '', '', '', ''],
                ['', '', '', '', '', '', '', ''],
                ['', '', '', '', '', '', '', ''],
                # Row 7: Section Headers
                ['', '', '', '', '', '', '', ''],
                # Row 8-10: Maestros y Vida
                ['', '', '', '', '', '', '', ''],
                ['', '', '', '', '', '', '', ''],
                ['', '', '', '', '', '', '', ''],
                # Row 11: Acomodadores
                ['', '', '', '', '', '', '', ''],
            ]

            # --- Map data to table_data ---
            # This mapping is brittle and depends on the fixed structure of week_data

            # Header
            try:
                start_date_str = week_date.strftime("%-d").lstrip("0")
            except ValueError: # Fallback for Windows
                start_date_str = week_date.strftime("%#d").lstrip("0")
            end_date_str = week_date.addDays(6).strftime("%B %Y")
            week_range_str = f"{start_date_str} - {week_date.addDays(6).day} de {end_date_str}"

            table_data[0][0] = Paragraph(week_range_str, styles['WeekHeader'])
            table_data[0][5] = Paragraph(f"<b>Presidente:</b> {weekly_data[0][1]}", styles['President'])

            # Oración
            table_data[1][0] = Paragraph(f"<b>Oración de inicio:</b> {weekly_data[1][0]}", styles['AssignmentName'])

            # Tesoros
            table_data[3][0] = Paragraph("TESOROS DE LA BIBLIA", styles['SectionHeader'])
            original_theme_tesoros = weekly_data[3][0]
            display_theme_tesoros = theme_overrides.get(original_theme_tesoros, original_theme_tesoros)
            table_data[4][1] = Paragraph(display_theme_tesoros, styles['AssignmentTheme'])
            table_data[5][1] = Paragraph(f"<b>Busquemos perlas escondidas:</b> {weekly_data[4][1]}", styles['AssignmentName'])
            table_data[6][1] = Paragraph(f"<b>Lectura de la Biblia:</b> {weekly_data[6][1]}", styles['AssignmentName'])

            # Sala B
            table_data[3][5] = Paragraph(f"<b>Lectura de la Biblia (Sala B)</b><br/>{weekly_data[1][1]}", styles['AssignmentName'])
            table_data[4][5] = Paragraph(f"<b>{weekly_data[3][1]}:</b><br/>{weekly_data[4][1]}", styles['AssignmentName'])
            table_data[5][5] = Paragraph(f"<b>{weekly_data[5][1]}:</b><br/>{weekly_data[6][1]}", styles['AssignmentName'])
            table_data[6][5] = Paragraph(f"<b>{weekly_data[7][1]}:</b><br/>{weekly_data[8][1]}", styles['AssignmentName'])

            # Maestros y Vida
            table_data[7][0] = Paragraph("SEAMOS MEJORES MAESTROS", styles['SectionHeader'])
            table_data[7][4] = Paragraph("NUESTRA VIDA CRISTIANA", styles['SectionHeader'])

            # Maestros Content
            for i, row_idx in enumerate(range(10, 16, 2)):
                title = weekly_data[row_idx][0]
                names = weekly_data[row_idx + 1][0] if (row_idx + 1) < len(weekly_data) else ""
                if not title or not names: continue
                table_data[8+i][1] = Paragraph(f"<b>{title}:</b><br/>{names}", styles['AssignmentName'])

            # Vida Content
            original_vida_1_title = weekly_data[10][1]
            display_vida_1_title = theme_overrides.get(original_vida_1_title, original_vida_1_title)
            table_data[8][5] = Paragraph(f"<b>{display_vida_1_title}:</b><br/>{weekly_data[11][1]}", styles['AssignmentName'])
            table_data[9][5] = Paragraph(f"<b>{weekly_data[13][1]}:</b><br/>{weekly_data[14][1]}", styles['AssignmentName'])
            table_data[10][5] = Paragraph(f"<b>Oración de final:</b> {weekly_data[15][1]}", styles['AssignmentName'])

            # Acomodadores
            table_data[11][0] = Paragraph(f"<b>Acomodadores de entrada:</b> {weekly_data[17][0]}", styles['AssignmentName'])
            table_data[11][4] = Paragraph(f"<b>Acomodadores de auditorio:</b> {weekly_data[17][1]}", styles['AssignmentName'])

            # --- Table Style ---
            style = TableStyle([
                # Alignment
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

                # Header Row
                ('SPAN', (0, 0), (4, 0)), # Date
                ('SPAN', (5, 0), (7, 0)), # President

                # Oracion Inicio
                ('SPAN', (0, 1), (3, 1)),

                # Separator Line
                ('LINEBELOW', (0, 1), (7, 1), 1, colors.black),
                ('BOTTOMPADDING', (0, 1), (7, 1), 8),

                # Tesoros Section
                ('SPAN', (0, 3), (3, 3)), # Header
                ('BACKGROUND', (0, 3), (3, 3), '#00796b'),
                ('SPAN', (1, 4), (3, 4)), # Theme
                ('SPAN', (1, 5), (3, 5)), # Perlas
                ('SPAN', (1, 6), (3, 6)), # Lectura

                # Sala B Section
                ('SPAN', (5, 3), (7, 3)), # Lectura B
                ('SPAN', (5, 4), (7, 4)), # Asig B 1
                ('SPAN', (5, 5), (7, 5)), # Asig B 2
                ('SPAN', (5, 6), (7, 6)), # Asig B 3

                # Maestros Section
                ('SPAN', (0, 7), (3, 7)), # Header
                ('BACKGROUND', (0, 7), (3, 7), '#c62828'),

                # Vida Cristiana Section
                ('SPAN', (4, 7), (7, 7)), # Header
                ('BACKGROUND', (4, 7), (7, 7), '#6a1b9a'),

                # Maestros Content
                ('SPAN', (1, 8), (3, 8)),
                ('SPAN', (1, 9), (3, 9)),
                ('SPAN', (1, 10), (3, 10)),

                # Vida Content
                ('SPAN', (5, 8), (7, 8)),
                ('SPAN', (5, 9), (7, 9)),
                ('SPAN', (5, 10), (7, 10)), # Oracion Final

                # Acomodadores
                ('SPAN', (0, 11), (3, 11)),
                ('SPAN', (4, 11), (7, 11)),
                ('TOPPADDING', (0, 11), (7, 11), 8),
                ('LINEABOVE', (0, 11), (7, 11), 0.5, colors.grey),

                # Grid for debugging
                # ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
            ])

            # Create table
            col_widths = [1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch]
            # A more dynamic width calculation
            total_width = doc.width
            num_cols = 8
            col_widths = [total_width / num_cols] * num_cols

            table = Table(table_data, colWidths=col_widths)
            table.setStyle(style)

            story.append(table)
            story.append(Spacer(1, 0.25 * inch))

        doc.build(story)
        return True
    except Exception as e:
        print(f"Error al generar PDF: {e}")
        return False
