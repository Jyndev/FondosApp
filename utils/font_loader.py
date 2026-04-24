import os
import io
import urllib.request
import zipfile
from pathlib import Path
from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtWidgets import QApplication

def load_custom_font(app: QApplication):
    font_dir = Path(os.path.expanduser("~/.local/share/fonts/fondos_app"))
    font_dir.mkdir(parents=True, exist_ok=True)
    
    font_path = font_dir / "Fredoka-Regular.ttf"
    
    if not font_path.exists():
        print("Downloading Fredoka font...")
        try:
            r = urllib.request.urlopen("https://fonts.google.com/download?family=Fredoka")
            with zipfile.ZipFile(io.BytesIO(r.read())) as z:
                # Find the regular ttf
                for name in z.namelist():
                    if 'Regular' in name and name.endswith('.ttf'):
                        with open(font_path, 'wb') as f:
                            f.write(z.read(name))
                        break
        except Exception as e:
            print(f"Error downloading font: {e}")
            return
            
    if font_path.exists():
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                custom_font = QFont(families[0])
                app.setFont(custom_font)
