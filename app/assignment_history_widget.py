import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView
)
from PyQt6.QtCore import Qt
from .database.database_manager import get_assignment_history_summary

class AssignmentHistoryWidget(QWidget):
    """
    Un widget para mostrar una tabla con el historial de la última
    asignación de cada persona.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)

        # --- Botón de Refrescar ---
        self.refresh_button = QPushButton("Refrescar Historial")
        self.main_layout.addWidget(self.refresh_button)

        # --- Tabla de Historial ---
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Nombre", "Fecha de Última Asignación", "Descripción"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Read-only
        self.main_layout.addWidget(self.table)

        # --- Conexiones ---
        self.refresh_button.clicked.connect(self.populate_table)

        # Poblar la tabla al inicio
        self.populate_table()

    def populate_table(self):
        self.table.setRowCount(0) # Limpiar tabla
        history_data = get_assignment_history_summary()

        if not history_data:
            return

        self.table.setRowCount(len(history_data))
        for row_idx, row_data in enumerate(history_data):
            # Columnas: nombre, fecha_reunion, descripcion_asignacion
            name_item = QTableWidgetItem(row_data['nombre'])

            date_str = row_data['fecha_reunion']
            date_item = QTableWidgetItem(date_str if date_str else "N/A")

            desc_str = row_data['descripcion_asignacion']
            desc_item = QTableWidgetItem(desc_str if desc_str else "N/A")

            self.table.setItem(row_idx, 0, name_item)
            self.table.setItem(row_idx, 1, date_item)
            self.table.setItem(row_idx, 2, desc_item)
