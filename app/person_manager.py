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
    add_roles_to_person, remove_roles_from_person, update_person_gender
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

        # Filter layout
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrar por Rol:"))
        self.role_filter_combo = QComboBox()
        filter_layout.addWidget(self.role_filter_combo)
        left_panel.addLayout(filter_layout)

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

        # --- Batch Gender Change ---
        gender_group = QGroupBox("Cambiar Género a Selección")
        gender_layout = QVBoxLayout(gender_group)
        self.batch_gender_combo = QComboBox()
        self.batch_gender_combo.addItems(["Hombre", "Mujer"])
        self.apply_gender_button = QPushButton("Aplicar Género")
        gender_layout.addWidget(self.batch_gender_combo)
        gender_layout.addWidget(self.apply_gender_button)
        batch_layout.addWidget(gender_group)

        batch_layout.addStretch() # Add a spacer at the end

        self.main_layout.addWidget(self.batch_panel, 1)
        self.table.itemChanged.connect(self.handle_item_changed)
        self.table.itemSelectionChanged.connect(self.update_panel_state)
        self.role_filter_combo.currentIndexChanged.connect(self.refresh_table)
        self.add_row_button.clicked.connect(self.add_new_row)
        self.bulk_add_button.clicked.connect(self.bulk_add_people)
        self.delete_button.clicked.connect(self.delete_person_confirmed)
        self.assign_button.clicked.connect(self.assign_roles_to_selection)
        self.unassign_button.clicked.connect(self.unassign_roles_from_selection)
        self.apply_gender_button.clicked.connect(self.apply_batch_gender)
        self.populate_role_filter()
        self.refresh_table()
        self.update_panel_state()

    def block_signals(self, block): self.table.blockSignals(block)

    def handle_item_changed(self, item):
        if not item or not self.table.item(item.row(), 0) or not self.table.item(item.row(), 0).text().isdigit():
            return

        self.block_signals(True)
        person_id = int(self.table.item(item.row(), 0).text())
        nombre = self.table.item(item.row(), 1).text()
        genero = self.table.item(item.row(), 2).text()

        if not nombre.strip():
            QMessageBox.warning(self, "Nombre Inválido", "El nombre no puede estar vacío. Se restaurará el nombre original.")
            _, original_nombre, _, _ = get_person_details(person_id)
            self.table.item(item.row(), 1).setText(original_nombre)
            self.block_signals(False)
            return

        _, _, role_ids = get_person_details(person_id)
        update_person_with_roles(person_id, nombre, genero, role_ids)
        self.block_signals(False)

    def add_new_row(self):
        self.table.blockSignals(True)

        placeholder_name = f"Nueva Persona {int(time.time())}"
        person_id = add_person_with_roles(placeholder_name, 'No especificado', [])

        if person_id is None:
            self.table.blockSignals(False)
            QMessageBox.critical(self, "Error", "No se pudo crear la nueva persona en la base de datos.")
            return

        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        id_item = QTableWidgetItem(str(person_id))
        name_item = QTableWidgetItem(placeholder_name)
        gender_item = QTableWidgetItem('No especificado')
        roles_item = QTableWidgetItem('Sin roles')

        self.table.setItem(row_position, 0, id_item)
        self.table.setItem(row_position, 1, name_item)
        self.table.setItem(row_position, 2, gender_item)
        self.table.setItem(row_position, 3, roles_item)

        self.table.blockSignals(False)

        self.table.scrollToItem(name_item)
        self.table.editItem(name_item)

    def populate_role_checkboxes(self):
        for checkbox in self.role_checkboxes: checkbox.deleteLater()
        self.role_checkboxes.clear()
        for role in get_all_roles():
            cb = QCheckBox(role['nombre']); cb.setProperty("role_id", role['id'])
            self.roles_checkbox_layout.addWidget(cb); self.role_checkboxes.append(cb)

    def populate_role_filter(self):
        self.role_filter_combo.blockSignals(True)
        current_id = self.role_filter_combo.currentData()
        self.role_filter_combo.clear()
        self.role_filter_combo.addItem("Todos", None)
        for role in get_all_roles():
            self.role_filter_combo.addItem(role['nombre'], role['id'])

        # Restore previous selection if it still exists
        index = self.role_filter_combo.findData(current_id)
        if index != -1:
            self.role_filter_combo.setCurrentIndex(index)
        self.role_filter_combo.blockSignals(False)

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
        role_filter_id = self.role_filter_combo.currentData()
        self.table.setRowCount(0)
        for row_num, person in enumerate(get_all_people_with_roles(role_id_filter=role_filter_id)):
            self.table.insertRow(row_num)
            self.table.setItem(row_num, 0, QTableWidgetItem(str(person['id'])))
            self.table.setItem(row_num, 1, QTableWidgetItem(person['nombre']))
            self.table.setItem(row_num, 2, QTableWidgetItem(person['genero']))
            self.table.setItem(row_num, 3, QTableWidgetItem(person['roles'] or 'Sin roles'))
        self.block_signals(False)
        self.populate_role_checkboxes()
        self.populate_role_filter()

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

    def apply_batch_gender(self):
        p_ids = self.get_selected_person_ids()
        if not p_ids:
            QMessageBox.information(self, "Información", "Selecciona al menos una persona.")
            return

        gender = self.batch_gender_combo.currentText()

        for p_id in p_ids:
            update_person_gender(p_id, gender)

        self.refresh_table()
        QMessageBox.information(self, "Éxito", f"Género actualizado para {len(p_ids)} persona(s).")
