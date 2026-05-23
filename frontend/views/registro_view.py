from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QMessageBox, QFormLayout
)
from PyQt6.QtCore import Qt

from backend.repositories.usuario_repo import crear_usuario


class RegistroDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear cuenta")
        self.setFixedSize(400, 480)
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(6)

        lbl_titulo = QLabel("Crear cuenta")
        lbl_titulo.setObjectName("tituloReg")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_titulo)

        lbl_sub = QLabel("Completa los datos para registrarte")
        lbl_sub.setObjectName("subReg")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_sub)

        layout.addSpacing(10)

        # Nombre
        layout.addWidget(self._label("Nombre completo"))
        self.input_nombre = self._input("Ej: María García")
        layout.addWidget(self.input_nombre)
        layout.addSpacing(8)

        # Usuario
        layout.addWidget(self._label("Usuario"))
        self.input_usuario = self._input("Ej: maria123")
        layout.addWidget(self.input_usuario)
        layout.addSpacing(8)

        # Contraseña
        layout.addWidget(self._label("Contraseña"))
        self.input_contrasena = self._input("Mínimo 4 caracteres", password=True)
        layout.addWidget(self.input_contrasena)
        layout.addSpacing(8)

        # Confirmar
        layout.addWidget(self._label("Confirmar contraseña"))
        self.input_confirmar = self._input("Repite la contraseña", password=True)
        layout.addWidget(self.input_confirmar)
        layout.addSpacing(8)

        # Rol
        layout.addWidget(self._label("Rol"))
        self.combo_rol = QComboBox()
        self.combo_rol.addItems(["mesero", "admin"])
        self.combo_rol.setFixedHeight(40)
        layout.addWidget(self.combo_rol)
        layout.addSpacing(8)

        # Error
        self.lbl_error = QLabel("")
        self.lbl_error.setObjectName("lblError")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.hide()
        layout.addWidget(self.lbl_error)

        layout.addSpacing(4)

        # Botones
        btns = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btnCancelar")
        btn_cancelar.setFixedHeight(40)
        btn_cancelar.clicked.connect(self.reject)

        btn_registrar = QPushButton("Registrarse")
        btn_registrar.setObjectName("btnRegistrar")
        btn_registrar.setFixedHeight(40)
        btn_registrar.clicked.connect(self._registrar)

        btns.addWidget(btn_cancelar)
        btns.addWidget(btn_registrar)
        layout.addLayout(btns)

    def _label(self, texto):
        lbl = QLabel(texto)
        lbl.setObjectName("labelCampo")
        return lbl

    def _input(self, placeholder, password=False):
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setObjectName("inputReg")
        inp.setFixedHeight(40)
        if password:
            inp.setEchoMode(QLineEdit.EchoMode.Password)
        return inp

    def _registrar(self):
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
                self, "Registro exitoso",
                f"✅ Cuenta '{usuario}' creada correctamente.\nYa puedes iniciar sesión."
            )
            self.accept()
        except Exception as e:
            if "UNIQUE" in str(e):
                self._error("✖  Ese nombre de usuario ya existe.")
            else:
                self._error(f"Error: {e}")

    def _error(self, msg):
        self.lbl_error.setText(msg)
        self.lbl_error.show()

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #1e1e2e;
                font-family: 'Segoe UI', sans-serif;
                color: #cdd6f4;
            }
            #tituloReg {
                font-size: 20px;
                font-weight: bold;
                color: #cba6f7;
            }
            #subReg {
                font-size: 12px;
                color: #585b70;
            }
            #labelCampo {
                font-size: 12px;
                color: #a6adc8;
                margin-bottom: 0px;
            }
            #inputReg {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 5px 12px;
                font-size: 13px;
            }
            #inputReg:focus {
                border: 1px solid #cba6f7;
            }
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 5px 12px;
                font-size: 13px;
            }
            QComboBox:focus { border: 1px solid #cba6f7; }
            #lblError {
                color: #f38ba8;
                font-size: 12px;
            }
            #btnRegistrar {
                background-color: #cba6f7;
                color: #1e1e2e;
                font-weight: bold;
                border-radius: 8px;
                border: none;
                padding: 8px 16px;
            }
            #btnRegistrar:hover { background-color: #b48ef0; }
            #btnCancelar {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 8px 16px;
            }
            #btnCancelar:hover { background-color: #45475a; }
        """)
