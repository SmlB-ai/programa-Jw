import sys
import calendar
from functools import partial
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QScrollArea, QFrame, QMessageBox, QDialog, QDialogButtonBox,
    QFileDialog
)
from PyQt6.QtCore import QDate, Qt
from .assignment_algorithm import generate_schedule
from .database.database_manager import save_schedule_to_history, get_people_for_role
from .pdf_exporter import export_schedule_to_pdf

# ManualOverrideDialog se mantiene igual por ahora, pero podría necesitar ajustes

class ScheduleViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_schedule_data = None # Para la plantilla llena
        self.current_schedule_dates = None # Para las fechas

        self.main_layout = QVBoxLayout(self)

        # --- Controles (sin cambios) ---
        controls_layout = QHBoxLayout()
        self.month_combo = QComboBox()
        self.year_spinbox = QSpinBox()
        self.generate_button = QPushButton("Generar Horario")
        self.save_button = QPushButton("Guardar en Historial")
        self.export_button = QPushButton("Exportar a PDF")
        self.save_button.setEnabled(False)
        self.export_button.setEnabled(False)
        current_date = QDate.currentDate()
        months_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.month_combo.addItems(months_es)
        self.month_combo.setCurrentIndex(current_date.month() - 1)
        self.year_spinbox.setRange(2020, 2050)
        self.year_spinbox.setValue(current_date.year())
        controls_layout.addWidget(QLabel("Mes:"))
        controls_layout.addWidget(self.month_combo)
        controls_layout.addWidget(QLabel("Año:"))
        controls_layout.addWidget(self.year_spinbox)
        controls_layout.addWidget(self.generate_button)
        controls_layout.addWidget(self.save_button)
        controls_layout.addWidget(self.export_button)
        self.main_layout.addLayout(controls_layout)

        # --- Área de Scroll para el nuevo Grid ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.schedule_container = QWidget()
        # El layout del container será un grid
        self.schedule_grid_layout = QGridLayout(self.schedule_container)
        self.scroll_area.setWidget(self.schedule_container)
        self.main_layout.addWidget(self.scroll_area)

        # --- Conexiones ---
        self.generate_button.clicked.connect(self.run_schedule_generation)
        # self.save_button.clicked.connect(self.save_schedule) # Deshabilitado por ahora
        self.export_button.clicked.connect(self.export_to_pdf)

    def export_to_pdf(self):
        if not self.current_schedule_data:
            QMessageBox.warning(self, "Sin Horario", "Primero debes generar un horario para poder exportarlo.")
            return

        first_date_str = self.current_schedule_dates[0].strftime('%Y-%m')
        default_filename = f"horario_{first_date_str}.pdf"

        filePath, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", default_filename, "PDF Files (*.pdf)")

        if filePath:
            success = export_schedule_to_pdf(self.current_schedule_dates, self.current_schedule_data, filePath)
            if success:
                QMessageBox.information(self, "Éxito", f"El horario ha sido exportado a:\n{filePath}")
            else:
                QMessageBox.critical(self, "Error", "Ocurrió un error al generar el archivo PDF.")

    def run_schedule_generation(self):
        month = self.month_combo.currentIndex() + 1
        year = self.year_spinbox.value()

        self.current_schedule_dates, self.current_schedule_data = generate_schedule(year, month)

        self.display_schedule()
        self.save_button.setEnabled(True)
        self.export_button.setEnabled(True)

    def display_schedule(self):
        # Limpiar grid anterior
        while self.schedule_grid_layout.count():
            child = self.schedule_grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.current_schedule_data:
            self.schedule_grid_layout.addWidget(QLabel("No se generó ningún horario."))
            return

        # Poblar el grid con la nueva estructura
        row_offset = 0
        for week_idx, weekly_data in enumerate(self.current_schedule_data):
            # Añadir título de la semana
            week_title = self.current_schedule_dates[week_idx].strftime("Semana del %d de %B de %Y")
            title_label = QLabel(f"<b>{week_title}</b>")
            self.schedule_grid_layout.addWidget(title_label, row_offset, 0, 1, 4) # Span 4 columns
            row_offset += 1

            for row_data in weekly_data:
                # Columna 1
                col1_label = QLabel(str(row_data[0]))
                col1_label.setWordWrap(True)
                self.schedule_grid_layout.addWidget(col1_label, row_offset, 0, 1, 2) # Span 2 columns

                # Columna 2
                col2_label = QLabel(str(row_data[1]))
                col2_label.setWordWrap(True)
                self.schedule_grid_layout.addWidget(col2_label, row_offset, 2, 1, 2) # Span 2 columns

                row_offset += 1

            # Añadir separador entre semanas
            if week_idx < len(self.current_schedule_data) - 1:
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.HLine)
                separator.setFrameShadow(QFrame.Shape.Sunken)
                self.schedule_grid_layout.addWidget(separator, row_offset, 0, 1, 4)
                row_offset += 1

    # Las funciones de guardar, exportar y anulación manual necesitan ser adaptadas
    # a la nueva estructura de datos `self.current_schedule_data`
    # Por ahora, se dejan deshabilitadas o con funcionalidad parcial.
