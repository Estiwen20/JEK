from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QPushButton, QLabel, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from views.mesas_view import MesasView
from views.platos_view import PlatosView
from views.pedidos_view import PedidosView
from views.pago_view import PagoView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Restaurante — Administrador")
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

        self.nav_buttons = []
        nav_items = [
            ("🪑  Mesas",    0),
            ("🍲  Platos",   1),
            ("📋  Pedidos",  2),
            ("💳  Pagos",    3),
        ]
        for label, index in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("navBtn")
            btn.setFixedHeight(48)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, i=index: self._navigate(i))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        version = QLabel("v1.0.0")
        version.setObjectName("version")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setFixedHeight(36)
        sidebar_layout.addWidget(version)

        # ── Contenido ──
        self.stack = QStackedWidget()
        self.stack.addWidget(MesasView())
        self.stack.addWidget(PlatosView())
        self.stack.addWidget(PedidosView())
        self.stack.addWidget(PagoView())

        root.addWidget(self.sidebar)
        root.addWidget(self.stack)

        self._navigate(0)

    def _navigate(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

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
            QPushButton:hover {
                background-color: #45475a;
            }
            QPushButton:pressed {
                background-color: #cba6f7;
                color: #1e1e2e;
            }
            QTableWidget {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 6px;
                gridline-color: #313244;
            }
            QTableWidget::item:selected {
                background-color: #45475a;
            }
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
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #cba6f7;
            }
            QLabel {
                color: #cdd6f4;
            }
            QMessageBox {
                background-color: #1e1e2e;
            }
        """)