import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from .person_manager import PersonManagerWidget
from .schedule_viewer import ScheduleViewerWidget
from .role_manager import RoleManagerWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestor de Asignaciones Ministeriales")
        self.resize(1024, 768)

        # Main Tab Widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tab for Person Management
        self.person_manager_tab = PersonManagerWidget()
        self.tabs.addTab(self.person_manager_tab, "Gestionar Personas")

        # Tab for Schedule Viewer
        self.schedule_tab = ScheduleViewerWidget()
        self.tabs.addTab(self.schedule_tab, "Horario (Datos)")

        # Tab for Preview
        from .preview_widget import PreviewWidget
        self.preview_tab = PreviewWidget()
        self.tabs.addTab(self.preview_tab, "Vista Previa de Horario")

        # Tab for Role Management
        self.role_manager_tab = RoleManagerWidget()
        self.tabs.addTab(self.role_manager_tab, "Gestionar Roles")

def main():
    # It's good practice to ensure the database exists before starting the app
    from .database.database_setup import setup_database
    setup_database()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
