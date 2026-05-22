from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
import os

from repositories.usuario_repo import crear_usuario, obtener_usuarios


class PrimerUsuarioView(QWidget):
    """
    Pantalla que aparece solo cuando no hay ningún usuario en la BD.
    Permite crear el primer administrador.
    """
    usuario_creado = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Restaurante — Configuración inicial")
        self.setMinimumSize(520, 580)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Banner superior ──
        banner = QWidget()
        banner.setObjectName("banner")
        banner.setFixedHeight(140)
        banner_layout = QVBoxLayout(banner)
        banner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner_layout.setSpacing(6)

        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "assets", "logo.png")
        lbl_logo = QLabel()
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(
                60, 60,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            lbl_logo.setPixmap(pixmap)
        else:
            lbl_logo.setText("🍽")
            lbl_logo.setStyleSheet("font-size: 40px;")

        lbl_titulo = QLabel("Configuración Inicial")
        lbl_titulo.setObjectName("tituloBanner")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_sub = QLabel("Crea el primer usuario administrador para comenzar")
        lbl_sub.setObjectName("subBanner")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        banner_layout.addWidget(lbl_logo)
        banner_layout.addWidget(lbl_titulo)
        banner_layout.addWidget(lbl_sub)
        root.addWidget(banner)

        # ── Formulario ──
        contenido = QWidget()
        contenido.setObjectName("contenido")
        form_layout = QVBoxLayout(contenido)
        form_layout.setContentsMargins(60, 30, 60, 30)
        form_layout.setSpacing(14)

        # Nombre completo
        form_layout.addWidget(self._label("Nombre completo"))
        self.input_nombre = self._input("Ej: usuario")
        form_layout.addWidget(self.input_nombre)

        # Usuario
        form_layout.addWidget(self._label("Usuario"))
        self.input_usuario = self._input("Ej: admin")
        form_layout.addWidget(self.input_usuario)

        # Contraseña
        form_layout.addWidget(self._label("Contraseña"))
        self.input_contrasena = self._input("Mínimo 4 caracteres", password=True)
        form_layout.addWidget(self.input_contrasena)

        # Confirmar contraseña
        form_layout.addWidget(self._label("Confirmar contraseña"))
        self.input_confirmar = self._input("Repite la contraseña", password=True)
        form_layout.addWidget(self.input_confirmar)

        # Rol
        form_layout.addWidget(self._label("Rol"))
        self.combo_rol = QComboBox()
        self.combo_rol.addItems(["admin", "mesero"])
        self.combo_rol.setFixedHeight(42)
        form_layout.addWidget(self.combo_rol)

        # Error
        self.lbl_error = QLabel("")
        self.lbl_error.setObjectName("lblError")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.hide()
        form_layout.addWidget(self.lbl_error)

        form_layout.addSpacing(4)

        # Botón
        self.btn_crear = QPushButton("Crear usuario y continuar")
        self.btn_crear.setObjectName("btnCrear")
        self.btn_crear.setFixedHeight(46)
        self.btn_crear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_crear.clicked.connect(self._crear)
        form_layout.addWidget(self.btn_crear)

        root.addWidget(contenido)

    def _label(self, texto):
        lbl = QLabel(texto)
        lbl.setObjectName("labelCampo")
        return lbl

    def _input(self, placeholder, password=False):
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setObjectName("inputForm")
        inp.setFixedHeight(42)
        if password:
            inp.setEchoMode(QLineEdit.EchoMode.Password)
        return inp

    def _crear(self):
        nombre = self.input_nombre.text().strip()
        usuario = self.input_usuario.text().strip()
        contrasena = self.input_contrasena.text().strip()
        confirmar = self.input_confirmar.text().strip()
        rol = self.combo_rol.currentText()

        if not nombre or not usuario or not contrasena or not confirmar:
            self._error("⚠  Completa todos los campos.")
            return
        if len(contrasena) < 4:
            self._error("⚠  La contraseña debe tener al menos 4 caracteres.")
            return
        if contrasena != confirmar:
            self._error("✖  Las contraseñas no coinciden.")
            self.input_confirmar.clear()
            return

        try:
            crear_usuario(nombre, usuario, contrasena, rol)
            QMessageBox.information(
                self, "Listo",
                f"✅ Usuario '{usuario}' creado correctamente.\nYa puedes iniciar sesión."
            )
            self.usuario_creado.emit()
            self.close()
        except Exception as e:
            self._error(f"Error al crear usuario:\n{e}")

    def _error(self, msg):
        self.lbl_error.setText(msg)
        self.lbl_error.show()

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                font-family: 'Segoe UI', sans-serif;
                color: #cdd6f4;
            }
            #banner {
                background-color: #181825;
                border-bottom: 1px solid #313244;
            }
            #tituloBanner {
                font-size: 20px;
                font-weight: bold;
                color: #cba6f7;
            }
            #subBanner {
                font-size: 12px;
                color: #a6adc8;
            }
            #contenido {
                background-color: #1e1e2e;
            }
            #labelCampo {
                font-size: 12px;
                color: #a6adc8;
            }
            #inputForm {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 5px 12px;
                font-size: 14px;
            }
            #inputForm:focus {
                border: 1px solid #cba6f7;
            }
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 5px 12px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 1px solid #cba6f7;
            }
            #lblError {
                color: #f38ba8;
                font-size: 12px;
            }
            #btnCrear {
                background-color: #cba6f7;
                color: #1e1e2e;
                font-weight: bold;
                font-size: 15px;
                border-radius: 8px;
                border: none;
            }
            #btnCrear:hover {
                background-color: #b48ef0;
            }
            #btnCrear:pressed {
                background-color: #9a73e8;
            }
        """)
