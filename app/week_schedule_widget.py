import sys
from datetime import timedelta
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal
from .editable_label import EditableLabel

class WeekScheduleWidget(QWidget):
    themeChanged = pyqtSignal(str, str) # old_theme, new_theme
    """
    Un widget para mostrar el horario de una sola semana con un diseño
    que imita la imagen de `Programa.png`.
    """
    def __init__(self, week_date, week_data, theme_overrides={}, parent=None):
        super().__init__(parent)
        self.week_date = week_date
        self.week_data = week_data
        self.theme_overrides = theme_overrides

        # Set a border for visual debugging
        self.setStyleSheet("border: 1px solid black;")

        self.init_ui()

    def _create_styled_label(self, text, bold=False, point_size=10, alignment=Qt.AlignmentFlag.AlignLeft, italic=False, text_color=None):
        label = QLabel(text)
        font = label.font()
        font.setBold(bold)
        font.setPointSize(point_size)
        font.setItalic(italic)
        label.setFont(font)
        label.setAlignment(alignment)
        label.setWordWrap(True)
        if text_color:
            label.setStyleSheet(f"color: {text_color};")
        return label

    def _create_section_header(self, text, background_color, text_color="white"):
        label = self._create_styled_label(text, bold=True, point_size=11, alignment=Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"background-color: {background_color}; color: {text_color}; padding: 4px; border-radius: 3px;")
        return label

    def init_ui(self):
        """
        Construye la interfaz de usuario para el widget de la semana.
        """
        if isinstance(self.week_data, dict) and self.week_data.get('is_special'):
            self.build_special_week_ui()
        else:
            self.build_normal_week_ui()

    def build_special_week_ui(self):
        layout = QVBoxLayout(self)

        try:
            start_date_str = self.week_date.strftime("%-d").lstrip("0")
        except ValueError:
            start_date_str = self.week_date.strftime("%#d").lstrip("0")

        end_date = self.week_date + timedelta(days=6)
        end_date_str = end_date.strftime("%B %Y")
        week_range_str = f"{start_date_str} - {end_date.day} de {end_date_str}"

        layout.addWidget(self._create_styled_label(week_range_str, bold=True, point_size=13))

        reason_label = self._create_styled_label(self.week_data.get('reason', 'Sin motivo especificado'), bold=True, point_size=12, alignment=Qt.AlignmentFlag.AlignCenter)
        reason_label.setStyleSheet("color: #c62828; margin-top: 10px; margin-bottom: 10px;")
        layout.addWidget(reason_label)

        self.setLayout(layout)

    def build_normal_week_ui(self):
        """
        Construye la interfaz de usuario para una semana normal.
        """
        try:
            layout = QGridLayout(self)
            layout.setSpacing(6)

            # --- Fila 0: Encabezado Principal (Fecha y Presidente) ---
            start_date_str = self.week_date.strftime("%#d")
            end_date = self.week_date + timedelta(days=6)
            end_date_str = end_date.strftime("%#d de %B de %Y")
            date_range_str = f"<b>{start_date_str} - {end_date_str}</b>"

            president_name = self.week_data[0][1]
            layout.addWidget(self._create_styled_label(date_range_str, point_size=13), 0, 0, 1, 5)
            layout.addWidget(self._create_styled_label(f"Presidente: {president_name}", bold=True, point_size=11), 0, 5, 1, 3, Qt.AlignmentFlag.AlignRight)

            # --- Fila 1: Oración de Inicio y Separador ---
            oracion_inicio_name = self.week_data[1][0]
            layout.addWidget(self._create_styled_label(f"Oración de inicio: {oracion_inicio_name}", bold=True), 1, 0, 1, 4)
            line_sep = QFrame(); line_sep.setFrameShape(QFrame.Shape.HLine); line_sep.setFrameShadow(QFrame.Shape.Sunken)
            layout.addWidget(line_sep, 2, 0, 1, 8)

            # --- Fila 3: TESOROS DE LA BIBLIA ---
            header_tesoros = self._create_section_header("TESOROS DE LA BIBLIA", "#00796b")
            layout.addWidget(header_tesoros, 3, 0, 1, 4)

            original_theme_tesoros = self.week_data[3][0]
            display_theme_tesoros = self.theme_overrides.get(original_theme_tesoros, original_theme_tesoros)
            editable_theme_tesoros = EditableLabel(display_theme_tesoros, self)
            editable_theme_tesoros.setFont(self._create_styled_label("", italic=True).font())
            editable_theme_tesoros.textChanged.connect(lambda new_text, old_theme=original_theme_tesoros: self.themeChanged.emit(old_theme, new_text))
            layout.addWidget(editable_theme_tesoros, 4, 1, 1, 3)

            layout.addWidget(self._create_styled_label(f"<b>Busquemos perlas escondidas:</b> {self.week_data[5][1]}"), 5, 1, 1, 3)
            layout.addWidget(self._create_styled_label(f"<b>Lectura de la Biblia:</b> {self.week_data[7][1]}"), 6, 1, 1, 3)

            # --- Fila 3-6: Sala Auxiliar B ---
            layout.addWidget(self._create_styled_label(f"<b>Lectura de la Biblia (Sala B)</b><br>{self.week_data[1][1]}", point_size=9), 3, 5, 1, 3)
            layout.addWidget(self._create_styled_label(f"<b>{self.week_data[3][1]}:</b><br>{self.week_data[4][1]}", point_size=9), 4, 5, 1, 3)
            layout.addWidget(self._create_styled_label(f"<b>{self.week_data[5][1]}:</b><br>{self.week_data[6][1]}", point_size=9), 5, 5, 1, 3)
            layout.addWidget(self._create_styled_label(f"<b>{self.week_data[7][1]}:</b><br>{self.week_data[8][1]}", point_size=9), 6, 5, 1, 3)

            # --- Fila 7: SEAMOS MEJORES MAESTROS y NUESTRA VIDA CRISTIANA ---
            header_maestros = self._create_section_header("SEAMOS MEJORES MAESTROS", "#c62828")
            layout.addWidget(header_maestros, 7, 0, 1, 4)
            header_vida = self._create_section_header("NUESTRA VIDA CRISTIANA", "#6a1b9a")
            layout.addWidget(header_vida, 7, 4, 1, 4)

            # --- Contenido de Maestros (CORREGIDO) ---
            # Asignación 1
            layout.addWidget(self._create_styled_label(f"<b>{self.week_data[10][0]}:</b><br>{self.week_data[11][0]}", point_size=9), 8, 1, 1, 3)
            # Asignación 2
            layout.addWidget(self._create_styled_label(f"<b>{self.week_data[12][0]}:</b><br>{self.week_data[13][0]}", point_size=9), 9, 1, 1, 3)
            # Asignación 3
            layout.addWidget(self._create_styled_label(f"<b>{self.week_data[14][0]}:</b><br>{self.week_data[15][0]}", point_size=9), 10, 1, 1, 3)

            # --- Contenido de Vida Cristiana (CORREGIDO) ---
            original_vida_1_title = self.week_data[10][1]
            display_vida_1_title = self.theme_overrides.get(original_vida_1_title, original_vida_1_title)
            vida_1_name = self.week_data[11][1]
            vida_1_layout = QVBoxLayout(); vida_1_layout.setSpacing(0)
            vida_1_title_label = EditableLabel(f"<b>{display_vida_1_title}:</b>", self)
            vida_1_title_label.setFont(self._create_styled_label("", point_size=9).font())
            vida_1_title_label.textChanged.connect(lambda new_text, old_theme=original_vida_1_title: self.themeChanged.emit(old_theme, new_text.replace("<b>","").replace("</b>","").replace(":","")))
            vida_1_name_label = self._create_styled_label(vida_1_name, point_size=9)
            vida_1_layout.addWidget(vida_1_title_label)
            vida_1_layout.addWidget(vida_1_name_label)
            layout.addLayout(vida_1_layout, 8, 5, 1, 3)

            # Estudio Bíblico
            layout.addWidget(self._create_styled_label(f"<b>{self.week_data[13][1]}:</b><br>{self.week_data[14][1]}", point_size=9), 9, 5, 1, 3)
            # Oración final
            layout.addWidget(self._create_styled_label(f"<b>Oración de final:</b> {self.week_data[15][1]}", bold=True), 10, 5, 1, 3)

            # --- Fila 11: Acomodadores ---
            layout.addWidget(self._create_styled_label(f"<b>{self.week_data[16][0]}:</b> {self.week_data[17][0]}"), 11, 0, 1, 4)
            layout.addWidget(self._create_styled_label(f"<b>{self.week_data[16][1]}:</b> {self.week_data[17][1]}"), 11, 4, 1, 4)

            # Set column stretch
            for i in range(8): layout.setColumnStretch(i, 1)

        except Exception as e:
            # --- Bloque de Error ---
            print(f"Error al construir la semana UI: {e}")
            print(f"Datos problemáticos: {self.week_data}")
            # Mostrar un mensaje de error en el propio widget
            layout = QVBoxLayout(self)
            error_label = QLabel(f"Error al renderizar esta semana.\nConsulte la consola para más detalles.\n\nError: {e}")
            error_label.setStyleSheet("color: red; font-weight: bold;")
            layout.addWidget(error_label)
            # Limpiar cualquier widget que se haya añadido antes del error
            while self.layout() and self.layout().count():
                child = self.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            self.setLayout(layout)
