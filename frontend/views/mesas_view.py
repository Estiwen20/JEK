from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDialog, QFormLayout, QSpinBox,
    QComboBox, QMessageBox, QScrollArea, QGridLayout,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve,
    QPoint, QRect, QSize
)
from PyQt6.QtGui import QColor

from backend.repositories.mesa_repo import (
    crear_mesa, obtener_mesas,
    actualizar_mesa, eliminar_mesa
)
from backend.repositories.pedido_repo import (
    crear_pedido, agregar_plato_a_pedido,
    obtener_pedido_abierto_por_mesa
)
from backend.repositories.plato_repo import obtener_platos
from datetime import datetime


COLORES_ESTADO = {
    "disponible":    {"fondo": "#1e3a2f", "borde": "#a6e3a1", "texto": "#a6e3a1", "badge": "#a6e3a1", "badge_txt": "#1e3a2f"},
    "ocupada":       {"fondo": "#3a1e1e", "borde": "#f38ba8", "texto": "#f38ba8", "badge": "#f38ba8", "badge_txt": "#3a1e1e"},
    "reservada":     {"fondo": "#2a2a1e", "borde": "#f9e2af", "texto": "#f9e2af", "badge": "#f9e2af", "badge_txt": "#2a2a1e"},
    "mantenimiento": {"fondo": "#252535", "borde": "#45475a", "texto": "#a6adc8", "badge": "#45475a", "badge_txt": "#cdd6f4"},
}

ICONOS_CAPACIDAD = {2: "🪑", 4: "🍽", 6: "🍽", 8: "🏮"}


class MesaCard(QFrame):
    def __init__(self, mesa, on_select, on_doble_clic, parent=None):
        super().__init__(parent)
        self.mesa = mesa
        self.on_select = on_select
        self.on_doble_clic = on_doble_clic
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
        lbl_cap.setStyleSheet(f"font-size: 10px; color: {colores['texto']}; border: none; background: transparent;")

        lbl_estado = QLabel(self.mesa.estado.capitalize())
        lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_estado.setStyleSheet(f"""
            font-size: 10px; font-weight: bold;
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

    def mouseDoubleClickEvent(self, event):
        self.on_doble_clic(self)

    def set_seleccionada(self, valor):
        self.seleccionada = valor
        colores = COLORES_ESTADO.get(self.mesa.estado, COLORES_ESTADO["disponible"])
        if valor:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colores['fondo']};
                    border: 3px solid #cba6f7;
                    border-radius: 10px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colores['fondo']};
                    border: 2px solid {colores['borde']};
                    border-radius: 10px;
                }}
            """)


class PanelPedido(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.platos_agregados = []
        self.mesa = None
        self.setFixedWidth(340)
        self.setObjectName("panelPedido")
        self.setStyleSheet("""
            #panelPedido {
                background-color: #181825;
                border-left: 1px solid #313244;
            }
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ──
        header = QWidget()
        header.setStyleSheet("background-color: #181825; border-bottom: 1px solid #313244;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 14, 16, 14)

        header_left = QVBoxLayout()
        self.lbl_titulo = QLabel("📒  Tomar Pedido")
        self.lbl_titulo.setStyleSheet("font-size: 14px; font-weight: bold; color: #cba6f7; border: none;")
        self.lbl_mesa = QLabel("Mesa #-")
        self.lbl_mesa.setStyleSheet("font-size: 11px; color: #a6adc8; border: none;")
        header_left.addWidget(self.lbl_titulo)
        header_left.addWidget(self.lbl_mesa)

        btn_cerrar = QPushButton("✕")
        btn_cerrar.setFixedSize(28, 28)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #a6adc8;
                border: none;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #313244;
                color: #f38ba8;
            }
        """)
        btn_cerrar.clicked.connect(self._solicitar_cierre)

        header_layout.addLayout(header_left)
        header_layout.addStretch()
        header_layout.addWidget(btn_cerrar)
        layout.addWidget(header)

        # ── Scroll body ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(16, 16, 16, 16)
        body_layout.setSpacing(14)

        # Menú
        lbl_menu = QLabel("MENÚ DISPONIBLE")
        lbl_menu.setStyleSheet("font-size: 10px; font-weight: bold; color: #585b70; letter-spacing: 1px;")
        body_layout.addWidget(lbl_menu)

        self.menu_layout = QVBoxLayout()
        self.menu_layout.setSpacing(6)
        body_layout.addLayout(self.menu_layout)

        # Pedido actual
        lbl_pedido = QLabel("PEDIDO ACTUAL")
        lbl_pedido.setStyleSheet("font-size: 10px; font-weight: bold; color: #585b70; letter-spacing: 1px; margin-top: 6px;")
        body_layout.addWidget(lbl_pedido)

        self.tabla_pedido = QTableWidget()
        self.tabla_pedido.setColumnCount(3)
        self.tabla_pedido.setHorizontalHeaderLabels(["Plato", "Cant.", "Subtotal"])
        self.tabla_pedido.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_pedido.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_pedido.verticalHeader().setVisible(False)
        self.tabla_pedido.setMaximumHeight(150)
        self.tabla_pedido.setStyleSheet("""
            QTableWidget {
                background-color: #252535;
                border: 1px solid #313244;
                border-radius: 8px;
                gridline-color: #313244;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #cba6f7;
                border: none;
                padding: 4px;
                font-size: 11px;
            }
        """)
        body_layout.addWidget(self.tabla_pedido)

        self.lbl_total = QLabel("Total: $0.00")
        self.lbl_total.setStyleSheet("font-size: 14px; font-weight: bold; color: #a6e3a1; border: none;")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        body_layout.addWidget(self.lbl_total)
        body_layout.addStretch()

        scroll.setWidget(body)
        layout.addWidget(scroll)

        # ── Footer ──
        footer = QWidget()
        footer.setStyleSheet("background-color: #181825; border-top: 1px solid #313244;")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(16, 12, 16, 12)

        self.btn_confirmar = QPushButton("✅  Confirmar Pedido")
        self.btn_confirmar.setFixedHeight(40)
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                color: #1e1e2e;
                font-weight: bold;
                font-size: 13px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background-color: #94d4a0; }
            QPushButton:pressed { background-color: #7ec48a; }
        """)
        self.btn_confirmar.clicked.connect(self._confirmar_pedido)
        footer_layout.addWidget(self.btn_confirmar)
        layout.addWidget(footer)

    def cargar_mesa(self, mesa):
        self.mesa = mesa
        self.platos_agregados = []
        self.lbl_mesa.setText(f"Mesa #{mesa.numero} · {mesa.capacidad} personas")
        self._renderizar_menu()
        self._renderizar_pedido()

    def _renderizar_menu(self):
        while self.menu_layout.count():
            item = self.menu_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.platos = obtener_platos()
        self.cantidades = {}

        for plato in self.platos:
            if not plato.disponible:
                continue
            self.cantidades[plato.id] = 0

            fila = QWidget()
            fila.setStyleSheet("""
                QWidget {
                    background-color: #252535;
                    border-radius: 8px;
                    border: 1px solid #313244;
                }
                QWidget:hover { border: 1px solid #cba6f7; }
            """)
            fila_layout = QHBoxLayout(fila)
            fila_layout.setContentsMargins(10, 8, 10, 8)

            info = QVBoxLayout()
            lbl_nombre = QLabel(plato.nombre)
            lbl_nombre.setStyleSheet("font-size: 12px; font-weight: bold; color: #cdd6f4; border: none; background: transparent;")
            lbl_precio = QLabel(f"${plato.precio:,.0f}")
            lbl_precio.setStyleSheet("font-size: 11px; color: #a6adc8; border: none; background: transparent;")
            info.addWidget(lbl_nombre)
            info.addWidget(lbl_precio)

            controles = QHBoxLayout()
            controles.setSpacing(4)

            btn_menos = QPushButton("−")
            btn_menos.setFixedSize(24, 24)
            btn_menos.setStyleSheet("""
                QPushButton {
                    background: #313244; color: #cdd6f4;
                    border: none; border-radius: 4px; font-size: 14px;
                }
                QPushButton:hover { background: #45475a; }
            """)

            lbl_qty = QLabel("0")
            lbl_qty.setFixedWidth(20)
            lbl_qty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_qty.setStyleSheet("font-size: 12px; font-weight: bold; color: #cdd6f4; border: none; background: transparent;")

            btn_mas = QPushButton("+")
            btn_mas.setFixedSize(24, 24)
            btn_mas.setStyleSheet("""
                QPushButton {
                    background: #313244; color: #cdd6f4;
                    border: none; border-radius: 4px; font-size: 14px;
                }
                QPushButton:hover { background: #45475a; }
            """)

            def hacer_cambio(p_id, delta, qty_label):
                def cambiar():
                    self.cantidades[p_id] = max(0, self.cantidades.get(p_id, 0) + delta)
                    qty_label.setText(str(self.cantidades[p_id]))
                    self._sincronizar_pedido()
                return cambiar

            btn_menos.clicked.connect(hacer_cambio(plato.id, -1, lbl_qty))
            btn_mas.clicked.connect(hacer_cambio(plato.id, 1, lbl_qty))

            controles.addWidget(btn_menos)
            controles.addWidget(lbl_qty)
            controles.addWidget(btn_mas)

            fila_layout.addLayout(info)
            fila_layout.addStretch()
            fila_layout.addLayout(controles)
            self.menu_layout.addWidget(fila)

    def _sincronizar_pedido(self):
        self.platos_agregados = [
            (pid, qty) for pid, qty in self.cantidades.items() if qty > 0
        ]
        self._renderizar_pedido()

    def _renderizar_pedido(self):
        self.tabla_pedido.setRowCount(0)
        total = 0.0
        platos_dict = {p.id: p for p in getattr(self, "platos", [])}
        for plato_id, cantidad in self.platos_agregados:
            plato = platos_dict.get(plato_id)
            if not plato:
                continue
            subtotal = plato.precio * cantidad
            total += subtotal
            row = self.tabla_pedido.rowCount()
            self.tabla_pedido.insertRow(row)
            self.tabla_pedido.setItem(row, 0, QTableWidgetItem(plato.nombre))
            self.tabla_pedido.setItem(row, 1, QTableWidgetItem(str(cantidad)))
            self.tabla_pedido.setItem(row, 2, QTableWidgetItem(f"${subtotal:,.0f}"))
        self.lbl_total.setText(f"Total: ${total:,.0f}")

    def _confirmar_pedido(self):
        if not self.platos_agregados:
            QMessageBox.warning(self, "Aviso", "Agrega al menos un plato.")
            return
        mesa = self.mesa
        try:
            pedido_existente = obtener_pedido_abierto_por_mesa(mesa.id)
            if pedido_existente:
                pedido_id = pedido_existente.id
                es_nuevo = False
            else:
                fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                pedido_id = crear_pedido(mesa.id, fecha)
                es_nuevo = True

            for plato_id, cantidad in self.platos_agregados:
                agregar_plato_a_pedido(pedido_id, plato_id, cantidad)

            if mesa.estado != "ocupada":
                actualizar_mesa(mesa.id, mesa.numero, mesa.capacidad, "ocupada")

            self._solicitar_cierre()

            if es_nuevo:
                QMessageBox.information(
                    self.parent(), "Pedido creado",
                    f"✅ Pedido #{pedido_id} creado para Mesa #{mesa.numero}."
                )
            else:
                QMessageBox.information(
                    self.parent(), "Pedido actualizado",
                    f"✅ Platos agregados al pedido #{pedido_id} de Mesa #{mesa.numero}."
                )

            if hasattr(self.parent(), "_cargar_mesas"):
                self.parent()._cargar_mesas()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar:\n{e}")

    def _solicitar_cierre(self):
        if hasattr(self.parent(), "_cerrar_panel"):
            self.parent()._cerrar_panel()


class MesasView(QWidget):
    def __init__(self):
        super().__init__()
        self.card_seleccionada = None
        self.cards = []
        self.panel_visible = False
        self._build_ui()
        self._cargar_mesas()

    def _build_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ── Contenido principal ──
        contenido = QWidget()
        contenido.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Encabezado
        header = QHBoxLayout()
        titulo = QLabel("Tablero de Mesas")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #cba6f7;")
        self.btn_nueva = QPushButton("+ Nueva Mesa")
        self.btn_nueva.setFixedWidth(140)
        self.btn_nueva.setStyleSheet("background-color: #cba6f7; color: #1e1e2e; font-weight: bold; border-radius: 6px; padding: 7px;")
        self.btn_nueva.clicked.connect(self._abrir_dialog_crear)
        header.addWidget(titulo)
        header.addStretch()
        header.addWidget(self.btn_nueva)
        layout.addLayout(header)

        # Leyenda
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

        # Hint doble clic
        lbl_hint = QLabel("💡 Doble clic sobre una mesa para editarla")
        lbl_hint.setStyleSheet("font-size: 11px; color: #585b70;")
        layout.addWidget(lbl_hint)

        # Grid con scroll
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

        # Botones acción
        acciones = QHBoxLayout()
        btn_eliminar = QPushButton("🗑  Eliminar Mesa")
        btn_eliminar.clicked.connect(self._eliminar_mesa)
        self.btn_tomar = QPushButton("📋  Tomar Pedido")
        self.btn_tomar.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                font-weight: bold;
                border-radius: 6px;
                padding: 7px 16px;
                border: none;
            }
            QPushButton:hover { background-color: #74a8f5; }
        """)
        self.btn_tomar.clicked.connect(self._abrir_panel)
        acciones.addStretch()
        acciones.addWidget(btn_eliminar)
        acciones.addWidget(self.btn_tomar)
        layout.addLayout(acciones)

        self.main_layout.addWidget(contenido)

        # ── Panel lateral ──
        self.panel = PanelPedido(self)
        self.panel.hide()
        self.main_layout.addWidget(self.panel)

    def _cargar_mesas(self):
        for card in self.cards:
            card.setParent(None)
        self.cards.clear()
        self.card_seleccionada = None

        mesas = obtener_mesas()
        columnas = 6
        for i, mesa in enumerate(mesas):
            card = MesaCard(mesa, self._seleccionar_card, self._doble_clic_mesa)
            self.grid_layout.addWidget(card, i // columnas, i % columnas)
            self.cards.append(card)

    def _seleccionar_card(self, card):
        if self.card_seleccionada:
            self.card_seleccionada.set_seleccionada(False)
        self.card_seleccionada = card
        card.set_seleccionada(True)

    def _doble_clic_mesa(self, card):
        self._seleccionar_card(card)
        mesa = card.mesa
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

    def _abrir_panel(self):
        if not self.card_seleccionada:
            QMessageBox.warning(self, "Aviso", "Selecciona una mesa primero.")
            return
        mesa = self.card_seleccionada.mesa
        if mesa.estado == "mantenimiento":
            QMessageBox.warning(self, "Aviso", "Esta mesa está en mantenimiento.")
            return

        self.panel.cargar_mesa(mesa)
        self.panel.show()
        self.panel_visible = True

        # Animación slide in
        ancho_panel = self.panel.width()
        self.panel.move(self.width(), 0)
        self.panel.resize(ancho_panel, self.height())

        self._anim_abrir = QPropertyAnimation(self.panel, b"pos")
        self._anim_abrir.setDuration(350)
        self._anim_abrir.setStartValue(QPoint(self.width(), 0))
        self._anim_abrir.setEndValue(QPoint(self.width() - ancho_panel, 0))
        self._anim_abrir.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_abrir.start()

    def _cerrar_panel(self):
        ancho_panel = self.panel.width()
        self._anim_cerrar = QPropertyAnimation(self.panel, b"pos")
        self._anim_cerrar.setDuration(300)
        self._anim_cerrar.setStartValue(QPoint(self.width() - ancho_panel, 0))
        self._anim_cerrar.setEndValue(QPoint(self.width(), 0))
        self._anim_cerrar.setEasingCurve(QEasingCurve.Type.InCubic)
        self._anim_cerrar.finished.connect(self.panel.hide)
        self._anim_cerrar.start()
        self.panel_visible = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.panel_visible:
            self.panel.resize(self.panel.width(), self.height())
            self.panel.move(self.width() - self.panel.width(), 0)

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
        self.setFixedSize(320, 230)
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
