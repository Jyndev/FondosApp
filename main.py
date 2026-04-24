import sys
import os

from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from services.environment_checker import EnvironmentChecker
from ui.main_window import MainWindow
from PySide6.QtGui import QFont

def main():
    # Set Wayland as the preferred platform if we are on Hyprland
    if EnvironmentChecker.is_hyprland():
        os.environ["QT_QPA_PLATFORM"] = "wayland"

    app = QApplication(sys.argv)
    
    # Apply system font Fredoka
    app.setFont(QFont("Fredoka One"))
    
    # Apply Material Design theme via ThemeManager
    from ui.theme_manager import ThemeManager
    theme = ThemeManager.get_instance()
    theme.load_system_colors()
    theme.apply_to_app(app)

    is_valid, error_message = EnvironmentChecker.validate()
    if not is_valid:
        show_error_dialog(error_message, title="Entorno no soportado")
        sys.exit(1)

    window = MainWindow()
    window.load_initial_folder()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
