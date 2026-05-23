import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame,
    QStackedLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QPixmap

from backend.repositories.usuario_repo import obtener_usuario_por_credenciales
from frontend.views.registro_view import RegistroDialog


class LoginView(QWidget):
    login_exitoso = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Restaurante — Iniciar Sesión")
        self.setMinimumSize(900, 580)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Panel izquierdo: logo ocupa todo, texto abajo encima ──
        panel_izq = QWidget()
        panel_izq.setObjectName("panelIzq")

        stack_layout = QStackedLayout(panel_izq)
        stack_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)

        # Capa 1 — logo de fondo
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "assets", "logo.png")
        self.lbl_logo = QLabel()
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.lbl_logo.setScaledContents(True)
        if os.path.exists(logo_path):
            self.lbl_logo.setPixmap(QPixmap(logo_path))
        else:
            self.lbl_logo.setText("🍽")
            self.lbl_logo.setStyleSheet("font-size: 80px;")

        # Capa 2 — texto superpuesto abajo
        overlay = QWidget()
        overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        overlay.setStyleSheet("background: transparent;")
        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 24)
        overlay_layout.addStretch()

        lbl_nombre = QLabel("Restaurante")
        lbl_nombre.setObjectName("nombreEmpresa")
        lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_slogan = QLabel("Sistema de Administración")
        lbl_slogan.setObjectName("slogan")
        lbl_slogan.setAlignment(Qt.AlignmentFlag.AlignCenter)

        overlay_layout.addWidget(lbl_nombre)
        overlay_layout.addWidget(lbl_slogan)

        stack_layout.addWidget(self.lbl_logo)
        stack_layout.addWidget(overlay)

        # ── Panel derecho (formulario) ──
        panel_der = QWidget()
        panel_der.setObjectName("panelDer")
        der_layout = QVBoxLayout(panel_der)
        der_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        der_layout.setContentsMargins(60, 60, 60, 60)
        der_layout.setSpacing(0)

        self.card = QFrame()
        self.card.setObjectName("loginCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(18)

        lbl_titulo = QLabel("Iniciar Sesión")
        lbl_titulo.setObjectName("tituloLogin")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl_titulo)

        lbl_sub = QLabel("Ingresa tus credenciales para continuar")
        lbl_sub.setObjectName("subLogin")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl_sub)

        card_layout.addSpacing(10)

        lbl_user = QLabel("Usuario")
        lbl_user.setObjectName("labelCampo")
        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Ingresa tu usuario")
        self.input_usuario.setObjectName("inputLogin")
        self.input_usuario.setFixedHeight(42)
        card_layout.addWidget(lbl_user)
        card_layout.addWidget(self.input_usuario)

        lbl_pass = QLabel("Contraseña")
        lbl_pass.setObjectName("labelCampo")
        self.input_contrasena = QLineEdit()
        self.input_contrasena.setPlaceholderText("Ingresa tu contraseña")
        self.input_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_contrasena.setObjectName("inputLogin")
        self.input_contrasena.setFixedHeight(42)
        self.input_contrasena.returnPressed.connect(self._intentar_login)
        card_layout.addWidget(lbl_pass)
        card_layout.addWidget(self.input_contrasena)

        self.lbl_error = QLabel("")
        self.lbl_error.setObjectName("lblError")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.hide()
        card_layout.addWidget(self.lbl_error)

        card_layout.addSpacing(6)

        self.btn_login = QPushButton("Ingresar")
        self.btn_login.setObjectName("btnLogin")
        self.btn_login.setFixedHeight(46)
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.clicked.connect(self._intentar_login)
        card_layout.addWidget(self.btn_login)

        btn_registro = QPushButton("¿No tienes cuenta? Regístrate")
        btn_registro.setObjectName("btnRegistro")
        btn_registro.setFixedHeight(36)
        btn_registro.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_registro.clicked.connect(self._abrir_registro)
        card_layout.addWidget(btn_registro)

        der_layout.addWidget(self.card)

        root.addWidget(panel_izq, stretch=1)
        root.addWidget(panel_der, stretch=1)

    def _intentar_login(self):
        usuario = self.input_usuario.text().strip()
        contrasena = self.input_contrasena.text().strip()

        if not usuario or not contrasena:
            self._mostrar_error("⚠  Completa todos los campos.")
            return

        user = obtener_usuario_por_credenciales(usuario, contrasena)
        if user:
            self.lbl_error.hide()
            self.login_exitoso.emit(user)
        else:
            self._mostrar_error("✖  Usuario o contraseña incorrectos.")
            self.input_contrasena.clear()
            self._shake()

    def _abrir_registro(self):
        dialog = RegistroDialog(self)
        dialog.exec()

    def _mostrar_error(self, msg):
        self.lbl_error.setText(msg)
        self.lbl_error.show()

    def _shake(self):
        pos_orig = self.card.pos()
        anim = QPropertyAnimation(self.card, b"pos")
        anim.setDuration(300)
        anim.setKeyValueAt(0,    pos_orig)
        anim.setKeyValueAt(0.15, pos_orig + QPoint(-10, 0))
        anim.setKeyValueAt(0.30, pos_orig + QPoint(10, 0))
        anim.setKeyValueAt(0.45, pos_orig + QPoint(-8, 0))
        anim.setKeyValueAt(0.60, pos_orig + QPoint(8, 0))
        anim.setKeyValueAt(0.75, pos_orig + QPoint(-4, 0))
        anim.setKeyValueAt(1.0,  pos_orig)
        anim.setEasingCurve(QEasingCurve.Type.Linear)
        self._anim_shake = anim
        anim.start()

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                font-family: 'Segoe UI', sans-serif;
            }
            #panelIzq {
                background-color: #ffffff;
                border-right: 1px solid #313244;
            }
            #nombreEmpresa {
                font-size: 26px;
                font-weight: bold;
                color: #000000;
            }
            #slogan {
                font-size: 13px;
                color: #333333;
            }
            #panelDer {
                background-color: #1e1e2e;
            }
            #loginCard {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 16px;
            }
            #tituloLogin {
                font-size: 22px;
                font-weight: bold;
                color: #cdd6f4;
            }
            #subLogin {
                font-size: 12px;
                color: #585b70;
            }
            #labelCampo {
                font-size: 12px;
                color: #a6adc8;
                margin-bottom: 2px;
            }
            #inputLogin {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 5px 12px;
                font-size: 14px;
            }
            #inputLogin:focus {
                border: 1px solid #cba6f7;
            }
            #lblError {
                color: #f38ba8;
                font-size: 12px;
            }
            #btnLogin {
                background-color: #cba6f7;
                color: #1e1e2e;
                font-weight: bold;
                font-size: 15px;
                border-radius: 8px;
                border: none;
            }
            #btnLogin:hover { background-color: #b48ef0; }
            #btnLogin:pressed { background-color: #9a73e8; }
            #btnRegistro {
                background: transparent;
                color: #a6adc8;
                border: none;
                font-size: 12px;
            }
            #btnRegistro:hover { color: #cba6f7; }
        """)
