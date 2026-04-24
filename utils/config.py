from PySide6.QtCore import QSettings
import os

class AppConfig:
    def __init__(self):
        self.settings = QSettings("FondosApp", "HyprlandWallpaper")
        
    def get_last_folder(self):
        home_pic = os.path.expanduser("~/Pictures")
        return self.settings.value("last_folder", home_pic)
        
    def set_last_folder(self, path):
        self.settings.setValue("last_folder", path)
