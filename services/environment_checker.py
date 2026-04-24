import os
import shutil
from utils.logger import get_logger

logger = get_logger(__name__)

class EnvironmentChecker:
    @staticmethod
    def is_hyprland():
        xdg_current = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        hypr_sig = os.environ.get('HYPRLAND_INSTANCE_SIGNATURE', '')
        
        if 'hyprland' in xdg_current or hypr_sig:
            return True
        return False

    @staticmethod
    def is_awww_installed():
        return shutil.which('awww') is not None

    @staticmethod
    def validate():
        if not EnvironmentChecker.is_hyprland():
            logger.error("Error: This application only works on Hyprland.")
            return False, "Esta aplicación requiere Hyprland para funcionar."
            
        if not EnvironmentChecker.is_awww_installed():
            logger.error("Error: 'awww' is not installed.")
            return False, "La herramienta 'awww' no está instalada.\nEjecute 'sudo pacman -S awww'."
            
        return True, ""
