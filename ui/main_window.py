import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QScrollArea, QGridLayout, QFileDialog, QSizePolicy, QFrame
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from ui.theme_manager import ThemeManager
from ui.components import ImageItem, show_error_dialog
from services.image_loader import ImageLoader
from services.wallpaper_service import WallpaperService
from utils.config import AppConfig

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hyprland Material Wallpaper")
        self.setMinimumSize(970, 651)
        self.resize(970, 651)
        
        self.config = AppConfig()
        self.image_loader = ImageLoader()
        self.image_loader.thumbnail_ready.connect(self.on_thumbnail_ready)
        self.wallpaper_service = WallpaperService()
        
        self.selected_image_path = ""
        self.image_widgets = {}
        
        self.init_ui()

    def init_ui(self):
        self.setObjectName("MainWindow")
        main_layout = QVBoxLayout(self)
        
        # Top Bar
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(10, 10, 10, 20)
        self.lbl_main_title = QLabel("Hyprland Material Wallpaper")
        self.lbl_main_title.setProperty("class", "h1")
        
        top_bar.addWidget(self.lbl_main_title)
        
        main_layout.addLayout(top_bar)
        
        # Content layout (Left: Grid, Right: Preview)
        content_layout = QHBoxLayout()
        
        # Scroll Area for Grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName("scrollWidget")
        self.grid_layout = QGridLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        
        content_layout.addWidget(self.scroll_area, 7) # 70% width
        
        # Preview Panel
        self.preview_widget = QFrame()
        self.preview_widget.setStyleSheet("QFrame { background-color: #1e1e1e; border-radius: 12px; }")
        preview_panel = QVBoxLayout(self.preview_widget)
        preview_panel.setContentsMargins(20, 20, 20, 20)
        
        self.lbl_preview_title = QLabel("Vista Previa")
        self.lbl_preview_title.setAlignment(Qt.AlignCenter)
        self.lbl_preview_title.setProperty("class", "h2")
        
        self.lbl_preview_image = QLabel()
        self.lbl_preview_image.setAlignment(Qt.AlignCenter)
        self.lbl_preview_image.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl_preview_image.setMinimumSize(250, 250)
        
        self.lbl_selected_name = QLabel("Ninguna imagen seleccionada")
        self.lbl_selected_name.setAlignment(Qt.AlignCenter)
        self.lbl_selected_name.setStyleSheet("color: #cccccc;")
        self.lbl_selected_name.setWordWrap(True)
        
        preview_panel.addWidget(self.lbl_preview_title)
        preview_panel.addWidget(self.lbl_preview_image, 1)
        preview_panel.addWidget(self.lbl_selected_name)
        
        # Action Buttons Layout
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(10)
        
        button_style = """
            QPushButton {
                background-color: #2c2c2c; 
                color: #ffffff; 
                border: 1px solid #444444; 
                padding: 10px; 
                border-radius: 8px; 
                font-weight: bold;
            }
            QPushButton:hover { background-color: #383838; border: 1px solid #666666; }
            QPushButton:disabled { background-color: #1a1a1a; color: #555555; border: 1px solid #333333; }
        """
        
        self.btn_apply_all = QPushButton("APLICAR TODO")
        self.btn_apply_all.setCursor(Qt.PointingHandCursor)
        self.btn_apply_all.clicked.connect(self.apply_wallpaper)
        self.btn_apply_all.setEnabled(False)
        actions_layout.addWidget(self.btn_apply_all)
        
        self.btn_only_wall = QPushButton("SOLO FONDO")
        self.btn_only_wall.setStyleSheet(button_style)
        self.btn_only_wall.setCursor(Qt.PointingHandCursor)
        self.btn_only_wall.clicked.connect(self.apply_only_wallpaper)
        self.btn_only_wall.setEnabled(False)
        actions_layout.addWidget(self.btn_only_wall)

        self.btn_only_colors = QPushButton("SOLO COLORES")
        self.btn_only_colors.setStyleSheet(button_style)
        self.btn_only_colors.setCursor(Qt.PointingHandCursor)
        self.btn_only_colors.clicked.connect(self.apply_only_colors)
        self.btn_only_colors.setEnabled(False)
        actions_layout.addWidget(self.btn_only_colors)

        self.btn_sddm = QPushButton("FONDO SDDM")
        self.btn_sddm.setStyleSheet(button_style)
        self.btn_sddm.setCursor(Qt.PointingHandCursor)
        self.btn_sddm.clicked.connect(self.apply_sddm_wallpaper)
        self.btn_sddm.setEnabled(False)
        actions_layout.addWidget(self.btn_sddm)
        
        preview_panel.addLayout(actions_layout)
        preview_panel.addStretch()
        
        content_layout.addWidget(self.preview_widget, 3) # 30% width
        
        main_layout.addLayout(content_layout)

        # Bottom Bar (Directory Label + Open Button)
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(10, 20, 10, 10)
        
        self.lbl_bottom_dir = QLabel("Último directorio de fondos: Ninguno")
        self.lbl_bottom_dir.setStyleSheet("color: #888888; font-size: 14px;")
        
        self.btn_open = QPushButton("Abrir carpeta")
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_open.clicked.connect(self.open_folder)
        
        bottom_bar.addWidget(self.lbl_bottom_dir)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self.btn_open)
        
        main_layout.addLayout(bottom_bar)
        self._apply_dynamic_styles()

    def _apply_dynamic_styles(self):
        theme = ThemeManager.get_instance()
        
        self.setStyleSheet(f"QWidget#MainWindow {{ background-color: {theme.surface}; }}")
        self.scroll_area.setStyleSheet(f"QScrollArea {{ background-color: transparent; border: none; }} QWidget#scrollWidget {{ background-color: transparent; }}")
        
        if hasattr(self, 'preview_widget'):
            self.preview_widget.setStyleSheet(f"QFrame {{ background-color: {theme.surface_variant}; border-radius: 12px; }}")

        self.lbl_main_title.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {theme.primary};")
        
        disabled_bg = theme.surface_container
        disabled_fg = theme.on_surface_variant
        
        self.btn_apply_all.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.primary}; color: {theme.surface}; 
                border: none; padding: 12px; border-radius: 8px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {theme.primary}dd; }}
            QPushButton:disabled {{ background-color: {disabled_bg}; color: {disabled_fg}; }}
        """)
        
        if hasattr(self, 'btn_open'):
             self.btn_open.setStyleSheet(f"background-color: {theme.primary}; color: {theme.surface}; border: none; padding: 6px 16px; border-radius: 4px; font-weight: bold; text-transform: none;")
             
        for widget in self.image_widgets.values():
            widget._apply_style()

    def _reload_ui_styles(self):
        theme = ThemeManager.get_instance()
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            theme.apply_to_app(app)
        self._apply_dynamic_styles()

    def open_folder(self):
        last_folder = self.config.get_last_folder()
        if not os.path.exists(last_folder):
            last_folder = os.path.expanduser("~/Pictures")
            
        folder_path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta", last_folder)
        if folder_path:
            self.config.set_last_folder(folder_path)
            self.load_images(folder_path)

    def load_images(self, folder_path):
        # Clear grid
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
                
        self.image_widgets.clear()
        self.selected_image_path = None
        self.lbl_preview_image.clear()
        self.lbl_selected_name.setText("Cargando imágenes...")
        
        self.btn_apply_all.setEnabled(False)
        self.btn_only_wall.setEnabled(False)
        self.btn_only_colors.setEnabled(False)
        self.btn_sddm.setEnabled(False)
        
        self.lbl_main_title.setText("Hyprland Material Wallpaper")
        
        images = self.image_loader.get_images_in_folder(folder_path)
        if not images:
            self.lbl_selected_name.setText("Carpeta vacía.")
            self.lbl_bottom_dir.setText(f"Último directorio de fondos: {folder_path} (Vacía)")
            return
            
        self.lbl_selected_name.setText("Ninguna imagen seleccionada")
        self.lbl_bottom_dir.setText(f"Último directorio de fondos: {folder_path}")
        
        # Populate grid
        cols = 3
        for idx, img_path in enumerate(images):
            item = ImageItem(img_path)
            item.clicked.connect(self.on_image_selected)
            self.image_widgets[img_path] = item
            
            row = idx // cols
            col = idx % cols
            self.grid_layout.addWidget(item, row, col)
            
            self.image_loader.request_thumbnail(img_path)

    def on_thumbnail_ready(self, thumb_path, original_path):
        if thumb_path and original_path in self.image_widgets:
            self.image_widgets[original_path].set_thumbnail(thumb_path)

    def on_image_selected(self, image_path):
        if self.selected_image_path and self.selected_image_path in self.image_widgets:
            self.image_widgets[self.selected_image_path].set_selected(False)
            
        self.selected_image_path = image_path
        self.lbl_selected_name.setText(os.path.basename(image_path))
        
        if image_path in self.image_widgets:
            self.image_widgets[image_path].set_selected(True)
            
        # Enable all action buttons
        self.btn_apply_all.setEnabled(True)
        self.btn_only_wall.setEnabled(True)
        self.btn_only_colors.setEnabled(True)
        self.btn_sddm.setEnabled(True)
        
        # Show preview
        pixmap = QPixmap(image_path)
        self.lbl_preview_image.setPixmap(pixmap.scaled(
            self.lbl_preview_image.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        ))

    def load_initial_folder(self):
        last_folder = self.config.get_last_folder()
        if os.path.exists(last_folder):
            self.load_images(last_folder)

    def _handle_action_result(self, success, message):
        if success:
            show_error_dialog(message, "Cambio Exitoso")
        else:
            show_error_dialog(message, "Error")

    def apply_wallpaper(self):
        if not self.selected_image_path: return
        success, msg, colors = self.wallpaper_service.apply_wallpaper(self.selected_image_path)
        if success and colors:
            ThemeManager.get_instance().update_colors(colors)
            self._reload_ui_styles()
        self._handle_action_result(success, msg)
        
    def apply_only_wallpaper(self):
        if not self.selected_image_path: return
        success, msg, colors = self.wallpaper_service.apply_only_wallpaper(self.selected_image_path)
        self._handle_action_result(success, msg)

    def apply_only_colors(self):
        if not self.selected_image_path: return
        success, msg, colors = self.wallpaper_service.apply_only_colors(self.selected_image_path)
        if success and colors:
            ThemeManager.get_instance().update_colors(colors)
            self._reload_ui_styles()
        self._handle_action_result(success, msg)
        
    def apply_sddm_wallpaper(self):
        if not self.selected_image_path: return
        success, msg, colors = self.wallpaper_service.apply_sddm_wallpaper(self.selected_image_path)
        self._handle_action_result(success, msg)
