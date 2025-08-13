import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QInputDialog, QLineEdit
)
from .database.database_manager import get_all_roles, add_role, rename_role, delete_role

class RoleManagerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)

        # Button layout
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Añadir Rol")
        self.rename_button = QPushButton("Renombrar Rol")
        self.delete_button = QPushButton("Eliminar Rol")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.rename_button)
        button_layout.addWidget(self.delete_button)
        self.layout.addLayout(button_layout)

        # List for roles
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        # Connect signals
        self.add_button.clicked.connect(self.add_role)
        self.rename_button.clicked.connect(self.rename_role)
        self.delete_button.clicked.connect(self.delete_role_confirmed)

        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        roles = get_all_roles()
        for role in roles:
            item = QListWidgetItem(role['nombre'])
            item.setData(1, role['id']) # Store ID in user data role
            self.list_widget.addItem(item)

    def add_role(self):
        text, ok = QInputDialog.getText(self, 'Añadir Rol', 'Nombre del nuevo rol:', QLineEdit.EchoMode.Normal)
        if ok and text:
            if add_role(text):
                self.refresh_list()
            else:
                QMessageBox.warning(self, "Error", f"No se pudo añadir el rol '{text}'. Puede que ya exista.")

    def rename_role(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "Selección Requerida", "Por favor, selecciona un rol para renombrar.")
            return

        role_id = selected_item.data(1)
        old_name = selected_item.text()

        text, ok = QInputDialog.getText(self, 'Renombrar Rol', 'Nuevo nombre del rol:', QLineEdit.EchoMode.Normal, old_name)
        if ok and text and text != old_name:
            if rename_role(role_id, text):
                self.refresh_list()
            else:
                QMessageBox.warning(self, "Error", f"No se pudo renombrar el rol. Puede que el nuevo nombre '{text}' ya exista.")

    def delete_role_confirmed(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "Selección Requerida", "Por favor, selecciona un rol para eliminar.")
            return

        role_id = selected_item.data(1)
        role_name = selected_item.text()

        reply = QMessageBox.question(self, 'Confirmar Eliminación',
                                     f"¿Estás seguro de que quieres eliminar el rol '{role_name}'? "
                                     "Esto también eliminará todas las asignaciones de este rol a las personas.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            delete_role(role_id)
            self.refresh_list()
