from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDialog, QFormLayout, QSpinBox,
    QComboBox, QMessageBox, QScrollArea, QGridLayout,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont

from repositories.mesa_repo import (
    crear_mesa, obtener_mesas,
    actualizar_mesa, eliminar_mesa
)


COLORES_ESTADO = {
    "disponible":    {"fondo": "#1e3a2f", "borde": "#a6e3a1", "texto": "#a6e3a1", "badge": "#a6e3a1", "badge_txt": "#1e3a2f"},
    "ocupada":       {"fondo": "#3a1e1e", "borde": "#f38ba8", "texto": "#f38ba8", "badge": "#f38ba8", "badge_txt": "#3a1e1e"},
    "reservada":     {"fondo": "#2a2a1e", "borde": "#f9e2af", "texto": "#f9e2af", "badge": "#f9e2af", "badge_txt": "#2a2a1e"},
    "mantenimiento": {"fondo": "#252535", "borde": "#45475a", "texto": "#a6adc8", "badge": "#45475a", "badge_txt": "#cdd6f4"},
}

ICONOS_CAPACIDAD = {2: "🪑", 4: "🍽", 6: "🍽", 8: "🏮"}


class MesaCard(QFrame):
    def __init__(self, mesa, on_select, parent=None):
        super().__init__(parent)
        self.mesa = mesa
        self.on_select = on_select
        self.seleccionada = False
        self.setFixedSize(120, 130)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_ui()

    def _build_ui(self):
        colores = COLORES_ESTADO.get(self.mesa.estado, COLORES_ESTADO["disponible"])
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colores['fondo']};
                border: 2px solid {colores['borde']};
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icono = ICONOS_CAPACIDAD.get(self.mesa.capacidad, "🍽")
        lbl_icono = QLabel(icono)
        lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icono.setStyleSheet("font-size: 26px; border: none; background: transparent;")

        lbl_num = QLabel(f"Mesa #{self.mesa.numero}")
        lbl_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_num.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {colores['texto']}; border: none; background: transparent;")

        lbl_cap = QLabel(f"{self.mesa.capacidad} personas")
        lbl_cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_cap.setStyleSheet(f"font-size: 10px; color: {colores['texto']}; opacity: 0.7; border: none; background: transparent;")

        lbl_estado = QLabel(self.mesa.estado.capitalize())
        lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_estado.setStyleSheet(f"""
            font-size: 10px;
            font-weight: bold;
            color: {colores['badge_txt']};
            background-color: {colores['badge']};
            border-radius: 8px;
            padding: 2px 8px;
            border: none;
        """)

        layout.addWidget(lbl_icono)
        layout.addWidget(lbl_num)
        layout.addWidget(lbl_cap)
        layout.addWidget(lbl_estado)

    def mousePressEvent(self, event):
        self.on_select(self)

    def set_seleccionada(self, valor):
        self.seleccionada = valor
        if valor:
            self.setStyleSheet(self.styleSheet().replace("border: 2px solid", "border: 3px solid #cba6f7; /* sel */\n        border-old: 2px solid"))
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORES_ESTADO.get(self.mesa.estado, {}).get('fondo', '#252535')};
                    border: 3px solid #cba6f7;
                    border-radius: 10px;
                }}
            """)
        else:
            colores = COLORES_ESTADO.get(self.mesa.estado, COLORES_ESTADO["disponible"])
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colores['fondo']};
                    border: 2px solid {colores['borde']};
                    border-radius: 10px;
                }}
            """)


class MesasView(QWidget):
    def __init__(self):
        super().__init__()
        self.card_seleccionada = None
        self.cards = []
        self._build_ui()
        self._cargar_mesas()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── Encabezado ──
        header = QHBoxLayout()
        titulo = QLabel("Gestión de Mesas")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #cba6f7;")
        btn_nueva = QPushButton("+ Nueva Mesa")
        btn_nueva.setFixedWidth(140)
        btn_nueva.setStyleSheet("background-color: #cba6f7; color: #1e1e2e; font-weight: bold; border-radius: 6px; padding: 7px;")
        btn_nueva.clicked.connect(self._abrir_dialog_crear)
        header.addWidget(titulo)
        header.addStretch()
        header.addWidget(btn_nueva)
        layout.addLayout(header)

        # ── Leyenda ──
        leyenda = QHBoxLayout()
        for estado, colores in COLORES_ESTADO.items():
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {colores['badge']}; font-size: 14px;")
            lbl = QLabel(estado.capitalize())
            lbl.setStyleSheet("color: #a6adc8; font-size: 12px;")
            leyenda.addWidget(dot)
            leyenda.addWidget(lbl)
            leyenda.addSpacing(12)
        leyenda.addStretch()
        layout.addLayout(leyenda)

        # ── Grid de mesas con scroll ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self.grid_container)
        layout.addWidget(scroll)

        # ── Botones acción ──
        acciones = QHBoxLayout()
        btn_editar = QPushButton("✏  Editar")
        btn_eliminar = QPushButton("🗑  Eliminar")
        btn_editar.clicked.connect(self._abrir_dialog_editar)
        btn_eliminar.clicked.connect(self._eliminar_mesa)
        acciones.addStretch()
        acciones.addWidget(btn_editar)
        acciones.addWidget(btn_eliminar)
        layout.addLayout(acciones)

    def _cargar_mesas(self):
        # Limpiar grid
        for card in self.cards:
            card.setParent(None)
        self.cards.clear()
        self.card_seleccionada = None

        mesas = obtener_mesas()
        columnas = 6
        for i, mesa in enumerate(mesas):
            card = MesaCard(mesa, self._seleccionar_card)
            self.grid_layout.addWidget(card, i // columnas, i % columnas)
            self.cards.append(card)

    def _seleccionar_card(self, card):
        if self.card_seleccionada:
            self.card_seleccionada.set_seleccionada(False)
        self.card_seleccionada = card
        card.set_seleccionada(True)

    def _mesa_seleccionada(self):
        if not self.card_seleccionada:
            QMessageBox.warning(self, "Aviso", "Selecciona una mesa primero.")
            return None
        return self.card_seleccionada.mesa

    def _abrir_dialog_crear(self):
        dialog = MesaDialog(self)
        if dialog.exec():
            datos = dialog.obtener_datos()
            try:
                crear_mesa(datos["numero"], datos["capacidad"], datos["estado"])
                self._cargar_mesas()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear la mesa:\n{e}")

    def _abrir_dialog_editar(self):
        mesa = self._mesa_seleccionada()
        if not mesa:
            return
        dialog = MesaDialog(self, {
            "numero": mesa.numero,
            "capacidad": mesa.capacidad,
            "estado": mesa.estado
        })
        if dialog.exec():
            datos = dialog.obtener_datos()
            try:
                actualizar_mesa(mesa.id, datos["numero"], datos["capacidad"], datos["estado"])
                self._cargar_mesas()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar:\n{e}")

    def _eliminar_mesa(self):
        mesa = self._mesa_seleccionada()
        if not mesa:
            return
        confirmar = QMessageBox.question(
            self, "Confirmar",
            f"¿Eliminar la mesa #{mesa.numero}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            try:
                eliminar_mesa(mesa.id)
                self._cargar_mesas()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar:\n{e}")


class MesaDialog(QDialog):
    def __init__(self, parent=None, mesa=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva Mesa" if not mesa else "Editar Mesa")
        self.setFixedSize(320, 220)
        self._build_ui(mesa)

    def _build_ui(self, mesa):
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.input_numero = QSpinBox()
        self.input_numero.setRange(1, 999)
        self.input_numero.setValue(mesa["numero"] if mesa else 1)

        self.input_capacidad = QSpinBox()
        self.input_capacidad.setRange(1, 20)
        self.input_capacidad.setValue(mesa["capacidad"] if mesa else 2)

        self.input_estado = QComboBox()
        self.input_estado.addItems(["disponible", "ocupada", "reservada", "mantenimiento"])
        if mesa:
            self.input_estado.setCurrentText(mesa["estado"])

        layout.addRow("Número:", self.input_numero)
        layout.addRow("Capacidad:", self.input_capacidad)
        layout.addRow("Estado:", self.input_estado)

        botones = QHBoxLayout()
        btn_guardar = QPushButton("Guardar")
        btn_cancelar = QPushButton("Cancelar")
        btn_guardar.setStyleSheet("background-color: #cba6f7; color: #1e1e2e; font-weight: bold;")
        btn_guardar.clicked.connect(self.accept)
        btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_guardar)
        layout.addRow(botones)

    def obtener_datos(self):
        return {
            "numero": self.input_numero.value(),
            "capacidad": self.input_capacidad.value(),
            "estado": self.input_estado.currentText(),
        }