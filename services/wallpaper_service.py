import subprocess
import os
import shutil
import time
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

class WallpaperService:
    def __init__(self):
        self.matugen_config = Path(os.path.expanduser("~/.config/matugen/config.toml"))

    def _get_clean_env(self):
        """Devuelve el entorno original sin las variables de PyInstaller."""
        env = os.environ.copy()
        
        # Eliminar cualquier variable inyectada por PyInstaller para evitar 
        # que AGS o programas hijos asuman que están dentro del bundle.
        keys_to_remove = [k for k in env if k.startswith('_PYI_')]
        for k in keys_to_remove:
            del env[k]

        if 'LD_LIBRARY_PATH_ORIG' in env:
            env['LD_LIBRARY_PATH'] = env['LD_LIBRARY_PATH_ORIG']
            del env['LD_LIBRARY_PATH_ORIG']
        elif 'LD_LIBRARY_PATH' in env:
            del env['LD_LIBRARY_PATH']
        return env

    def _ensure_daemon_running(self):
        """Ensures that awww-daemon is running before attempting to use awww client."""
        try:
            subprocess.run(["pgrep", "awww-daemon"], check=True, capture_output=True, env=self._get_clean_env())
        except subprocess.CalledProcessError:
            logger.info("awww-daemon not running, starting it...")
            try:
                subprocess.Popen(["awww-daemon"], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=self._get_clean_env())
                import time
                time.sleep(1) # Give it a moment to initialize the socket
            except Exception as e:
                logger.error(f"Failed to start awww-daemon: {e}")

    def _get_matugen_mode(self):
        try:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True, text=True, env=self._get_clean_env()
            )
            mode_str = result.stdout.strip()
            if "prefer-dark" in mode_str:
                return "dark"
            return "light"
        except Exception as e:
            logger.error(f"Error reading gsettings: {e}")
            return "dark" # Default fallback

    def _apply_theme(self, image_path, scheme_type="scheme-tonal-spot"):
        if not shutil.which('matugen'):
            logger.error("matugen is not installed.")
            return False, "Matugen no está instalado en el sistema.", {}
            
        mode = self._get_matugen_mode()
        extracted_colors = {}
        
        try:
            # matugen image "path" -m "dark/light" -t scheme-tonal-spot
            matugen_cmd = ["matugen", "image", str(image_path), "-m", mode, "-t", scheme_type]
            
            # Use specific config if it exists
            if self.matugen_config.exists():
                matugen_cmd.extend(["-c", str(self.matugen_config)])
                
            # Add flag to non-interactively select the primary color and run as normal subprocess
            matugen_cmd.extend(["--source-color-index", "0"])
            
            result = subprocess.run(matugen_cmd, capture_output=True, text=True, cwd=os.path.expanduser("~"), env=self._get_clean_env())
            
            if result.returncode != 0:
                 return False, f"Error matugen:\n{result.stderr[-100:]}", {}

            # Extract colors array from matugen dynamically
            import json
            json_cmd = ["matugen", "image", str(image_path), "-m", mode, "-t", scheme_type, "-j", "hex", "--source-color-index", "0", "--dry-run"]
            json_result = subprocess.run(json_cmd, capture_output=True, text=True, cwd=os.path.expanduser("~"), env=self._get_clean_env())
            if json_result.returncode == 0:
                try:
                    extracted_colors = json.loads(json_result.stdout)
                except Exception as e:
                    logger.error(f"Error parsing json colors: {e}")
                 
            logger.info(f"Theme extracted successfully with matugen (mode: {mode})")
            return True, "", extracted_colors
        except Exception as e:
            logger.error(f"Matugen failed: {str(e)}")
            return False, f"Error al generar tema con matugen: {str(e)}", {}
            
    def _reload_environment(self):
        # Reiniciar AGS
        try:
            logger.info("Reiniciando AGS...")
            # Intentar cerrar AGS elegantemente
            try:
                subprocess.run(["ags", "quit"], capture_output=True, timeout=5, env=self._get_clean_env())
                # Esperar hasta 3 segundos para que los plugins (ej. Spotify MPRIS) cierren limpiamente
                for _ in range(15):
                    if subprocess.run(["pgrep", "-x", "ags"], capture_output=True).returncode != 0:
                        break  # ags se cerró correctamente
                    time.sleep(0.2)
            except subprocess.TimeoutExpired:
                logger.warning("ags quit agotó el tiempo de espera, forzando cierre...")
            
            # Matar procesos restantes
            subprocess.run(["pkill", "-x", "ags"], capture_output=True, env=self._get_clean_env())
            
            # Pequeña espera para asegurar que el proceso anterior terminó y liberó el socket
            time.sleep(1.0)
            
            ags_app = os.path.expanduser("~/.config/ags/yuu/app.ts")
            default_config = os.path.expanduser("~/.config/ags/config.js")
            ags_script = os.path.expanduser("~/.config/ags/yuu/run_ags.sh")
            
            if os.path.exists(ags_app):
                logger.info(f"Iniciando AGS con app.ts: {ags_app}")
                subprocess.Popen(["ags", "run", ags_app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True, env=self._get_clean_env())
            elif os.path.exists(default_config):
                logger.info(f"Iniciando AGS con config.js: {default_config}")
                subprocess.Popen(["ags", "-c", default_config], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True, env=self._get_clean_env())
            elif os.path.exists(ags_script):
                logger.info(f"Iniciando AGS con script: {ags_script}")
                subprocess.Popen([ags_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True, env=self._get_clean_env())
            else:
                logger.info("Iniciando AGS por defecto")
                subprocess.Popen(["ags"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True, env=self._get_clean_env())
        except Exception as e:
            logger.error(f"Error al reiniciar AGS: {e}")
            
        # Matar proceso de Rofi en caso de que esté abierto con los colores viejos
        try:
            subprocess.run(["pkill", "rofi"], env=self._get_clean_env())
        except Exception:
            pass

    def apply_wallpaper(self, image_path, scheme_type="scheme-tonal-spot"):
        try:
            # 0. Ensure daemon is running
            self._ensure_daemon_running()

            # 1. Apply wallpaper with awww
            awww_cmd = ["awww", "img", str(image_path), "--transition-type", "outer", "--transition-pos", "0.854,0.977", "--transition-step", "90"]
            logger.info(f"Applying wallpaper: {' '.join(awww_cmd)}")
            result = subprocess.run(awww_cmd, capture_output=True, text=True, env=self._get_clean_env())
            
            if result.returncode != 0:
                return False, f"Error al aplicar el fondo:\n{result.stderr[-100:]}", {}
                
            # 2. Apply matugen theme
            theme_success, theme_err, colors = self._apply_theme(image_path, scheme_type)
            
            # 3. Reload UI elements
            self._reload_environment()
            
            if not theme_success:
                 return True, f"Fondo aplicado, pero falló la generación de color:\n{theme_err}", {}
                 
            return True, "Fondo y colores de sistema aplicados.", colors
            
        except Exception as e:
            logger.exception("Failed to execute wallpaper setup.")
            return False, str(e), {}
            
    def apply_only_wallpaper(self, image_path):
        try:
            # 0. Ensure daemon is running
            self._ensure_daemon_running()

            awww_cmd = ["awww", "img", str(image_path), "--transition-type", "outer", "--transition-pos", "0.854,0.977", "--transition-step", "90"]
            logger.info(f"Applying only wallpaper: {' '.join(awww_cmd)}")
            result = subprocess.run(awww_cmd, capture_output=True, text=True, env=self._get_clean_env())
            
            if result.returncode != 0:
                return False, f"Error al aplicar el fondo:\n{result.stderr[-100:]}", {}
            return True, "Fondo aplicado.", {}
        except Exception as e:
            logger.exception("Failed to execute only_wallpaper.")
            return False, str(e), {}

    def apply_only_colors(self, image_path, scheme_type="scheme-tonal-spot"):
        try:
            theme_success, theme_err, colors = self._apply_theme(image_path, scheme_type)
            self._reload_environment()
            if not theme_success:
                return False, f"Falló la generación de color:\n{theme_err}", {}
            return True, "Colores de sistema aplicados.", colors
        except Exception as e:
            logger.exception("Failed to execute only_colors.")
            return False, str(e), {}
            
    def apply_sddm_wallpaper(self, image_path, scheme_type="scheme-tonal-spot"):
        sddm_dir = Path("/usr/local/etc/sddm")
        if not sddm_dir.exists():
            return False, f"El directorio SDDM no existe en {sddm_dir}."
            
        try:
            # Clear SDDM dir
            for item in sddm_dir.glob('*'):
                if item.is_file() or item.is_symlink():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
                    
            # Copy image
            image_name = Path(image_path).name
            dest_image = sddm_dir / image_name
            shutil.copy2(image_path, dest_image)
            
            # Create symlink for background
            sddm_bg = sddm_dir / "sddm_background"
            if sddm_bg.exists() or sddm_bg.is_symlink():
                sddm_bg.unlink()
            sddm_bg.symlink_to(dest_image)
            
            # Run matugen for SDDM
            mode = self._get_matugen_mode()
            matugen_config_sddm = Path(os.path.expanduser("~/.config/matugen/config-sddm.toml"))
            
            matugen_cmd = ["matugen", "image", str(image_path), "-m", mode, "-t", scheme_type]
            if matugen_config_sddm.exists():
                matugen_cmd.extend(["-c", str(matugen_config_sddm)])
                
            matugen_cmd.extend(["--source-color-index", "0"])
            
            # Run matugen but do not check for exit codes (matches bash script behavior)
            subprocess.run(matugen_cmd, capture_output=True, text=True, cwd=os.path.expanduser("~"), env=self._get_clean_env())
            
            # Symlink colors
            colors_qml = sddm_dir / "Colors.qml"
            sddm_colors = sddm_dir / "sddm_config_colors"
            if sddm_colors.exists() or sddm_colors.is_symlink():
                sddm_colors.unlink()
            sddm_colors.symlink_to(colors_qml)
            
            return True, "Fondo de inicio de sesión cambiado.", {}
        except Exception as e:
            logger.exception("Failed to execute SDDM setup.")
            return False, f"Error configurando SDDM:\n{str(e)}", {}

    def get_colors(self, image_path, scheme_type="scheme-tonal-spot"):
        """Returns the matugen color dictionary for a given image without applying it."""
        success, err, colors = self._apply_theme(image_path, scheme_type)
        return colors if success else {}

