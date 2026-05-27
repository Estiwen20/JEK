import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QPushButton, QLabel, QStackedWidget,
    QMessageBox, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QColor

from frontend.views.mesas_view import MesasView
from frontend.views.platos_view import PlatosView
from frontend.views.pedidos_view import PedidosView
from frontend.views.pago_view import PagoView
from frontend.views.dashboard_view import DashboardView


class AnimatedNavBtn(QPushButton):
    def __init__(self, label, parent=None):
        super().__init__(label, parent)
        self.setObjectName("navBtn")
        self.setFixedHeight(48)
        self.setCheckable(True)

    def enterEvent(self, event):
        if not self.isChecked():
            self.setStyleSheet(self.styleSheet())
        super().enterEvent(event)


class MainWindow(QMainWindow):
    cerrar_sesion = pyqtSignal()

    def __init__(self, usuario):
        super().__init__()
        self.usuario = usuario
        self.setWindowTitle(
            f"Restaurante — {usuario.nombre} ({usuario.rol.capitalize()})"
        )
        self.setMinimumSize(1100, 680)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(210)
        self.sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # ── Logo ──
        logo_container = QFrame()
        logo_container.setObjectName("logoContainer")
        logo_container.setFixedHeight(190)
        logo_inner = QVBoxLayout(logo_container)
        logo_inner.setContentsMargins(20, 16, 20, 16)
        logo_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo = QLabel()
        logo.setObjectName("logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setScaledContents(False)
        logo_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "assets", "logo.png"
        )
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(
                150, 150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo.setPixmap(pixmap)
        else:
            logo.setText("🍽  Restaurante")

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 80))
        logo.setGraphicsEffect(shadow)

        logo_inner.addWidget(logo)
        sidebar_layout.addWidget(logo_container)

        sep_top = QFrame()
        sep_top.setObjectName("sepDeco")
        sep_top.setFixedHeight(2)
        sidebar_layout.addWidget(sep_top)

        # ── Usuario ──
        user_frame = QFrame()
        user_frame.setObjectName("userFrame")
        user_layout = QVBoxLayout(user_frame)
        user_layout.setContentsMargins(12, 8, 12, 8)
        user_layout.setSpacing(2)

        lbl_user = QLabel(f"👤  {self.usuario.nombre}")
        lbl_user.setObjectName("lblUser")
        lbl_user.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_rol = QLabel(
            f"{'🔑 Administrador' if self.usuario.es_admin() else '🧑‍🍳 Mesero'}"
        )
        lbl_rol.setObjectName("lblRol")
        lbl_rol.setAlignment(Qt.AlignmentFlag.AlignCenter)

        user_layout.addWidget(lbl_user)
        user_layout.addWidget(lbl_rol)
        sidebar_layout.addWidget(user_frame)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #313244; margin: 0 12px;")
        sidebar_layout.addWidget(sep)

        sidebar_layout.addSpacing(6)

        self.nav_buttons = []
        self.stack = QStackedWidget()

        # ── Vistas según rol ──
        if self.usuario.es_admin():
            nav_items = [
                ("📊  Dashboard", DashboardView()),
                ("🪑  Mesas",     MesasView(self.usuario)),
                ("🍲  Platos",    PlatosView(self.usuario)),
                ("📋  Pedidos",   PedidosView(self.usuario)),
                ("💳  Pagos",     PagoView(self.usuario)),
            ]
        else:
            nav_items = [
                ("🪑  Mesas",     MesasView(self.usuario)),
                ("🍲  Platos",    PlatosView(self.usuario)),
                ("📋  Pedidos",   PedidosView(self.usuario)),
                ("💳  Pagos",     PagoView(self.usuario)),
            ]

        for i, (label, vista) in enumerate(nav_items):
            btn = AnimatedNavBtn(label)
            btn.clicked.connect(lambda _, idx=i: self._navigate(idx))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)
            self.stack.addWidget(vista)

        sidebar_layout.addStretch()

        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background-color: #313244;")
        sidebar_layout.addWidget(sep2)

        btn_logout = QPushButton("🚪  Cerrar Sesión")
        btn_logout.setObjectName("btnLogout")
        btn_logout.setFixedHeight(42)
        btn_logout.clicked.connect(self._logout)
        sidebar_layout.addWidget(btn_logout)

        version = QLabel("v1.0.0")
        version.setObjectName("version")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setFixedHeight(30)
        sidebar_layout.addWidget(version)

        root.addWidget(self.sidebar)
        root.addWidget(self.stack)

        self._navigate(0)

    def _navigate(self, index):
        current = self.stack.currentWidget()
        self.stack.setCurrentIndex(index)
        new = self.stack.currentWidget()

        # Animación fade
        if new and new != current:
            anim = QPropertyAnimation(new, b"windowOpacity")
            anim.setDuration(180)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._nav_anim = anim
            anim.start()

        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

        # ← Esto es lo que faltaba — refrescar dashboard al entrar
        widget = self.stack.currentWidget()
        if hasattr(widget, "refrescar"):
            widget.refrescar()

    def _logout(self):
        confirmar = QMessageBox.question(
            self, "Cerrar sesión",
            "¿Seguro que quieres cerrar sesión?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            self.cerrar_sesion.emit()
            self.close()

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            #sidebar {
                background-color: #181825;
                border-right: 1px solid #2a2a3e;
            }
            #logoContainer {
                background-color: #181825;
                border-bottom: none;
                padding: 0;
            }
            #logo {
                background: transparent;
                border: none;
            }
            #sepDeco {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent,
                    stop:0.3 #cba6f7,
                    stop:0.7 #cba6f7,
                    stop:1 transparent
                );
                margin: 0 24px;
                border: none;
            }
            #userFrame { background: transparent; }
            #lblUser { font-size: 12px; color: #cdd6f4; font-weight: bold; }
            #lblRol { font-size: 11px; color: #a6adc8; }
            #navBtn {
                background: transparent;
                color: #a6adc8;
                border: none;
                border-left: 3px solid transparent;
                text-align: left;
                padding-left: 20px;
                font-size: 13px;
                border-radius: 0;
            }
            #navBtn:hover {
                background-color: #252535;
                color: #cdd6f4;
                border-left: 3px solid #6c6c8a;
            }
            #navBtn:checked {
                background-color: #2a2a42;
                color: #cba6f7;
                border-left: 3px solid #cba6f7;
                font-weight: bold;
            }
            #btnLogout {
                background: transparent;
                color: #f38ba8;
                border: none;
                font-size: 12px;
                border-radius: 0;
                text-align: left;
                padding-left: 20px;
            }
            #btnLogout:hover { background-color: #2e1e26; color: #ff9ab2; }
            #version { color: #45475a; font-size: 10px; }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px 16px;
            }
            QPushButton:hover { background-color: #45475a; }
            QPushButton:pressed { background-color: #cba6f7; color: #1e1e2e; }
            QTableWidget {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 6px;
                gridline-color: #252535;
            }
            QTableWidget::item:selected { background-color: #2a2a42; color: #cba6f7; }
            QHeaderView::section {
                background-color: #252535;
                color: #cba6f7;
                border: none;
                border-bottom: 1px solid #313244;
                padding: 7px;
                font-weight: bold;
                font-size: 12px;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 5px 10px;
            }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #cba6f7; }
            QLabel { color: #cdd6f4; }
            QMessageBox { background-color: #1e1e2e; }
            QScrollBar:vertical {
                background: #181825; width: 6px; border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #45475a; border-radius: 3px; min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: #cba6f7; }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0; }
        """)