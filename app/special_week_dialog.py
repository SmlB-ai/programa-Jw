import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QComboBox, QLineEdit, QLabel, QMessageBox
)
from PyQt6.QtCore import QDate
from .database.database_manager import get_special_weeks_for_month, add_special_week, remove_special_week

class SpecialWeekDialog(QDialog):
    def __init__(self, year, month, meeting_dates, parent=None):
        super().__init__(parent)
        self.year = year
        self.month = month
        self.meeting_dates = meeting_dates
        self.setWindowTitle("Gestionar Semanas Especiales")
        self.setMinimumWidth(400)

        self.main_layout = QVBoxLayout(self)

        # Lista de semanas especiales existentes
        self.main_layout.addWidget(QLabel("Semanas especiales en este mes:"))
        self.list_widget = QListWidget()
        self.main_layout.addWidget(self.list_widget)

        # Controles para añadir/quitar
        controls_layout = QHBoxLayout()
        self.remove_button = QPushButton("Eliminar Seleccionada")
        self.remove_button.setEnabled(False)
        controls_layout.addWidget(self.remove_button)
        self.main_layout.addLayout(controls_layout)

        self.main_layout.addWidget(QLabel("Añadir nueva semana especial:"))
        add_layout = QHBoxLayout()
        self.date_combo = QComboBox()
        for dt in self.meeting_dates:
            self.date_combo.addItem(dt.toString("d 'de' MMMM"), dt)

        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("Motivo (ej: Asamblea Regional)")
        self.add_button = QPushButton("Añadir")

        add_layout.addWidget(self.date_combo)
        add_layout.addWidget(self.reason_input)
        add_layout.addWidget(self.add_button)
        self.main_layout.addLayout(add_layout)

        # Conexiones
        self.add_button.clicked.connect(self.add_item)
        self.remove_button.clicked.connect(self.remove_item)
        self.list_widget.itemSelectionChanged.connect(lambda: self.remove_button.setEnabled(True))

        self.populate_list()

    def populate_list(self):
        self.list_widget.clear()
        special_weeks = get_special_weeks_for_month(self.year, self.month)
        for date_str, reason in sorted(special_weeks.items()):
            date_obj = QDate.fromString(date_str, "yyyy-MM-dd")
            item = QListWidgetItem(f"{date_obj.toString('d MMMM')}: {reason}")
            item.setData(Qt.ItemDataRole.UserRole, date_obj)
            self.list_widget.addItem(item)
        self.remove_button.setEnabled(False)

    def add_item(self):
        date_obj = self.date_combo.currentData()
        reason = self.reason_input.text().strip()
        if not reason:
            QMessageBox.warning(self, "Error", "El motivo no puede estar vacío.")
            return

        add_special_week(date_obj.toString("yyyy-MM-dd"), reason)
        self.reason_input.clear()
        self.populate_list()

    def remove_item(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item:
            return

        date_obj = selected_item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "Confirmar", f"¿Seguro que quieres eliminar la semana especial del {date_obj.toString('d MMMM')}?")

        if reply == QMessageBox.StandardButton.Yes:
            remove_special_week(date_obj.toString("yyyy-MM-dd"))
            self.populate_list()
