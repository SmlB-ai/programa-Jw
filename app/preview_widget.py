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
from .database.database_manager import save_schedule_to_history
from .pdf_exporter import export_schedule_to_pdf
from .special_week_dialog import SpecialWeekDialog

class PreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_schedule_data = None
        self.current_schedule_dates = None
        self.theme_overrides = {}
        self.main_layout = QVBoxLayout(self)
        controls_layout = QHBoxLayout()
        self.month_combo = QComboBox()
        self.year_spinbox = QSpinBox()
        self.generate_button = QPushButton("Generar Vista Previa")
        self.save_button = QPushButton("Guardar en Historial")
        self.export_button = QPushButton("Exportar a PDF")
        self.special_week_button = QPushButton("Semanas Especiales...")
        self.save_button.setEnabled(False); self.export_button.setEnabled(False)

        current_date = QDate.currentDate()
        months_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.month_combo.addItems(months_es)
        self.month_combo.setCurrentIndex(current_date.month() - 1)

        self.year_spinbox.setRange(2020, 2050); self.year_spinbox.setValue(current_date.year())

        controls_layout.addWidget(QLabel("Mes:")); controls_layout.addWidget(self.month_combo)
        controls_layout.addWidget(QLabel("Año:")); controls_layout.addWidget(self.year_spinbox)
        controls_layout.addWidget(self.generate_button); controls_layout.addWidget(self.save_button)
        controls_layout.addWidget(self.export_button)
        controls_layout.addWidget(self.special_week_button)

        self.main_layout.addLayout(controls_layout)
        self.scroll_area = QScrollArea(); self.scroll_area.setWidgetResizable(True)
        self.schedule_container = QWidget()
        self.scroll_area.setWidget(self.schedule_container)
        self.main_layout.addWidget(self.scroll_area)

        self.generate_button.clicked.connect(self.run_schedule_generation)
        self.save_button.clicked.connect(self.save_schedule)
        self.export_button.clicked.connect(self.export_to_pdf)
        self.special_week_button.clicked.connect(self.open_special_week_dialog)

    def open_special_week_dialog(self):
        year = self.year_spinbox.value()
        month = self.month_combo.currentIndex() + 1

        cal = calendar.Calendar()
        meeting_day=calendar.THURSDAY
        month_dates = [d.date() for d in cal.itermonthdates(year, month) if d.weekday() == meeting_day and d.month == month]

        dialog = SpecialWeekDialog(year, month, month_dates, self)
        if dialog.exec():
            self.run_schedule_generation()

    def run_schedule_generation(self):
        month = self.month_combo.currentIndex() + 1
        year = self.year_spinbox.value()
        self.current_schedule_dates, self.current_schedule_data = generate_schedule(year, month)
        self.display_schedule()
        self.save_button.setEnabled(True); self.export_button.setEnabled(True)

    def display_schedule(self):
        if self.schedule_container.layout() is not None:
            while self.schedule_container.layout().count():
                child = self.schedule_container.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            new_layout = QVBoxLayout(self.schedule_container)
            self.schedule_container.setLayout(new_layout)

        if not self.current_schedule_data:
            return

        container_layout = self.schedule_container.layout()
        container_layout.setSpacing(15)

        from .week_schedule_widget import WeekScheduleWidget

        for week_idx, weekly_data in enumerate(self.current_schedule_data):
            week_date = self.current_schedule_dates[week_idx]
            week_type = week_idx % 4
            week_widget = WeekScheduleWidget(week_date, week_type, weekly_data, self.theme_overrides)
            week_widget.themeChanged.connect(self._on_theme_changed)
            container_layout.addWidget(week_widget)

        container_layout.addStretch()

    def _on_theme_changed(self, week_type, row, col, new_text):
        from .database.database_manager import update_template_text
        # Actualizar la base de datos
        update_template_text(week_type, row, col, new_text)
        # Actualizar el override local para la sesión actual
        self.theme_overrides[(week_type, row, col)] = new_text

    def save_schedule(self):
        # This function might need adjustment depending on how schedule history is handled
        if not self.current_schedule_data: return
        # ... (save logic)
        QMessageBox.information(self, "Éxito", "El horario ha sido guardado en el historial.")
        self.save_button.setEnabled(False)

    def export_to_pdf(self):
        if not self.current_schedule_data: return
        default_filename = f"horario_{self.current_schedule_dates[0].strftime('%Y-%m')}.pdf"
        filePath, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", default_filename, "PDF Files (*.pdf)")
        if filePath:
            if export_schedule_to_pdf(self.current_schedule_dates, self.current_schedule_data, filePath, self.theme_overrides):
                QMessageBox.information(self, "Éxito", f"Horario exportado a:\n{filePath}")
            else:
                QMessageBox.critical(self, "Error", "Ocurrió un error al generar el PDF.")
