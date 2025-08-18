import sys
import calendar
from functools import partial
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QScrollArea, QFrame, QMessageBox, QDialog, QDialogButtonBox,
    QFileDialog
)
from PyQt6.QtCore import QDate, Qt
from .assignment_algorithm import generate_schedule, USER_TEMPLATE_STRUCTURE
from .database.database_manager import save_schedule_to_history
from .special_week_dialog import SpecialWeekDialog

# Nota: El ManualOverrideDialog se ha quitado de este widget por ahora
# para devolverlo a un estado más simple.

class ScheduleViewerWidget(QWidget):
    """
    Este widget muestra el horario en una tabla simple de datos.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_schedule_data = None
        self.current_schedule_dates = None
        self.main_layout = QVBoxLayout(self)

        # --- Controles ---
        controls_layout = QHBoxLayout()
        self.month_combo = QComboBox()
        self.year_spinbox = QSpinBox()
        self.generate_button = QPushButton("Generar Horario (Datos)")
        self.special_week_button = QPushButton("Semanas Especiales...")

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
        controls_layout.addWidget(self.special_week_button)
        self.main_layout.addLayout(controls_layout)

        # --- Área de Scroll para la Tabla ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.schedule_container = QWidget()
        self.grid_layout = QGridLayout(self.schedule_container)
        self.scroll_area.setWidget(self.schedule_container)
        self.main_layout.addWidget(self.scroll_area)

        # --- Conexiones ---
        self.generate_button.clicked.connect(self.run_schedule_generation)
        self.special_week_button.clicked.connect(self.open_special_week_dialog)

    def open_special_week_dialog(self):
        year = self.year_spinbox.value()
        month = self.month_combo.currentIndex() + 1
        cal = calendar.Calendar()
        meeting_day = calendar.THURSDAY
        month_dates = [d.date() for d in cal.itermonthdates(year, month) if d.weekday() == meeting_day and d.month == month]
        dialog = SpecialWeekDialog(year, month, month_dates, self)
        if dialog.exec():
            self.run_schedule_generation()

    def run_schedule_generation(self):
        # Limpiar la vista anterior
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        month = self.month_combo.currentIndex() + 1
        year = self.year_spinbox.value()
        self.current_schedule_dates, self.current_schedule_data = generate_schedule(year, month)
        self.display_schedule_grid()

    def display_schedule_grid(self):
        if not self.current_schedule_data:
            return

        row_offset = 0
        for week_idx, weekly_data in enumerate(self.current_schedule_data):
            week_date = self.current_schedule_dates[week_idx]

            # Título de la semana
            week_title = week_date.strftime("Semana del %d de %B de %Y")
            self.grid_layout.addWidget(QLabel(f"<b>{week_title}</b>"), row_offset, 0, 1, 2)
            row_offset += 1

            # Manejar semanas especiales
            if isinstance(weekly_data, dict) and weekly_data.get('is_special'):
                reason = weekly_data.get('reason', 'Sin motivo')
                label = QLabel(f"<i>{reason}</i>")
                label.setStyleSheet("color: red;")
                self.grid_layout.addWidget(label, row_offset, 0, 1, 2)
                row_offset += 1
                continue

            # Mostrar datos de la semana en la tabla
            for row_data in weekly_data:
                # La tupla puede tener 2 o más elementos, nos interesan los dos primeros
                col1_text = str(row_data[0]) if len(row_data) > 0 else ""
                col2_text = str(row_data[1]) if len(row_data) > 1 else ""
                self.grid_layout.addWidget(QLabel(col1_text), row_offset, 0)
                self.grid_layout.addWidget(QLabel(col2_text), row_offset, 1)
                row_offset += 1

            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            self.grid_layout.addWidget(separator, row_offset, 0, 1, 2)
            row_offset += 1
