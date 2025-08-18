import sys
from PyQt6.QtWidgets import QLabel, QLineEdit, QVBoxLayout, QWidget
from PyQt6.QtCore import pyqtSignal, Qt

class EditableLabel(QLabel):
    """
    Un QLabel que se convierte en un QLineEdit al hacer doble clic.
    Emite una señal 'textChanged' cuando el texto es editado y confirmado.
    """
    textChanged = pyqtSignal(str)

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        self._line_edit = QLineEdit(self)
        self._line_edit.setWindowFlags(Qt.WindowType.SubWindow)
        self._line_edit.hide()
        self._line_edit.editingFinished.connect(self._handle_editing_finished)

    def mouseDoubleClickEvent(self, event):
        self._line_edit.setText(self.text())
        self._line_edit.selectAll()
        self.setBuddy(self._line_edit) # Ayuda a transferir el foco

        # Posicionar y mostrar el QLineEdit sobre el QLabel
        self._line_edit.setGeometry(self.geometry())
        self._line_edit.show()
        self._line_edit.setFocus()

    def _handle_editing_finished(self):
        new_text = self._line_edit.text()
        self.setText(new_text)
        self.textChanged.emit(new_text)
        self._line_edit.hide()
