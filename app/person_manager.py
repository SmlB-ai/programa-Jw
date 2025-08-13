import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QLineEdit, QCheckBox, QScrollArea, QDialogButtonBox,
    QMessageBox, QHeaderView, QLabel, QTextEdit
)
from PyQt6.QtCore import Qt
from .database.database_manager import (
    get_all_people_with_roles, get_all_roles, add_person_with_roles,
    get_person_details, update_person_with_roles, delete_person
)

class PersonDialog(QDialog):
    def __init__(self, person_id=None, parent=None):
        super().__init__(parent)
        self.person_id = person_id
        self.setWindowTitle("Añadir/Editar Persona")
        self.setMinimumWidth(400)

        self.layout = QVBoxLayout(self)

        # Name field
        self.layout.addWidget(QLabel("Nombre:"))
        self.name_input = QLineEdit()
        self.layout.addWidget(self.name_input)

        # Gender field
        self.layout.addWidget(QLabel("Género:"))
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["No especificado", "Hombre", "Mujer"])
        self.layout.addWidget(self.gender_combo)

        # Roles area
        self.layout.addWidget(QLabel("Roles Asignados:"))
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.roles_widget = QWidget()
        self.roles_layout = QVBoxLayout(self.roles_widget)
        self.scroll_area.setWidget(self.roles_widget)
        self.layout.addWidget(self.scroll_area)

        self.role_checkboxes = []
        self.all_roles = get_all_roles()
        for role in self.all_roles:
            checkbox = QCheckBox(role['nombre'])
            checkbox.setProperty("role_id", role['id'])
            self.role_checkboxes.append(checkbox)
            self.roles_layout.addWidget(checkbox)

        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        if self.person_id:
            self.load_person_data()

    def load_person_data(self):
        nombre, genero, assigned_role_ids = get_person_details(self.person_id)
        if nombre is None:
            self.name_input.setText("Error: Persona no encontrada")
            return

        self.name_input.setText(nombre)
        self.gender_combo.setCurrentText(genero)
        for checkbox in self.role_checkboxes:
            role_id = checkbox.property("role_id")
            if role_id in assigned_role_ids:
                checkbox.setChecked(True)

    def get_data(self):
        name = self.name_input.text().strip()
        gender = self.gender_combo.currentText()
        selected_role_ids = []
        for checkbox in self.role_checkboxes:
            if checkbox.isChecked():
                selected_role_ids.append(checkbox.property("role_id"))
        return name, gender, selected_role_ids

class BulkAddDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir Múltiples Personas")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Pega una lista de nombres (uno por línea):"))

        self.names_input = QTextEdit()
        layout.addWidget(self.names_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_names(self):
        return self.names_input.toPlainText().strip().split('\n')

class PersonManagerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)

        # Button layout
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Añadir Persona")
        self.bulk_add_button = QPushButton("Añadir Varios")
        self.edit_button = QPushButton("Editar Persona")
        self.delete_button = QPushButton("Eliminar Persona")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.bulk_add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        self.layout.addLayout(button_layout)

        # Table for people
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Género", "Roles Asignados"])
        self.table.setColumnHidden(0, True) # Hide ID column
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.layout.addWidget(self.table)

        # Connect signals
        self.add_button.clicked.connect(self.add_person)
        self.bulk_add_button.clicked.connect(self.bulk_add_people)
        self.edit_button.clicked.connect(self.edit_person)
        self.delete_button.clicked.connect(self.delete_person_confirmed)

        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(0)
        people = get_all_people_with_roles()
        for row_num, person in enumerate(people):
            self.table.insertRow(row_num)
            self.table.setItem(row_num, 0, QTableWidgetItem(str(person['id'])))
            self.table.setItem(row_num, 1, QTableWidgetItem(person['nombre']))
            self.table.setItem(row_num, 2, QTableWidgetItem(person['genero']))
            self.table.setItem(row_num, 3, QTableWidgetItem(person['roles'] or 'Sin roles'))

    def add_person(self):
        dialog = PersonDialog(parent=self)
        if dialog.exec():
            name, gender, role_ids = dialog.get_data()
            if not name:
                QMessageBox.warning(self, "Entrada Inválida", "El nombre no puede estar vacío.")
                return

            result = add_person_with_roles(name, gender, role_ids)
            if result is None:
                QMessageBox.warning(self, "Error", f"Ya existe una persona con el nombre '{name}'.")
            else:
                self.refresh_table()

    def edit_person(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Selección Requerida", "Por favor, selecciona una persona para editar.")
            return

        person_id = int(self.table.item(selected_rows[0].row(), 0).text())
        dialog = PersonDialog(person_id=person_id, parent=self)
        if dialog.exec():
            name, gender, role_ids = dialog.get_data()
            if not name:
                QMessageBox.warning(self, "Entrada Inválida", "El nombre no puede estar vacío.")
                return
            update_person_with_roles(person_id, name, gender, role_ids)
            self.refresh_table()

    def delete_person_confirmed(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Selección Requerida", "Por favor, selecciona una persona para eliminar.")
            return

        person_id = int(self.table.item(selected_rows[0].row(), 0).text())
        person_name = self.table.item(selected_rows[0].row(), 1).text()

        reply = QMessageBox.question(self, 'Confirmar Eliminación',
                                     f"¿Estás seguro de que quieres eliminar a '{person_name}'? Esta acción no se puede deshacer.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            delete_person(person_id)
            self.refresh_table()

    def bulk_add_people(self):
        dialog = BulkAddDialog(self)
        if dialog.exec():
            names = dialog.get_names()
            added_count = 0
            skipped_count = 0
            for name in names:
                name = name.strip()
                if not name:
                    continue

                # add_person_with_roles returns None if the name already exists
                if add_person_with_roles(name, 'No especificado', []) is not None:
                    added_count += 1
                else:
                    skipped_count += 1

            QMessageBox.information(self, "Proceso Completado",
                                    f"Se añadieron {added_count} personas nuevas.\n"
                                    f"Se omitieron {skipped_count} nombres (vacíos o ya existentes).")
            self.refresh_table()
