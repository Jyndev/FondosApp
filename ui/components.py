from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QDialog, QPushButton, QGraphicsDropShadowEffect
from PySide6.QtGui import QPixmap, QCursor, QColor
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from ui.theme_manager import ThemeManager

class CustomAlert(QDialog):
    def __init__(self, title, message, is_error=False, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(400, 200)

        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Container to hold styles
        container = QFrame(self)
        container.setObjectName("alertContainer")
        
        # Drop shadow for modern look
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        # Style depending on type
        theme = ThemeManager.get_instance()
        accent_color = theme.error if is_error else theme.success
        
        container.setStyleSheet(f"""
            QFrame#alertContainer {{
                background-color: {theme.surface_container};
                border-radius: 12px;
                border-left: 6px solid {accent_color};
            }}
            QLabel#alertTitle {{
                color: {theme.on_surface};
                font-size: 20px;
                font-weight: bold;
            }}
            QLabel#alertMessage {{
                color: {theme.on_surface_variant};
                font-size: 14px;
            }}
            QPushButton#alertBtn {{
                background-color: {accent_color};
                color: {theme.surface};
                border-radius: 6px;
                padding: 8px 24px;
                font-weight: bold;
            }}
            QPushButton#alertBtn:hover {{
                background-color: {theme.surface_variant};
                border: 2px solid {accent_color};
                color: {accent_color};
            }}
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(10)
        
        lbl_title = QLabel(title)
        lbl_title.setObjectName("alertTitle")
        
        lbl_message = QLabel(message)
        lbl_message.setObjectName("alertMessage")
        lbl_message.setWordWrap(True)
        lbl_message.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("ACEPTAR")
        btn_ok.setObjectName("alertBtn")
        btn_ok.setCursor(QCursor(Qt.PointingHandCursor))
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        
        container_layout.addWidget(lbl_title)
        container_layout.addWidget(lbl_message)
        container_layout.addStretch()
        container_layout.addLayout(btn_layout)
        
        layout.addWidget(container)
        
        # Add simple pop animation
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(250)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()

def show_error_dialog(text, title="Error"):
    # Determinamos si es un error basado en el título para decidir el color (Rojo/Verde)
    is_error = title.lower() != "cambio exitoso"
    alert = CustomAlert(title, text, is_error=is_error)
    alert.exec()

class ImageItem(QFrame):
    clicked = Signal(str)

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.is_selected = False
        
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        # Fix size
        self.setFixedSize(200, 200)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        # setScaledContents(True) causes the QLabel to stretch the image, ignoring aspect ratio.
        self.image_label.setScaledContents(False)

        layout.addWidget(self.image_label)
        self.setLayout(layout)
        self._apply_style()

    def _apply_style(self):
        theme = ThemeManager.get_instance()
        if self.is_selected:
            color = theme.primary
            border_width = "3px"
            bg_color = theme.surface_variant
        else:
            color = theme.surface_container
            border_width = "1px"
            bg_color = theme.surface_container
            
        self.setStyleSheet(f"""
            ImageItem {{
                background-color: {bg_color};
                border: {border_width} solid {color};
                border-radius: 8px;
            }}
        """)

    def set_thumbnail(self, pixmap_path):
        pixmap = QPixmap(pixmap_path)
        self.image_label.setPixmap(pixmap.scaled(
            190, 190, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def set_selected(self, selected=True):
        self.is_selected = selected
        self._apply_style()

    def enterEvent(self, event):
        theme = ThemeManager.get_instance()
        if not self.is_selected:
            self.setStyleSheet(f"""
                ImageItem {{
                    background-color: {theme.surface_bright};
                    border: 1px solid {theme.primary};
                    border-radius: 8px;
                }}
            """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.image_path)
