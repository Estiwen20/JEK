from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDialog, QFormLayout, QSpinBox,
    QComboBox, QMessageBox, QScrollArea, QGridLayout,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QGraphicsDropShadowEffect, QLineEdit,
    QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve,
    QPoint, QSize, pyqtProperty
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

# Mismas categorías que platos_view para coherencia
CATEGORIAS = {
    "Asados":       {"icono": "🔥", "color": "#f38ba8"},
    "Hamburguesas": {"icono": "🍔", "color": "#fab387"},
    "Perros":       {"icono": "🌭", "color": "#f9e2af"},
    "Bebidas":      {"icono": "🥤", "color": "#89b4fa"},
    "Postres":      {"icono": "🍰", "color": "#cba6f7"},
    "Ensaladas":    {"icono": "🥗", "color": "#a6e3a1"},
    "Sopas":        {"icono": "🍲", "color": "#94e2d5"},
    "Especiales":   {"icono": "⭐", "color": "#eba0ac"},
    "Otros":        {"icono": "🍽️", "color": "#a6adc8"},
}


# ──────────────────────────────────────────────
#  MesaCard  (sin cambios)
# ──────────────────────────────────────────────
class MesaCard(QFrame):
    def __init__(self, mesa, on_select, on_doble_clic, parent=None):
        super().__init__(parent)
        self.mesa = mesa
        self.on_select = on_select
        self.on_doble_clic = on_doble_clic
        self.seleccionada = False
        self._hover = False
        self.setFixedSize(128, 138)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_ui()
        self._apply_shadow()

    def _apply_shadow(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(14)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 90))
        self.setGraphicsEffect(shadow)

    def _build_ui(self):
        colores = COLORES_ESTADO.get(self.mesa.estado, COLORES_ESTADO["disponible"])
        self._colores = colores
        self._update_style(hover=False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icono = ICONOS_CAPACIDAD.get(self.mesa.capacidad, "🍽")
        lbl_icono = QLabel(icono)
        lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icono.setStyleSheet("font-size: 28px; border: none; background: transparent;")

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
            border-radius: 8px; padding: 2px 8px; border: none;
        """)

        layout.addWidget(lbl_icono)
        layout.addWidget(lbl_num)
        layout.addWidget(lbl_cap)
        layout.addWidget(lbl_estado)

    def _update_style(self, hover=False, seleccionada=False):
        colores = self._colores if hasattr(self, '_colores') else COLORES_ESTADO["disponible"]
        if seleccionada:
            borde, borde_w = "#cba6f7", "3px"
        elif hover:
            borde, borde_w = "#cba6f7", "2px"
        else:
            borde, borde_w = colores['borde'], "2px"
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colores['fondo']};
                border: {borde_w} solid {borde};
                border-radius: 12px;
            }}
        """)

    def showEvent(self, event):
        super().showEvent(event)
        self._pos_original = None

    def _get_pos_original(self):
        if self._pos_original is None:
            self._pos_original = self.pos()
        return self._pos_original

    def enterEvent(self, event):
        self._hover = True
        if not self.seleccionada:
            self._update_style(hover=True)
            origen = self._get_pos_original()
            for a in ('_anim_up', '_anim_down'):
                anim = getattr(self, a, None)
                if anim and anim.state() == QPropertyAnimation.State.Running:
                    anim.stop()
            anim = QPropertyAnimation(self, b"pos")
            anim.setDuration(120)
            anim.setStartValue(self.pos())
            anim.setEndValue(origen + QPoint(0, -3))
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._anim_up = anim
            anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        if not self.seleccionada:
            self._update_style(hover=False)
            origen = self._get_pos_original()
            for a in ('_anim_up', '_anim_down'):
                anim = getattr(self, a, None)
                if anim and anim.state() == QPropertyAnimation.State.Running:
                    anim.stop()
            anim = QPropertyAnimation(self, b"pos")
            anim.setDuration(120)
            anim.setStartValue(self.pos())
            anim.setEndValue(origen)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._anim_down = anim
            anim.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.on_select(self)

    def mouseDoubleClickEvent(self, event):
        self.on_doble_clic(self)

    def set_seleccionada(self, valor):
        self.seleccionada = valor
        self._update_style(seleccionada=valor)


# ──────────────────────────────────────────────
#  PanelPedido  — carta organizada por categorías
# ──────────────────────────────────────────────
class PanelPedido(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.platos_agregados = []
        self.mesa = None
        self.cantidades = {}
        self.platos = []
        self._cat_activa = "Todas"
        self._busqueda = ""
        self.setFixedWidth(420)
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
        header.setFixedHeight(62)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 10, 16, 10)

        left = QVBoxLayout()
        self.lbl_titulo = QLabel("📒  Tomar Pedido")
        self.lbl_titulo.setStyleSheet("font-size: 14px; font-weight: bold; color: #cba6f7; border: none;")
        self.lbl_mesa = QLabel("Mesa #-")
        self.lbl_mesa.setStyleSheet("font-size: 11px; color: #a6adc8; border: none;")
        left.addWidget(self.lbl_titulo)
        left.addWidget(self.lbl_mesa)

        btn_cerrar = QPushButton("✕")
        btn_cerrar.setFixedSize(36, 36)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #f38ba8; color: #fff;
                border: none; font-size: 15px; font-weight: bold; border-radius: 6px;
            }
            QPushButton:hover { background-color: #e06c8a; }
        """)
        btn_cerrar.clicked.connect(self._solicitar_cierre)

        h_layout.addLayout(left)
        h_layout.addStretch()
        h_layout.addWidget(btn_cerrar)
        layout.addWidget(header)

        # ── Buscador ──
        buscar_frame = QWidget()
        buscar_frame.setStyleSheet("background-color: #181825; border-bottom: 1px solid #252535;")
        buscar_frame.setFixedHeight(46)
        b_layout = QHBoxLayout(buscar_frame)
        b_layout.setContentsMargins(12, 6, 12, 6)
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("🔍  Buscar plato...")
        self.input_buscar.setStyleSheet("""
            QLineEdit {
                background-color: #252535; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 14px;
                padding: 0 12px; font-size: 12px;
            }
            QLineEdit:focus { border: 1px solid #cba6f7; }
        """)
        self.input_buscar.textChanged.connect(self._on_buscar)
        b_layout.addWidget(self.input_buscar)
        layout.addWidget(buscar_frame)

        # ── Tabs de categorías ──
        self.tabs_frame = QFrame()
        self.tabs_frame.setStyleSheet("background-color: #181825; border-bottom: 1px solid #252535;")
        self.tabs_frame.setFixedHeight(40)
        tabs_scroll = QScrollArea()
        tabs_scroll.setWidgetResizable(True)
        tabs_scroll.setFixedHeight(40)
        tabs_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tabs_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tabs_scroll.setStyleSheet("border: none; background: transparent;")

        tabs_inner = QWidget()
        tabs_inner.setStyleSheet("background: transparent;")
        tabs_layout = QHBoxLayout(tabs_inner)
        tabs_layout.setContentsMargins(10, 4, 10, 4)
        tabs_layout.setSpacing(4)

        self._tab_btns = {}
        categorias_tabs = ["Todas"] + list(CATEGORIAS.keys())
        for cat in categorias_tabs:
            info = CATEGORIAS.get(cat, {})
            icono = info.get("icono", "🍽️")
            color = info.get("color", "#cba6f7")
            label = f"{icono} {cat}" if cat != "Todas" else "🍽️ Todas"
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: none;
                    color: #a6adc8; font-size: 11px;
                    border-radius: 6px; padding: 0 10px;
                    border-bottom: 2px solid transparent;
                }}
                QPushButton:hover {{ color: #cdd6f4; background-color: #252535; }}
                QPushButton:checked {{
                    color: {color if cat != "Todas" else "#cba6f7"};
                    background-color: #252535;
                    border-bottom: 2px solid {color if cat != "Todas" else "#cba6f7"};
                    font-weight: bold;
                }}
            """)
            btn.clicked.connect(lambda _, c=cat: self._on_tab(c))
            self._tab_btns[cat] = btn
            tabs_layout.addWidget(btn)

        tabs_layout.addStretch()
        self._tab_btns["Todas"].setChecked(True)
        tabs_scroll.setWidget(tabs_inner)

        tab_container = QWidget()
        tab_container.setStyleSheet("background-color: #181825; border-bottom: 1px solid #252535;")
        tab_container.setFixedHeight(40)
        tc_layout = QVBoxLayout(tab_container)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.addWidget(tabs_scroll)
        layout.addWidget(tab_container)

        # ── Carta (scroll de platos) ──
        self.carta_scroll = QScrollArea()
        self.carta_scroll.setWidgetResizable(True)
        self.carta_scroll.setStyleSheet("""
            QScrollArea { border: none; background: #1e1e2e; }
            QScrollBar:vertical { background: #181825; width: 5px; border-radius: 3px; }
            QScrollBar::handle:vertical { background: #45475a; border-radius: 3px; }
            QScrollBar::handle:vertical:hover { background: #cba6f7; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        self.carta_body = QWidget()
        self.carta_body.setStyleSheet("background: #1e1e2e;")
        self.carta_body_layout = QVBoxLayout(self.carta_body)
        self.carta_body_layout.setContentsMargins(12, 12, 12, 12)
        self.carta_body_layout.setSpacing(16)
        self.carta_scroll.setWidget(self.carta_body)
        layout.addWidget(self.carta_scroll, stretch=1)

        # ── Resumen del pedido ──
        resumen_frame = QFrame()
        resumen_frame.setObjectName("resumenFrame")
        resumen_frame.setStyleSheet("""
            #resumenFrame {
                background-color: #181825;
                border-top: 1px solid #313244;
            }
        """)
        resumen_layout = QVBoxLayout(resumen_frame)
        resumen_layout.setContentsMargins(14, 10, 14, 0)
        resumen_layout.setSpacing(6)

        lbl_resumen_titulo = QLabel("PEDIDO ACTUAL")
        lbl_resumen_titulo.setStyleSheet("font-size: 10px; font-weight: bold; color: #585b70; letter-spacing: 1px;")
        resumen_layout.addWidget(lbl_resumen_titulo)

        self.tabla_pedido = QTableWidget()
        self.tabla_pedido.setColumnCount(3)
        self.tabla_pedido.setHorizontalHeaderLabels(["Plato", "Cant.", "Subtotal"])
        self.tabla_pedido.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_pedido.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_pedido.verticalHeader().setVisible(False)
        self.tabla_pedido.setMaximumHeight(120)
        self.tabla_pedido.setMinimumHeight(60)
        self.tabla_pedido.setStyleSheet("""
            QTableWidget {
                background-color: #252535; border: 1px solid #313244;
                border-radius: 8px; gridline-color: #313244;
            }
            QHeaderView::section {
                background-color: #313244; color: #cba6f7;
                border: none; padding: 4px; font-size: 11px;
            }
            QTableWidget::item { color: #cdd6f4; font-size: 12px; }
        """)
        resumen_layout.addWidget(self.tabla_pedido)

        total_row = QHBoxLayout()
        self.lbl_total = QLabel("Total: $0")
        self.lbl_total.setStyleSheet("font-size: 14px; font-weight: bold; color: #a6e3a1; border: none;")
        total_row.addStretch()
        total_row.addWidget(self.lbl_total)
        resumen_layout.addLayout(total_row)

        layout.addWidget(resumen_frame)

        # ── Footer con botón confirmar ──
        footer = QWidget()
        footer.setStyleSheet("background-color: #181825; border-top: 1px solid #252535;")
        footer.setFixedHeight(56)
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(14, 8, 14, 8)

        btn_limpiar = QPushButton("🗑  Limpiar")
        btn_limpiar.setFixedHeight(38)
        btn_limpiar.setStyleSheet("""
            QPushButton {
                background-color: #3a1e1e; color: #f38ba8;
                border: 1px solid #f38ba833; border-radius: 8px;
                font-size: 12px; padding: 0 12px;
            }
            QPushButton:hover { background-color: #f38ba8; color: #1e1e2e; }
        """)
        btn_limpiar.clicked.connect(self._limpiar_pedido)

        self.btn_confirmar = QPushButton("✅  Confirmar Pedido")
        self.btn_confirmar.setFixedHeight(38)
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1; color: #1e1e2e;
                font-weight: bold; font-size: 13px; border-radius: 8px; border: none;
            }
            QPushButton:hover { background-color: #94d4a0; }
            QPushButton:pressed { background-color: #7ec48a; }
        """)
        self.btn_confirmar.clicked.connect(self._confirmar_pedido)

        f_layout.addWidget(btn_limpiar)
        f_layout.addStretch()
        f_layout.addWidget(self.btn_confirmar)
        layout.addWidget(footer)

    # ── Carga ──

    def cargar_mesa(self, mesa):
        self.mesa = mesa
        self.platos_agregados = []
        self.cantidades = {}
        self._cat_activa = "Todas"
        self._busqueda = ""
        self.input_buscar.blockSignals(True)
        self.input_buscar.clear()
        self.input_buscar.blockSignals(False)
        for btn in self._tab_btns.values():
            btn.setChecked(False)
        self._tab_btns["Todas"].setChecked(True)
        self.lbl_mesa.setText(f"Mesa #{mesa.numero} · {mesa.capacidad} personas")
        self.platos = [p for p in obtener_platos() if p.disponible]
        for p in self.platos:
            self.cantidades[p.id] = 0
        self._renderizar_carta()
        self._renderizar_resumen()

    def _on_tab(self, cat):
        self._cat_activa = cat
        for c, btn in self._tab_btns.items():
            btn.setChecked(c == cat)
        self._renderizar_carta()

    def _on_buscar(self, texto):
        self._busqueda = texto.lower()
        self._renderizar_carta()

    def _platos_filtrados(self):
        platos = self.platos
        if self._cat_activa != "Todas":
            platos = [p for p in platos if p.categoria == self._cat_activa]
        if self._busqueda:
            platos = [p for p in platos if self._busqueda in p.nombre.lower()]
        return platos

    # ── Renderizado de la carta ──

    def _renderizar_carta(self):
        # Limpiar
        while self.carta_body_layout.count():
            item = self.carta_body_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        platos = self._platos_filtrados()

        if not platos:
            lbl = QLabel("No hay platos para mostrar.")
            lbl.setStyleSheet("color: #585b70; font-size: 13px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.carta_body_layout.addWidget(lbl)
            self.carta_body_layout.addStretch()
            return

        # Agrupar por categoría
        grupos = {}
        for plato in platos:
            cat = plato.categoria if plato.categoria in CATEGORIAS else "Otros"
            grupos.setdefault(cat, []).append(plato)

        # Orden de categorías definido
        orden = list(CATEGORIAS.keys())
        for cat in orden:
            if cat not in grupos:
                continue
            info = CATEGORIAS[cat]
            lista = grupos[cat]

            # Encabezado de sección
            sec = QWidget()
            sec.setStyleSheet("background: transparent;")
            sec_layout = QHBoxLayout(sec)
            sec_layout.setContentsMargins(0, 0, 0, 0)
            sec_layout.setSpacing(8)

            lbl_icono = QLabel(info["icono"])
            lbl_icono.setStyleSheet("font-size: 16px; background: transparent; border: none;")

            lbl_cat = QLabel(cat)
            lbl_cat.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {info['color']}; background: transparent; border: none;")

            sep_line = QFrame()
            sep_line.setFrameShape(QFrame.Shape.HLine)
            sep_line.setStyleSheet(f"background-color: {info['color']}44; border: none;")
            sep_line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            lbl_cnt = QLabel(f"{len(lista)}")
            lbl_cnt.setStyleSheet(f"font-size: 10px; color: {info['color']}; background: {info['color']}22; border-radius: 8px; padding: 1px 6px; border: none;")

            sec_layout.addWidget(lbl_icono)
            sec_layout.addWidget(lbl_cat)
            sec_layout.addWidget(sep_line)
            sec_layout.addWidget(lbl_cnt)
            self.carta_body_layout.addWidget(sec)

            # Platos de esta categoría
            for plato in lista:
                fila = self._crear_fila_plato(plato)
                self.carta_body_layout.addWidget(fila)

        self.carta_body_layout.addStretch()

    def _crear_fila_plato(self, plato):
        info_cat = CATEGORIAS.get(plato.categoria, CATEGORIAS["Otros"])
        color_acento = info_cat["color"]
        qty_actual = self.cantidades.get(plato.id, 0)
        seleccionado = qty_actual > 0

        fila = QFrame()
        fila.setObjectName("filaPlato")
        fila.setStyleSheet(f"""
            QFrame#filaPlato {{
                background-color: {"#252540" if seleccionado else "#252535"};
                border-radius: 10px;
                border: 1px solid {color_acento if seleccionado else "#313244"};
            }}
        """)
        fila.setFixedHeight(56)

        f_layout = QHBoxLayout(fila)
        f_layout.setContentsMargins(12, 0, 10, 0)
        f_layout.setSpacing(8)

        # Icono del plato
        lbl_icono = QLabel(plato.icono if hasattr(plato, 'icono') and plato.icono else info_cat["icono"])
        lbl_icono.setFixedWidth(28)
        lbl_icono.setStyleSheet("font-size: 20px; border: none; background: transparent;")

        # Nombre y precio
        info_col = QVBoxLayout()
        info_col.setSpacing(1)
        lbl_nombre = QLabel(plato.nombre)
        lbl_nombre.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {'#cba6f7' if seleccionado else '#cdd6f4'}; border: none; background: transparent;")
        lbl_precio = QLabel(f"${plato.precio:,.0f}")
        lbl_precio.setStyleSheet(f"font-size: 11px; color: {color_acento}; border: none; background: transparent;")
        info_col.addWidget(lbl_nombre)
        info_col.addWidget(lbl_precio)

        # Controles cantidad
        controles = QHBoxLayout()
        controles.setSpacing(4)

        btn_menos = QPushButton("−")
        btn_menos.setFixedSize(26, 26)
        btn_menos.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_menos.setStyleSheet("""
            QPushButton { background: #313244; color: #cdd6f4; border: none; border-radius: 5px; font-size: 15px; font-weight: bold; }
            QPushButton:hover { background: #45475a; }
            QPushButton:pressed { background: #f38ba8; color: #1e1e2e; }
        """)

        lbl_qty = QLabel(str(qty_actual))
        lbl_qty.setFixedWidth(24)
        lbl_qty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_qty.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {'#cba6f7' if seleccionado else '#585b70'}; border: none; background: transparent;")

        btn_mas = QPushButton("+")
        btn_mas.setFixedSize(26, 26)
        btn_mas.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_mas.setStyleSheet("""
            QPushButton { background: #313244; color: #cdd6f4; border: none; border-radius: 5px; font-size: 15px; font-weight: bold; }
            QPushButton:hover { background: #45475a; }
            QPushButton:pressed { background: #a6e3a1; color: #1e1e2e; }
        """)

        def hacer_cambio(p_id, delta, qty_label, frame):
            def cambiar():
                nuevo = max(0, self.cantidades.get(p_id, 0) + delta)
                self.cantidades[p_id] = nuevo
                qty_label.setText(str(nuevo))
                sel = nuevo > 0
                frame.setStyleSheet(f"""
                    QFrame#filaPlato {{
                        background-color: {"#252540" if sel else "#252535"};
                        border-radius: 10px;
                        border: 1px solid {color_acento if sel else "#313244"};
                    }}
                """)
                lbl_nombre.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {'#cba6f7' if sel else '#cdd6f4'}; border: none; background: transparent;")
                qty_label.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {'#cba6f7' if sel else '#585b70'}; border: none; background: transparent;")
                self._sincronizar_pedido()
            return cambiar

        btn_menos.clicked.connect(hacer_cambio(plato.id, -1, lbl_qty, fila))
        btn_mas.clicked.connect(hacer_cambio(plato.id, 1, lbl_qty, fila))

        controles.addWidget(btn_menos)
        controles.addWidget(lbl_qty)
        controles.addWidget(btn_mas)

        f_layout.addWidget(lbl_icono)
        f_layout.addLayout(info_col, stretch=1)
        f_layout.addLayout(controles)

        return fila

    # ── Lógica del pedido ──

    def _sincronizar_pedido(self):
        self.platos_agregados = [
            (pid, qty) for pid, qty in self.cantidades.items() if qty > 0
        ]
        self._renderizar_resumen()

    def _renderizar_resumen(self):
        self.tabla_pedido.setRowCount(0)
        total = 0.0
        platos_dict = {p.id: p for p in self.platos}
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

    def _limpiar_pedido(self):
        for pid in self.cantidades:
            self.cantidades[pid] = 0
        self.platos_agregados = []
        self._renderizar_carta()
        self._renderizar_resumen()

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

            msg = f"✅ Pedido #{pedido_id} creado para Mesa #{mesa.numero}." if es_nuevo \
                  else f"✅ Platos agregados al pedido #{pedido_id} de Mesa #{mesa.numero}."
            QMessageBox.information(self.parent(), "Pedido" + (" creado" if es_nuevo else " actualizado"), msg)

            if hasattr(self.parent(), "_cargar_mesas"):
                self.parent()._cargar_mesas()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar:\n{e}")

    def _solicitar_cierre(self):
        if hasattr(self.parent(), "_cerrar_panel"):
            self.parent()._cerrar_panel()


# ──────────────────────────────────────────────
#  MesasView  (sin cambios de lógica)
# ──────────────────────────────────────────────
class MesasView(QWidget):
    def __init__(self, usuario=None):
        super().__init__()
        self.usuario = usuario
        self.card_seleccionada = None
        self.cards = []
        self.panel_visible = False
        self._build_ui()
        self._cargar_mesas()

    def _es_admin(self):
        return self.usuario is not None and self.usuario.es_admin()

    def _build_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        contenido = QWidget()
        contenido.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        titulo = QLabel("Tablero de Mesas")
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #cba6f7;")
        header.addWidget(titulo)
        header.addStretch()

        if self._es_admin():
            self.btn_nueva = QPushButton("+ Nueva Mesa")
            self.btn_nueva.setFixedWidth(140)
            self.btn_nueva.setStyleSheet("""
                QPushButton {
                    background-color: #cba6f7; color: #1e1e2e;
                    font-weight: bold; border-radius: 8px; padding: 7px; border: none;
                }
                QPushButton:hover { background-color: #b48ef0; }
                QPushButton:pressed { background-color: #9a73e8; }
            """)
            self.btn_nueva.clicked.connect(self._abrir_dialog_crear)
            header.addWidget(self.btn_nueva)

        layout.addLayout(header)

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

        hint_texto = "💡 Doble clic sobre una mesa para editarla" if self._es_admin() \
                     else "💡 Selecciona una mesa y usa 'Tomar Pedido'"
        lbl_hint = QLabel(hint_texto)
        lbl_hint.setStyleSheet("font-size: 11px; color: #585b70;")
        layout.addWidget(lbl_hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self.grid_container)
        layout.addWidget(scroll)

        acciones = QHBoxLayout()
        if self._es_admin():
            self.btn_eliminar = QPushButton("🗑  Eliminar Mesa")
            self.btn_eliminar.clicked.connect(self._eliminar_mesa)
            acciones.addStretch()
            acciones.addWidget(self.btn_eliminar)
        else:
            # Mesero puede cambiar estado de la mesa (ocupada ↔ disponible)
            self.btn_estado_mesa = QPushButton("🔄  Cambiar Estado")
            self.btn_estado_mesa.setStyleSheet("""
                QPushButton {
                    background-color: #313244; color: #cdd6f4;
                    border: 1px solid #45475a; border-radius: 8px;
                    padding: 7px 14px; font-size: 13px;
                }
                QPushButton:hover { background-color: #45475a; }
                QPushButton:pressed { background-color: #585b70; }
            """)
            self.btn_estado_mesa.clicked.connect(self._cambiar_estado_mesa)
            acciones.addStretch()
            acciones.addWidget(self.btn_estado_mesa)

        self.btn_tomar = QPushButton("📋  Tomar Pedido")
        self.btn_tomar.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa; color: #1e1e2e;
                font-weight: bold; border-radius: 8px; padding: 7px 16px; border: none;
            }
            QPushButton:hover { background-color: #74a8f5; }
            QPushButton:pressed { background-color: #5a94e8; }
        """)
        self.btn_tomar.clicked.connect(self._abrir_panel)
        acciones.addWidget(self.btn_tomar)
        layout.addLayout(acciones)

        self.main_layout.addWidget(contenido)

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
        if not self._es_admin():
            return
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

    def _cambiar_estado_mesa(self):
        mesa = self._mesa_seleccionada()
        if not mesa:
            return
        dialog = EstadoMesaDialog(self, mesa.estado)
        if dialog.exec():
            nuevo_estado = dialog.obtener_estado()
            if nuevo_estado == mesa.estado:
                return
            try:
                actualizar_mesa(mesa.id, mesa.numero, mesa.capacidad, nuevo_estado)
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


# ──────────────────────────────────────────────
#  EstadoMesaDialog  — para el mesero
# ──────────────────────────────────────────────
class EstadoMesaDialog(QDialog):
    """Diálogo compacto para que el mesero cambie el estado de una mesa."""
    def __init__(self, parent=None, estado_actual="disponible"):
        super().__init__(parent)
        self.setWindowTitle("Cambiar estado de mesa")
        self.setFixedSize(360, 260)
        self._estado_sel = estado_actual
        self._build_ui(estado_actual)
        self._apply_styles()

    def _build_ui(self, estado_actual):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        lbl_titulo = QLabel("¿Cuál es el estado de la mesa?")
        lbl_titulo.setStyleSheet("font-size: 14px; font-weight: bold; color: #cdd6f4;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_titulo)

        # Botones de estado como tarjetas
        OPCIONES = [
            ("disponible",    "✅  Disponible",    "#a6e3a1", "#1e3a2f"),
            ("ocupada",       "🔴  Ocupada",        "#f38ba8", "#3a1e1e"),
            ("reservada",     "🟡  Reservada",      "#f9e2af", "#2a2a1e"),
            ("mantenimiento", "🔧  Mantenimiento",  "#a6adc8", "#252535"),
        ]

        self._btns = {}
        grid = QGridLayout()
        grid.setSpacing(10)
        for i, (estado, label, color, fondo) in enumerate(OPCIONES):
            btn = QPushButton(label)
            btn.setFixedHeight(46)
            btn.setCheckable(True)
            btn.setChecked(estado == estado_actual)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {"" if estado != estado_actual else fondo};
                    color: {color};
                    border: 2px solid {"" if estado != estado_actual else color};
                    border-radius: 10px;
                    font-size: 13px; font-weight: bold;
                    padding: 0 12px;
                    background-color: {fondo if estado == estado_actual else "#252535"};
                    border-color: {color if estado == estado_actual else "#45475a"};
                }}
                QPushButton:hover {{
                    background-color: {fondo};
                    border: 2px solid {color};
                    color: {color};
                }}
                QPushButton:checked {{
                    background-color: {fondo};
                    border: 2px solid {color};
                    color: {color};
                }}
            """)
            btn.clicked.connect(lambda _, e=estado, c=color, f=fondo: self._seleccionar(e, c, f))
            self._btns[estado] = (btn, color, fondo)
            grid.addWidget(btn, i // 2, i % 2)

        layout.addLayout(grid)

        # Botones confirmar / cancelar
        botones = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFixedHeight(38)
        btn_cancelar.clicked.connect(self.reject)

        self.btn_confirmar = QPushButton("Confirmar")
        self.btn_confirmar.setFixedHeight(38)
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                background-color: #cba6f7; color: #1e1e2e;
                font-weight: bold; border-radius: 8px; border: none; padding: 0 20px;
            }
            QPushButton:hover { background-color: #b48ef0; }
            QPushButton:pressed { background-color: #9a73e8; }
        """)
        self.btn_confirmar.clicked.connect(self.accept)

        botones.addWidget(btn_cancelar)
        botones.addStretch()
        botones.addWidget(self.btn_confirmar)
        layout.addLayout(botones)

    def _seleccionar(self, estado, color, fondo):
        self._estado_sel = estado
        # Actualizar estilos de todos los botones
        COLORES_MAP = {
            "disponible":    ("#a6e3a1", "#1e3a2f"),
            "ocupada":       ("#f38ba8", "#3a1e1e"),
            "reservada":     ("#f9e2af", "#2a2a1e"),
            "mantenimiento": ("#a6adc8", "#252535"),
        }
        for e, (btn, c, f) in self._btns.items():
            activo = e == estado
            btn.setChecked(activo)
            c2, f2 = COLORES_MAP[e]
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {f2 if activo else "#252535"};
                    color: {c2};
                    border: 2px solid {c2 if activo else "#45475a"};
                    border-radius: 10px;
                    font-size: 13px; font-weight: bold;
                    padding: 0 12px;
                }}
                QPushButton:hover {{
                    background-color: {f2};
                    border: 2px solid {c2};
                    color: {c2};
                }}
                QPushButton:checked {{
                    background-color: {f2};
                    border: 2px solid {c2};
                    color: {c2};
                }}
            """)

    def obtener_estado(self):
        return self._estado_sel

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; font-family: 'Segoe UI'; }
            QLabel { color: #cdd6f4; }
            QPushButton {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 8px; padding: 5px 14px;
            }
            QPushButton:hover { background-color: #45475a; }
        """)


# ──────────────────────────────────────────────
#  MesaDialog  (sin cambios)
# ──────────────────────────────────────────────
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
        btn_guardar.setStyleSheet("background-color: #cba6f7; color: #1e1e2e; font-weight: bold; border-radius: 6px;")
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