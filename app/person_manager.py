import sys
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QLineEdit, QCheckBox, QScrollArea, QDialogButtonBox,
    QMessageBox, QHeaderView, QLabel, QTextEdit, QGroupBox, QAbstractItemView,
    QStyledItemDelegate, QComboBox
)
from PyQt6.QtCore import Qt
from .database.database_manager import (
    get_all_people_with_roles, get_all_roles, add_person_with_roles,
    get_person_details, update_person_with_roles, delete_person,
    add_roles_to_person, remove_roles_from_person
)

class BulkAddDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir Múltiples Personas por Lista")
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

class GenderDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(["No especificado", "Hombre", "Mujer"])
        return editor
    def setEditorData(self, editor, index):
        editor.setCurrentText(str(index.model().data(index, Qt.ItemDataRole.EditRole)))
    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class PersonManagerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QHBoxLayout(self)
        left_panel = QVBoxLayout()
        person_buttons_layout = QHBoxLayout()
        self.add_row_button = QPushButton("Añadir Fila")
        self.bulk_add_button = QPushButton("Añadir por Lista")
        self.delete_button = QPushButton("Eliminar Seleccionados")
        person_buttons_layout.addWidget(self.add_row_button)
        person_buttons_layout.addWidget(self.bulk_add_button)
        person_buttons_layout.addWidget(self.delete_button)
        left_panel.addLayout(person_buttons_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Género", "Roles Asignados"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.SelectedClicked)
        self.gender_delegate = GenderDelegate(self)
        self.table.setItemDelegateForColumn(2, self.gender_delegate)
        left_panel.addWidget(self.table)
        self.main_layout.addLayout(left_panel, 2)
        self.batch_panel = QGroupBox("Asignar Roles a Selección")
        batch_layout = QVBoxLayout(self.batch_panel)
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        roles_widget = QWidget(); self.roles_checkbox_layout = QVBoxLayout(roles_widget)
        scroll_area.setWidget(roles_widget)
        batch_layout.addWidget(scroll_area)
        self.role_checkboxes = []
        batch_buttons_layout = QHBoxLayout()
        self.assign_button = QPushButton("Asignar"); self.unassign_button = QPushButton("Quitar")
        batch_buttons_layout.addWidget(self.assign_button); batch_buttons_layout.addWidget(self.unassign_button)
        batch_layout.addLayout(batch_buttons_layout)
        self.main_layout.addWidget(self.batch_panel, 1)
        self.table.itemChanged.connect(self.handle_item_changed)
        self.table.itemSelectionChanged.connect(self.update_panel_state)
        self.add_row_button.clicked.connect(self.add_new_row)
        self.bulk_add_button.clicked.connect(self.bulk_add_people)
        self.delete_button.clicked.connect(self.delete_person_confirmed)
        self.assign_button.clicked.connect(self.assign_roles_to_selection)
        self.unassign_button.clicked.connect(self.unassign_roles_from_selection)
        self.refresh_table()
        self.update_panel_state()

    def block_signals(self, block): self.table.blockSignals(block)

    def handle_item_changed(self, item):
        self.block_signals(True)
        person_id = int(self.table.item(item.row(), 0).text())
        nombre = self.table.item(item.row(), 1).text()
        genero = self.table.item(item.row(), 2).text()
        _, _, role_ids = get_person_details(person_id)
        update_person_with_roles(person_id, nombre, genero, role_ids)
        self.block_signals(False)

    def add_new_row(self):
        placeholder_name = f"Nueva Persona {int(time.time())}"
        person_id = add_person_with_roles(placeholder_name, 'No especificado', [])
        if person_id is None: return
        self.refresh_table()
        for row in range(self.table.rowCount()):
            if int(self.table.item(row, 0).text()) == person_id:
                self.table.editItem(self.table.item(row, 1))
                break

    def populate_role_checkboxes(self):
        for checkbox in self.role_checkboxes: checkbox.deleteLater()
        self.role_checkboxes.clear()
        for role in get_all_roles():
            cb = QCheckBox(role['nombre']); cb.setProperty("role_id", role['id'])
            self.roles_checkbox_layout.addWidget(cb); self.role_checkboxes.append(cb)

    def update_panel_state(self): self.batch_panel.setEnabled(bool(self.table.selectionModel().selectedRows()))

    def get_selected_person_ids(self): return [int(self.table.item(i.row(), 0).text()) for i in self.table.selectionModel().selectedRows()]

    def assign_roles_to_selection(self):
        p_ids = self.get_selected_person_ids()
        r_ids = [cb.property("role_id") for cb in self.role_checkboxes if cb.isChecked()]
        if not p_ids or not r_ids: return
        for p_id in p_ids: add_roles_to_person(p_id, r_ids)
        self.refresh_table()

    def unassign_roles_from_selection(self):
        p_ids = self.get_selected_person_ids()
        r_ids = [cb.property("role_id") for cb in self.role_checkboxes if cb.isChecked()]
        if not p_ids or not r_ids: return
        for p_id in p_ids: remove_roles_from_person(p_id, r_ids)
        self.refresh_table()

    def refresh_table(self):
        self.block_signals(True)
        self.table.setRowCount(0)
        for row_num, person in enumerate(get_all_people_with_roles()):
            self.table.insertRow(row_num)
            self.table.setItem(row_num, 0, QTableWidgetItem(str(person['id'])))
            self.table.setItem(row_num, 1, QTableWidgetItem(person['nombre']))
            self.table.setItem(row_num, 2, QTableWidgetItem(person['genero']))
            self.table.setItem(row_num, 3, QTableWidgetItem(person['roles'] or 'Sin roles'))
        self.block_signals(False)
        self.populate_role_checkboxes()

    def delete_person_confirmed(self):
        p_ids = self.get_selected_person_ids()
        if not p_ids: return
        reply = QMessageBox.question(self, 'Confirmar', f"¿Eliminar {len(p_ids)} persona(s)?")
        if reply == QMessageBox.StandardButton.Yes:
            for p_id in p_ids: delete_person(p_id)
            self.refresh_table()

    def bulk_add_people(self):
        dialog = BulkAddDialog(self)
        if dialog.exec():
            added, skipped = 0, 0
            for name in dialog.get_names():
                if name.strip() and add_person_with_roles(name.strip(), 'No especificado', []) is not None:
                    added += 1
                else: skipped += 1
            QMessageBox.information(self, "Completado", f"Añadidos: {added}. Omitidos: {skipped}.")
            self.refresh_table()
