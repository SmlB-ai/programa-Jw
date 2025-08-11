import sys
import calendar
from functools import partial
import sys
import calendar
from functools import partial
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QScrollArea, QFrame, QMessageBox, QDialog, QDialogButtonBox,
    QFileDialog
)
from PyQt6.QtCore import QDate
from .assignment_algorithm import generate_schedule, TEMPLATES_CYCLE
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
        self.candidates = candidates
        for candidate in self.candidates:
            self.combo.addItem(candidate['nombre'], userData=candidate['id'])
        layout.addWidget(self.combo)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_selected_person(self):
        return self.combo.currentText()

class ScheduleViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_schedule = None
        self.person_buttons = {} # To keep track of the buttons to update them

        self.main_layout = QVBoxLayout(self)
        # ... (Controls are the same as before) ...
        # --- Controls Layout ---
        controls_layout = QHBoxLayout()
        self.month_combo = QComboBox()
        self.year_spinbox = QSpinBox()
        self.generate_button = QPushButton("Generar Horario")
        self.save_button = QPushButton("Guardar en Historial")
        self.export_button = QPushButton("Exportar a PDF")
        self.save_button.setEnabled(False)
        self.export_button.setEnabled(False)

        # Populate controls
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

        # --- Scroll Area for Schedule ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.schedule_container = QWidget()
        self.schedule_layout = QVBoxLayout(self.schedule_container)
        self.scroll_area.setWidget(self.schedule_container)
        self.main_layout.addWidget(self.scroll_area)

        self.generate_button.clicked.connect(self.run_schedule_generation)
        self.save_button.clicked.connect(self.save_schedule)
        self.export_button.clicked.connect(self.export_to_pdf)

    def run_schedule_generation(self):
        month = self.month_combo.currentIndex() + 1
        year = self.year_spinbox.value()
        self.current_schedule = generate_schedule(year, month)
        self.display_schedule(self.current_schedule)
        self.save_button.setEnabled(True)
        self.export_button.setEnabled(True)

    def display_schedule(self, schedule_data):
        self.person_buttons.clear()
        while self.schedule_layout.count():
            child = self.schedule_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not schedule_data:
            self.schedule_layout.addWidget(QLabel("No hay reuniones para el mes seleccionado."))
            return

        sorted_dates = sorted(schedule_data.keys())
        all_templates = {item['slot']: item for template in TEMPLATES_CYCLE for item in template}

        for date_str in sorted_dates:
            week_frame = QFrame()
            week_frame.setFrameShape(QFrame.Shape.StyledPanel)
            week_layout = QGridLayout(week_frame)

            date_obj = QDate.fromString(date_str, "yyyy-MM-dd")
            week_label = QLabel(f"<b>Semana del {date_obj.toString('d MMMM yyyy')}</b>")
            week_layout.addWidget(week_label, 0, 0, 1, 2)

            weekly_assignments = schedule_data[date_str]
            row = 1
            for slot, person in weekly_assignments.items():
                title_label = QLabel(f"{slot.replace('_', ' ')}:")
                title_label.setStyleSheet("font-weight: bold;")
                week_layout.addWidget(title_label, row, 0)

                role_info = all_templates.get(slot)
                if role_info and role_info.get('role'):
                    # This is an assignable slot, make the person a button
                    person_button = QPushButton(str(person))
                    person_button.clicked.connect(partial(self.open_override_dialog, date_str, slot, person_button))
                    self.person_buttons[(date_str, slot)] = person_button
                    week_layout.addWidget(person_button, row, 1)
                else:
                    # This is a title or non-assignable item
                    week_layout.addWidget(QLabel(str(person)), row, 1)

                row += 1

            self.schedule_layout.addWidget(week_frame)

    def open_override_dialog(self, date_str, slot, button):
        current_person = button.text()
        all_templates = {item['slot']: item for template in TEMPLATES_CYCLE for item in template}
        role_name = all_templates.get(slot, {}).get('role')

        if not role_name:
            QMessageBox.information(self, "No Asignable", "Este campo no es una asignación que se pueda cambiar.")
            return

        candidates = get_people_for_role(role_name)
        if not candidates:
            QMessageBox.warning(self, "Sin Candidatos", f"No hay personas disponibles con el rol '{role_name}'.")
            return

        dialog = ManualOverrideDialog(current_person, candidates, self)
        if dialog.exec():
            new_person = dialog.get_selected_person()
            # Update data and UI
            self.current_schedule[date_str][slot] = new_person
            button.setText(new_person)
            self.save_button.setEnabled(True) # Re-enable save button after manual edit

    def save_schedule(self):
        if not self.current_schedule:
            QMessageBox.warning(self, "Sin Horario", "Primero debes generar un horario.")
            return

        reply = QMessageBox.question(self, 'Confirmar Guardado',
                                     "¿Estás seguro de que quieres guardar este horario en el historial? "
                                     "Cualquier asignación existente para estas fechas será sobreescrita.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            save_schedule_to_history(self.current_schedule)
            QMessageBox.information(self, "Éxito", "El horario ha sido guardado en el historial.")
            self.save_button.setEnabled(False)

    def export_to_pdf(self):
        if not self.current_schedule:
            QMessageBox.warning(self, "Sin Horario", "Primero debes generar un horario para poder exportarlo.")
            return

        # Propose a default filename
        first_date_str = sorted(self.current_schedule.keys())[0]
        default_filename = f"horario_{first_date_str[:7]}.pdf" # e.g., horario_2025-01.pdf

        filePath, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", default_filename, "PDF Files (*.pdf)")

        if filePath:
            success = export_schedule_to_pdf(self.current_schedule, filePath)
            if success:
                QMessageBox.information(self, "Éxito", f"El horario ha sido exportado a:\n{filePath}")
            else:
                QMessageBox.critical(self, "Error", "Ocurrió un error al generar el archivo PDF.")
