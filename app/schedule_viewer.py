import sys
import calendar
from functools import partial
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QScrollArea, QFrame, QMessageBox, QDialog, QDialogButtonBox,
    QFileDialog
)
from PyQt6.QtCore import QDate, Qt
from .assignment_algorithm import generate_schedule, USER_TEMPLATE_STRUCTURE, _get_metadata_for_slot
from .database.database_manager import save_schedule_to_history, get_people_for_role
from .pdf_exporter import export_schedule_to_pdf

class ManualOverrideDialog(QDialog):
    def __init__(self, current_person, candidates, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cambio Manual")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Asignación actual: {current_person}"))
        layout.addWidget(QLabel("Seleccionar nuevo asignado:"))
        self.combo = QComboBox()
        for candidate in candidates: self.combo.addItem(candidate['nombre'], userData=candidate['id'])
        layout.addWidget(self.combo)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept); self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
    def get_selected_person(self): return self.combo.currentText()

class ScheduleViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_schedule_data = None
        self.current_schedule_dates = None
        self.main_layout = QVBoxLayout(self)
        controls_layout = QHBoxLayout()
        self.month_combo = QComboBox()
        self.year_spinbox = QSpinBox()
        self.generate_button = QPushButton("Generar Horario")
        self.save_button = QPushButton("Guardar en Historial")
        self.export_button = QPushButton("Exportar a PDF")
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
        self.main_layout.addLayout(controls_layout)
        self.scroll_area = QScrollArea(); self.scroll_area.setWidgetResizable(True)
        self.schedule_container = QWidget()
        self.schedule_grid_layout = QGridLayout(self.schedule_container)
        self.scroll_area.setWidget(self.schedule_container)
        self.main_layout.addWidget(self.scroll_area)
        self.generate_button.clicked.connect(self.run_schedule_generation)
        self.save_button.clicked.connect(self.save_schedule)
        self.export_button.clicked.connect(self.export_to_pdf)

    def run_schedule_generation(self):
        month = self.month_combo.currentIndex() + 1
        year = self.year_spinbox.value()
        self.current_schedule_dates, self.current_schedule_data = generate_schedule(year, month)
        self.display_schedule()
        self.save_button.setEnabled(True); self.export_button.setEnabled(True)

    def display_schedule(self):
        while self.schedule_grid_layout.count():
            child = self.schedule_grid_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        if not self.current_schedule_data: return
        row_offset = 0
        for week_idx, weekly_data in enumerate(self.current_schedule_data):
            week_title = self.current_schedule_dates[week_idx].strftime("Semana del %d de %B de %Y")
            self.schedule_grid_layout.addWidget(QLabel(f"<b>{week_title}</b>"), row_offset, 0, 1, 4)
            row_offset += 1
            for row_idx, row_data in enumerate(weekly_data):
                self.schedule_grid_layout.addWidget(QLabel(str(row_data[0])), row_offset + row_idx, 0, 1, 2)
                original_cell = USER_TEMPLATE_STRUCTURE[week_idx % len(USER_TEMPLATE_STRUCTURE)][row_idx][1]
                if original_cell in ('N', '/'):
                    button = QPushButton(str(row_data[1]))
                    button.clicked.connect(partial(self.open_manual_override_dialog, week_idx, row_idx, 1, button))
                    self.schedule_grid_layout.addWidget(button, row_offset + row_idx, 2, 1, 2)
                else:
                    self.schedule_grid_layout.addWidget(QLabel(str(row_data[1])), row_offset + row_idx, 2, 1, 2)
            row_offset += len(weekly_data)
            if week_idx < len(self.current_schedule_data) - 1:
                separator = QFrame(); separator.setFrameShape(QFrame.Shape.HLine)
                self.schedule_grid_layout.addWidget(separator, row_offset, 0, 1, 4)
                row_offset += 1

    def open_manual_override_dialog(self, week_idx, row_idx, col_idx, button):
        week_template = USER_TEMPLATE_STRUCTURE[week_idx % len(USER_TEMPLATE_STRUCTURE)]
        metadata = _get_metadata_for_slot(row_idx, col_idx, week_template)
        if not metadata: return
        current_assignees = button.text().split(' / ')
        current_person = current_assignees[0]
        candidates = get_people_for_role(metadata['role'], metadata['gender'])
        if not candidates: return
        dialog = ManualOverrideDialog(current_person, candidates, self)
        if dialog.exec():
            new_person = dialog.get_selected_person()
            current_assignees[0] = new_person
            new_text = " / ".join(current_assignees)
            row_list = list(self.current_schedule_data[week_idx][row_idx])
            row_list[col_idx] = new_text
            self.current_schedule_data[week_idx][row_idx] = tuple(row_list)
            button.setText(new_text)
            self.save_button.setEnabled(True)

    def save_schedule(self):
        if not self.current_schedule_data: return
        schedule_dict = {}
        for week_idx, weekly_data in enumerate(self.current_schedule_data):
            date_str = self.current_schedule_dates[week_idx].strftime("%Y-%m-%d")
            assignments = {}
            week_template = USER_TEMPLATE_STRUCTURE[week_idx % len(USER_TEMPLATE_STRUCTURE)]
            for row_idx, row_data in enumerate(weekly_data):
                assignments[week_template[row_idx][0]] = row_data[0]
                assignments[week_template[row_idx][1]] = row_data[1]
            schedule_dict[date_str] = assignments
        save_schedule_to_history(schedule_dict)
        QMessageBox.information(self, "Éxito", "El horario ha sido guardado en el historial.")
        self.save_button.setEnabled(False)

    def export_to_pdf(self):
        if not self.current_schedule_data: return
        default_filename = f"horario_{self.current_schedule_dates[0].strftime('%Y-%m')}.pdf"
        filePath, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", default_filename, "PDF Files (*.pdf)")
        if filePath:
            if export_schedule_to_pdf(self.current_schedule_dates, self.current_schedule_data, filePath):
                QMessageBox.information(self, "Éxito", f"Horario exportado a:\n{filePath}")
            else:
                QMessageBox.critical(self, "Error", "Ocurrió un error al generar el PDF.")
