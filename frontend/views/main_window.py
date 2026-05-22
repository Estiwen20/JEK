from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QPushButton, QLabel, QStackedWidget, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from frontend.views.mesas_view import MesasView
from frontend.views.platos_view import PlatosView
from frontend.views.pedidos_view import PedidosView
from frontend.views.pago_view import PagoView


class MainWindow(QMainWindow):
    cerrar_sesion = pyqtSignal()  # señal para volver al login

    def __init__(self, usuario):
        super().__init__()
        self.usuario = usuario
        self.setWindowTitle(f"Restaurante — {usuario.nombre} ({usuario.rol.capitalize()})")
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
        self.sidebar.setFixedWidth(200)
        self.sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        logo = QLabel("🍽  Restaurante")
        logo.setObjectName("logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedHeight(70)
        sidebar_layout.addWidget(logo)

        # Info usuario
        lbl_user = QLabel(f"👤  {self.usuario.nombre}")
        lbl_user.setObjectName("lblUser")
        lbl_user.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_user.setFixedHeight(30)
        lbl_rol = QLabel(f"{'🔑 Administrador' if self.usuario.es_admin() else '🧑‍🍳 Mesero'}")
        lbl_rol.setObjectName("lblRol")
        lbl_rol.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_rol.setFixedHeight(24)
        sidebar_layout.addWidget(lbl_user)
        sidebar_layout.addWidget(lbl_rol)

        # Separador
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #313244;")
        sidebar_layout.addWidget(sep)

        self.nav_buttons = []
        self.stack = QStackedWidget()

        # Definir vistas según rol
        # mesero: solo Pedidos
        # admin: Mesas, Platos, Pedidos, Pagos
        if self.usuario.es_admin():
            nav_items = [
                ("🪑  Mesas",   MesasView()),
                ("🍲  Platos",  PlatosView()),
                ("📋  Pedidos", PedidosView()),
                ("💳  Pagos",   PagoView()),
            ]
        else:
            nav_items = [
                ("📋  Pedidos", PedidosView()),
            ]

        for i, (label, vista) in enumerate(nav_items):
            btn = QPushButton(label)
            btn.setObjectName("navBtn")
            btn.setFixedHeight(48)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, idx=i: self._navigate(idx))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)
            self.stack.addWidget(vista)

        sidebar_layout.addStretch()

        # Botón cerrar sesión
        btn_logout = QPushButton("🚪  Cerrar Sesión")
        btn_logout.setObjectName("btnLogout")
        btn_logout.setFixedHeight(40)
        btn_logout.clicked.connect(self._logout)
        sidebar_layout.addWidget(btn_logout)

        version = QLabel("v1.0.0")
        version.setObjectName("version")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setFixedHeight(36)
        sidebar_layout.addWidget(version)

        root.addWidget(self.sidebar)
        root.addWidget(self.stack)

        self._navigate(0)

    def _navigate(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

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
                border-right: 1px solid #313244;
            }
            #logo {
                font-size: 15px;
                font-weight: bold;
                color: #cba6f7;
                border-bottom: 1px solid #313244;
            }
            #lblUser {
                font-size: 12px;
                color: #cdd6f4;
                font-weight: bold;
                padding-top: 8px;
            }
            #lblRol {
                font-size: 11px;
                color: #a6adc8;
                padding-bottom: 8px;
            }
            #navBtn {
                background: transparent;
                color: #a6adc8;
                border: none;
                text-align: left;
                padding-left: 24px;
                font-size: 13px;
                border-radius: 0;
            }
            #navBtn:hover {
                background-color: #313244;
                color: #cdd6f4;
            }
            #navBtn:checked {
                background-color: #313244;
                color: #cba6f7;
                border-left: 3px solid #cba6f7;
            }
            #btnLogout {
                background: transparent;
                color: #f38ba8;
                border: none;
                border-top: 1px solid #313244;
                font-size: 12px;
                border-radius: 0;
            }
            #btnLogout:hover {
                background-color: #3a1e1e;
            }
            #version {
                color: #585b70;
                font-size: 11px;
            }
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
                gridline-color: #313244;
            }
            QTableWidget::item:selected { background-color: #45475a; }
            QHeaderView::section {
                background-color: #313244;
                color: #cba6f7;
                border: none;
                padding: 6px;
                font-weight: bold;
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
        """)
