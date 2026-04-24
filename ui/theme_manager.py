from qt_material import apply_stylesheet

class ThemeManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            cls._instance.primary = "#ffb300"
            cls._instance.secondary = "#2c2c2c"
            cls._instance.surface = "#121212"
            cls._instance.surface_container = "#1e1e1e"
            cls._instance.surface_variant = "#2c2c2c"
            cls._instance.surface_bright = "#3a3a3a"
            cls._instance.on_surface = "#ffffff"
            cls._instance.on_surface_variant = "#cccccc"
            cls._instance.error = "#f44336"
            cls._instance.success = "#4caf50"
        return cls._instance

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls()
        return cls._instance

    def load_system_colors(self):
        """Attempts to dynamically fetch current system wallpaper from awww and load its matugen JSON palette"""
        try:
            import subprocess
            import json
            import os
            
            # Ensure daemon is running
            try:
                subprocess.run(["pgrep", "awww-daemon"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                subprocess.Popen(["awww-daemon"], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                import time
                time.sleep(1)
            
            # 1. Ask awww for current background using JSON
            result = subprocess.run(["awww", "query", "--json"], capture_output=True, text=True)
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    # Use the first monitor's image path
                    image_path = None
                    for namespace_outputs in data.values():
                        for output in namespace_outputs:
                            displaying = output.get("displaying", {})
                            if "image" in displaying:
                                image_path = displaying["image"]
                                break
                        if image_path: break
                    
                    if image_path and os.path.exists(image_path):
                        # Determine mode
                        mode = "dark"
                        try:
                            g_res = subprocess.run(["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"], capture_output=True, text=True)
                            if "prefer-dark" not in g_res.stdout:
                                mode = "light"
                        except: pass
                        
                        # Generate json dynamically with matugen
                        json_cmd = ["matugen", "image", str(image_path), "-m", mode, "-t", "scheme-tonal-spot", "-j", "hex", "--source-color-index", "0", "--dry-run"]
                        json_result = subprocess.run(json_cmd, capture_output=True, text=True, cwd=os.path.expanduser("~"))
                        if json_result.returncode == 0:
                            colors_dict = json.loads(json_result.stdout)
                            self.update_colors(colors_dict)
                            return True
                except Exception as e:
                    print(f"Error parsing awww query json: {e}")
        except Exception as e:
            print(f"Error loading system colors at startup: {e}")
        return False

    def update_colors(self, colors_dict):
        """
        Updates the colors parsing from matugen hex JSON
        `colors_dict` must follow the structure parsed from matugen.
        """
        mode = colors_dict.get("mode", "dark")
        
        try:
            colors = colors_dict.get("colors", {})
            if not colors:
                return

            def get_color(name, default):
                color_node = colors.get(name, {})
                mode_node = color_node.get(mode, color_node.get("default", {}))
                return mode_node.get("color", default)
            
            self.primary = get_color("primary", self.primary)
            self.surface = get_color("surface", self.surface)
            self.surface_container = get_color("surface_container", self.surface_container)
            self.surface_variant = get_color("surface_variant", self.surface_variant)
            self.surface_bright = get_color("surface_bright", self.surface_bright)
            self.on_surface = get_color("on_surface", self.on_surface)
            self.on_surface_variant = get_color("on_surface_variant", self.on_surface_variant)
            self.error = get_color("error", self.error)
            self.secondary = get_color("secondary_container", self.secondary)
            self.success = get_color("tertiary", self.success)
            
        except Exception as e:
            print(f"Error parsing colors: {e}")

    def apply_to_app(self, app):
        """
        Applies colors to the entire QApplication using qt_material
        """
        extra_colors = {
            'primaryColor': self.primary,
            'dangerColor': self.error,
        }
        apply_stylesheet(app, theme='dark_amber.xml', extra=extra_colors)
