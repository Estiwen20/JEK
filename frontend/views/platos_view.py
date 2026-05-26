from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDialog, QFormLayout, QComboBox,
    QLineEdit, QMessageBox, QDoubleSpinBox,
    QCheckBox, QScrollArea, QFrame, QGridLayout,
    QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QColor, QFont

from backend.repositories.plato_repo import (
    crear_plato, obtener_platos,
    actualizar_plato, eliminar_plato
)

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

ICONOS_DISPONIBLES = [
    "🍔","🌭","🔥","🥩","🍗","🍕","🌮","🌯","🥪","🍱",
    "🥗","🍲","🍜","🍝","🍛","🍣","🦐","🥚","🧆","🧇",
    "🥤","🧃","☕","🍺","🍹","🧋","🍵","🥛","🍶","🍷",
    "🍰","🍩","🍪","🧁","🍫","🍦","🍮","🥧","🍭","🍬",
    "🥗","🥦","🥕","🌽","🍅","🧅","🧄","🥑","🍋","🫐",
    "⭐","🌟","💎","🏆","❤️","🎯","🎪","🎨","🌶️","🫕",
]


class PlatoCard(QFrame):
    def __init__(self, plato, on_edit, on_delete, on_toggle, es_admin=True, parent=None):
        super().__init__(parent)
        self.plato = plato
        self._pos_orig = None
        self.setFixedSize(200, 175)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_ui(on_edit, on_delete, on_toggle, es_admin)
        self._apply_shadow()

    def _apply_shadow(self):
        s = QGraphicsDropShadowEffect()
        s.setBlurRadius(16)
        s.setOffset(0, 4)
        s.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(s)

    def _build_ui(self, on_edit, on_delete, on_toggle, es_admin):
        cat = CATEGORIAS.get(self.plato.categoria, CATEGORIAS["Otros"])
        color_acento = cat["color"]
        disponible = self.plato.disponible

        fondo = "#1e2535" if disponible else "#1a1a1a"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {fondo};
                border: 1px solid {"#313244" if disponible else "#2a2a2a"};
                border-radius: 14px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(52)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {color_acento}22;
                border-top-left-radius: 14px; border-top-right-radius: 14px;
                border-bottom: 1px solid {color_acento}44;
                border-left: none; border-right: none;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 6, 12, 6)

        lbl_icono = QLabel(self.plato.icono)
        lbl_icono.setStyleSheet("font-size: 26px; border: none; background: transparent;")

        lbl_cat = QLabel(self.plato.categoria)
        lbl_cat.setStyleSheet(f"font-size: 10px; color: {color_acento}; border: none; background: transparent; font-weight: bold;")
        lbl_cat.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        header_layout.addWidget(lbl_icono)
        header_layout.addStretch()
        header_layout.addWidget(lbl_cat)
        root.addWidget(header)

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(12, 8, 12, 8)
        body_layout.setSpacing(3)

        lbl_nombre = QLabel(self.plato.nombre)
        lbl_nombre.setWordWrap(True)
        lbl_nombre.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {'#cdd6f4' if disponible else '#585b70'}; border: none; background: transparent;")
        body_layout.addWidget(lbl_nombre)

        if self.plato.descripcion:
            lbl_desc = QLabel(self.plato.descripcion)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet(f"font-size: 10px; color: {'#7f849c' if disponible else '#3a3a3a'}; border: none; background: transparent;")
            body_layout.addWidget(lbl_desc)

        body_layout.addStretch()

        precio_row = QHBoxLayout()
        lbl_precio = QLabel(f"${self.plato.precio:,.0f}")
        lbl_precio.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {color_acento if disponible else '#45475a'}; border: none; background: transparent;")

        badge = QLabel("Disponible" if disponible else "No disponible")
        badge.setStyleSheet(f"""
            font-size: 9px; font-weight: bold;
            color: {'#1e3a2f' if disponible else '#3a1e1e'};
            background-color: {'#a6e3a1' if disponible else '#f38ba8'};
            border-radius: 6px; padding: 2px 6px; border: none;
        """)
        precio_row.addWidget(lbl_precio)
        precio_row.addStretch()
        precio_row.addWidget(badge)
        body_layout.addLayout(precio_row)
        root.addWidget(body)

        # ── Botones de acción según rol ──
        actions = QFrame()
        actions.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-top: 1px solid #2a2a3e;
                border-bottom-left-radius: 14px; border-bottom-right-radius: 14px;
                border-left: none; border-right: none;
            }}
        """)
        actions.setFixedHeight(34)
        act_layout = QHBoxLayout(actions)
        act_layout.setContentsMargins(6, 4, 6, 4)
        act_layout.setSpacing(4)

        btn_style = """
            QPushButton {
                background: transparent; border: none;
                font-size: 14px; border-radius: 4px; padding: 2px 4px;
            }
            QPushButton:hover { background-color: #313244; }
        """

        if es_admin:
            # Admin: editar, eliminar y toggle disponibilidad
            btn_edit = QPushButton("✏️")
            btn_edit.setToolTip("Editar")
            btn_edit.setFixedSize(28, 26)
            btn_edit.setStyleSheet(btn_style)
            btn_edit.clicked.connect(on_edit)

            btn_del = QPushButton("🗑️")
            btn_del.setToolTip("Eliminar")
            btn_del.setFixedSize(28, 26)
            btn_del.setStyleSheet(btn_style)
            btn_del.clicked.connect(on_delete)

            btn_toggle = QPushButton("👁️" if disponible else "🚫")
            btn_toggle.setToolTip("Cambiar disponibilidad")
            btn_toggle.setFixedSize(28, 26)
            btn_toggle.setStyleSheet(btn_style)
            btn_toggle.clicked.connect(on_toggle)

            act_layout.addWidget(btn_edit)
            act_layout.addWidget(btn_del)
            act_layout.addStretch()
            act_layout.addWidget(btn_toggle)
        else:
            # Mesero: solo puede cambiar disponibilidad
            btn_toggle = QPushButton("👁️" if disponible else "🚫")
            btn_toggle.setToolTip("Cambiar disponibilidad")
            btn_toggle.setFixedSize(28, 26)
            btn_toggle.setStyleSheet(btn_style)
            btn_toggle.clicked.connect(on_toggle)

            act_layout.addStretch()
            act_layout.addWidget(btn_toggle)

        root.addWidget(actions)

    def showEvent(self, event):
        super().showEvent(event)
        self._pos_orig = None

    def _get_orig(self):
        if self._pos_orig is None:
            self._pos_orig = self.pos()
        return self._pos_orig

    def enterEvent(self, event):
        orig = self._get_orig()
        for a in ("_ah", "_al"):
            anim = getattr(self, a, None)
            if anim and anim.state() == QPropertyAnimation.State.Running:
                anim.stop()
        a = QPropertyAnimation(self, b"pos")
        a.setDuration(130); a.setStartValue(self.pos())
        a.setEndValue(orig + QPoint(0, -4))
        a.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._ah = a; a.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        orig = self._get_orig()
        for a in ("_ah", "_al"):
            anim = getattr(self, a, None)
            if anim and anim.state() == QPropertyAnimation.State.Running:
                anim.stop()
        a = QPropertyAnimation(self, b"pos")
        a.setDuration(130); a.setStartValue(self.pos())
        a.setEndValue(orig)
        a.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._al = a; a.start()
        super().leaveEvent(event)


class PlatosView(QWidget):
    def __init__(self, usuario=None):
        super().__init__()
        self.usuario = usuario
        self._plato_seleccionado = None
        self._build_ui()
        self._cargar_platos()

    def _es_admin(self):
        return self.usuario is not None and self.usuario.es_admin()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(64)
        topbar.setStyleSheet("""
            #topbar { background-color: #181825; border-bottom: 1px solid #313244; }
        """)
        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(24, 0, 24, 0)

        titulo = QLabel("📋  Carta del Restaurante")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #cba6f7; background: transparent;")

        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("🔍  Buscar plato...")
        self.input_buscar.setFixedWidth(220)
        self.input_buscar.setFixedHeight(36)
        self.input_buscar.setStyleSheet("""
            QLineEdit {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 18px;
                padding: 0 14px; font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid #cba6f7; }
        """)
        self.input_buscar.textChanged.connect(self._filtrar)

        top_layout.addWidget(titulo)
        top_layout.addStretch()
        top_layout.addWidget(self.input_buscar)

        # ── Solo el admin puede crear platos ──
        if self._es_admin():
            btn_nuevo = QPushButton("＋  Nuevo Plato")
            btn_nuevo.setFixedHeight(36)
            btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_nuevo.setStyleSheet("""
                QPushButton {
                    background-color: #cba6f7; color: #1e1e2e;
                    font-weight: bold; font-size: 13px;
                    border-radius: 8px; border: none; padding: 0 16px;
                }
                QPushButton:hover { background-color: #b48ef0; }
                QPushButton:pressed { background-color: #9a73e8; }
            """)
            btn_nuevo.clicked.connect(self._abrir_dialog_crear)
            top_layout.addSpacing(12)
            top_layout.addWidget(btn_nuevo)

        root.addWidget(topbar)

        self.tab_bar = QFrame()
        self.tab_bar.setStyleSheet("background-color: #181825; border-bottom: 1px solid #2a2a3e;")
        self.tab_bar.setFixedHeight(48)
        tab_layout = QHBoxLayout(self.tab_bar)
        tab_layout.setContentsMargins(16, 0, 16, 0)
        tab_layout.setSpacing(4)

        self._tab_buttons = {}
        categorias_tabs = ["Todas"] + list(CATEGORIAS.keys())
        for cat in categorias_tabs:
            info = CATEGORIAS.get(cat, {})
            icono = info.get("icono", "🍽️")
            color = info.get("color", "#cba6f7")
            label = f"{icono} {cat}" if cat != "Todas" else "🍽️ Todas"
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: none;
                    color: #a6adc8; font-size: 12px;
                    border-radius: 6px; padding: 0 12px;
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
            btn.clicked.connect(lambda _, c=cat: self._filtrar_categoria(c))
            self._tab_buttons[cat] = btn
            tab_layout.addWidget(btn)

        tab_layout.addStretch()
        self._tab_buttons["Todas"].setChecked(True)
        self._cat_activa = "Todas"
        root.addWidget(self.tab_bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background-color: #1e1e2e; }
            QScrollBar:vertical { background: #181825; width: 6px; border-radius: 3px; }
            QScrollBar::handle:vertical { background: #45475a; border-radius: 3px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: #cba6f7; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        self.carta_widget = QWidget()
        self.carta_widget.setStyleSheet("background-color: #1e1e2e;")
        self.carta_layout = QVBoxLayout(self.carta_widget)
        self.carta_layout.setContentsMargins(24, 20, 24, 24)
        self.carta_layout.setSpacing(28)
        self.scroll.setWidget(self.carta_widget)
        root.addWidget(self.scroll)

    def _cargar_platos(self):
        self.platos = obtener_platos()
        self._renderizar(self.platos)

    def _renderizar(self, platos):
        while self.carta_layout.count():
            item = self.carta_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not platos:
            lbl = QLabel("No hay platos para mostrar.")
            lbl.setStyleSheet("color: #585b70; font-size: 14px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.carta_layout.addWidget(lbl)
            self.carta_layout.addStretch()
            return

        grupos = {}
        for plato in platos:
            cat = plato.categoria if plato.categoria in CATEGORIAS else "Otros"
            grupos.setdefault(cat, []).append(plato)

        orden = list(CATEGORIAS.keys())
        for cat in orden:
            if cat not in grupos:
                continue
            lista = grupos[cat]
            info = CATEGORIAS[cat]

            sec_header = QWidget()
            sec_header.setStyleSheet("background: transparent;")
            sh_layout = QHBoxLayout(sec_header)
            sh_layout.setContentsMargins(0, 0, 0, 0)
            sh_layout.setSpacing(10)

            lbl_icono_sec = QLabel(info["icono"])
            lbl_icono_sec.setStyleSheet("font-size: 22px; background: transparent;")

            lbl_cat_sec = QLabel(cat)
            lbl_cat_sec.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {info['color']}; background: transparent;")

            linea = QFrame()
            linea.setFrameShape(QFrame.Shape.HLine)
            linea.setStyleSheet(f"background-color: {info['color']}44; border: none; max-height: 1px;")
            linea.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            lbl_cnt = QLabel(f"{len(lista)} plato{'s' if len(lista) != 1 else ''}")
            lbl_cnt.setStyleSheet("font-size: 11px; color: #585b70; background: transparent;")

            sh_layout.addWidget(lbl_icono_sec)
            sh_layout.addWidget(lbl_cat_sec)
            sh_layout.addWidget(linea)
            sh_layout.addWidget(lbl_cnt)
            self.carta_layout.addWidget(sec_header)

            grid_widget = QWidget()
            grid_widget.setStyleSheet("background: transparent;")
            grid = QGridLayout(grid_widget)
            grid.setSpacing(16)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

            cols = 5
            for i, plato in enumerate(lista):
                card = PlatoCard(
                    plato,
                    on_edit=lambda _, p=plato: self._editar(p),
                    on_delete=lambda _, p=plato: self._eliminar(p),
                    on_toggle=lambda _, p=plato: self._toggle(p),
                    es_admin=self._es_admin(),
                )
                grid.addWidget(card, i // cols, i % cols)

            self.carta_layout.addWidget(grid_widget)

        self.carta_layout.addStretch()

    def _filtrar(self, texto):
        cat = self._cat_activa
        platos = self.platos
        if cat != "Todas":
            platos = [p for p in platos if p.categoria == cat]
        if texto:
            platos = [p for p in platos if texto.lower() in p.nombre.lower()]
        self._renderizar(platos)

    def _filtrar_categoria(self, cat):
        self._cat_activa = cat
        for c, btn in self._tab_buttons.items():
            btn.setChecked(c == cat)
        self._filtrar(self.input_buscar.text())

    def _abrir_dialog_crear(self):
        dialog = PlatoDialog(self)
        if dialog.exec():
            datos = dialog.obtener_datos()
            try:
                crear_plato(datos["nombre"], datos["descripcion"],
                            datos["precio"], datos["disponible"],
                            datos["categoria"], datos["icono"])
                self._cargar_platos()
                self._filtrar_categoria(self._cat_activa)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear el plato:\n{e}")

    def _editar(self, plato):
        if not self._es_admin():
            return
        dialog = PlatoDialog(self, plato)
        if dialog.exec():
            datos = dialog.obtener_datos()
            try:
                actualizar_plato(plato.id, datos["nombre"], datos["descripcion"],
                                 datos["precio"], datos["disponible"],
                                 datos["categoria"], datos["icono"])
                self._cargar_platos()
                self._filtrar_categoria(self._cat_activa)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar:\n{e}")

    def _eliminar(self, plato):
        if not self._es_admin():
            return
        confirmar = QMessageBox.question(
            self, "Confirmar",
            f"¿Eliminar '{plato.nombre}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            try:
                eliminar_plato(plato.id)
                self._cargar_platos()
                self._filtrar_categoria(self._cat_activa)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar:\n{e}")

    def _toggle(self, plato):
        try:
            actualizar_plato(plato.id, plato.nombre, plato.descripcion,
                             plato.precio, not plato.disponible,
                             plato.categoria, plato.icono)
            self._cargar_platos()
            self._filtrar_categoria(self._cat_activa)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cambiar disponibilidad:\n{e}")


class PlatoDialog(QDialog):
    def __init__(self, parent=None, plato=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Plato" if not plato else "Editar Plato")
        self.setFixedSize(520, 500)
        self._icono_sel = plato.icono if plato else "🍽️"
        self._build_ui(plato)
        self._apply_styles()

    def _build_ui(self, plato):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        layout.addWidget(self._label("Nombre del plato"))
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ej: Bandeja Paisa")
        self.input_nombre.setObjectName("inp")
        if plato: self.input_nombre.setText(plato.nombre)
        layout.addWidget(self.input_nombre)

        layout.addWidget(self._label("Descripción (opcional)"))
        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("Ej: Con arroz, frijoles y chicharrón")
        self.input_desc.setObjectName("inp")
        if plato: self.input_desc.setText(plato.descripcion or "")
        layout.addWidget(self.input_desc)

        fila = QHBoxLayout()
        col1 = QVBoxLayout()
        col1.addWidget(self._label("Precio"))
        self.input_precio = QDoubleSpinBox()
        self.input_precio.setRange(0, 999999)
        self.input_precio.setDecimals(0)
        self.input_precio.setPrefix("$ ")
        self.input_precio.setObjectName("inp")
        self.input_precio.setFixedHeight(38)
        if plato: self.input_precio.setValue(plato.precio)
        col1.addWidget(self.input_precio)

        col2 = QVBoxLayout()
        col2.addWidget(self._label("Categoría"))
        self.combo_cat = QComboBox()
        self.combo_cat.setObjectName("inp")
        self.combo_cat.setFixedHeight(38)
        for cat, info in CATEGORIAS.items():
            self.combo_cat.addItem(f"{info['icono']} {cat}", cat)
        if plato:
            idx = self.combo_cat.findData(plato.categoria)
            if idx >= 0: self.combo_cat.setCurrentIndex(idx)
        col2.addWidget(self.combo_cat)

        fila.addLayout(col1)
        fila.addSpacing(12)
        fila.addLayout(col2)
        layout.addLayout(fila)

        layout.addWidget(self._label("Icono del plato"))
        icono_scroll = QScrollArea()
        icono_scroll.setFixedHeight(170)
        icono_scroll.setWidgetResizable(True)
        icono_scroll.setStyleSheet("""
            QScrollArea { border: 1px solid #45475a; border-radius: 8px; background: #252535; }
            QScrollBar:vertical { background: #252535; width: 6px; border-radius: 3px; }
            QScrollBar::handle:vertical { background: #45475a; border-radius: 3px; }
            QScrollBar::handle:vertical:hover { background: #cba6f7; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        icono_inner = QWidget()
        icono_inner.setStyleSheet("background: transparent;")
        icono_grid = QGridLayout(icono_inner)
        icono_grid.setContentsMargins(10, 10, 10, 10)
        icono_grid.setSpacing(6)

        self._icono_btns = {}
        cols = 8
        for i, em in enumerate(ICONOS_DISPONIBLES):
            b = QPushButton(em)
            b.setFixedSize(46, 46)
            b.setCheckable(True)
            b.setChecked(em == self._icono_sel)
            b.setToolTip(em)
            b.setStyleSheet("""
                QPushButton {
                    background: transparent; border: 1px solid transparent;
                    border-radius: 6px; font-size: 22px; padding: 0;
                }
                QPushButton:hover { background: #3a3a4e; }
                QPushButton:checked {
                    background: #313244; border: 2px solid #cba6f7; border-radius: 6px;
                }
            """)
            b.clicked.connect(lambda _, e=em: self._sel_icono(e))
            icono_grid.addWidget(b, i // cols, i % cols)
            self._icono_btns[em] = b

        icono_scroll.setWidget(icono_inner)
        layout.addWidget(icono_scroll)

        fila2 = QHBoxLayout()
        self.chk_disp = QCheckBox("  Disponible")
        self.chk_disp.setChecked(plato.disponible if plato else True)
        self.chk_disp.setStyleSheet("color: #a6adc8; font-size: 13px;")

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("btnCancelar")
        btn_cancelar.setFixedHeight(38)
        btn_cancelar.clicked.connect(self.reject)

        btn_guardar = QPushButton("Guardar")
        btn_guardar.setObjectName("btnGuardar")
        btn_guardar.setFixedHeight(38)
        btn_guardar.clicked.connect(self._validar)

        fila2.addWidget(self.chk_disp)
        fila2.addStretch()
        fila2.addWidget(btn_cancelar)
        fila2.addSpacing(8)
        fila2.addWidget(btn_guardar)
        layout.addLayout(fila2)

    def _sel_icono(self, emoji):
        self._icono_sel = emoji
        for e, b in self._icono_btns.items():
            b.setChecked(e == emoji)

    def _label(self, txt):
        l = QLabel(txt)
        l.setStyleSheet("font-size: 11px; color: #a6adc8; background: transparent;")
        return l

    def _validar(self):
        if not self.input_nombre.text().strip():
            QMessageBox.warning(self, "Aviso", "El nombre no puede estar vacío.")
            return
        self.accept()

    def obtener_datos(self):
        return {
            "nombre":      self.input_nombre.text().strip(),
            "descripcion": self.input_desc.text().strip(),
            "precio":      self.input_precio.value(),
            "disponible":  self.chk_disp.isChecked(),
            "categoria":   self.combo_cat.currentData(),
            "icono":       self._icono_sel,
        }

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; font-family: 'Segoe UI'; }
            #inp {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 8px;
                padding: 5px 12px; font-size: 13px; height: 38px;
            }
            #inp:focus { border: 1px solid #cba6f7; }
            QComboBox { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 8px; padding: 5px 12px; font-size: 13px; }
            QComboBox:focus { border: 1px solid #cba6f7; }
            #btnGuardar { background-color: #cba6f7; color: #1e1e2e; font-weight: bold; border-radius: 8px; border: none; padding: 0 20px; }
            #btnGuardar:hover { background-color: #b48ef0; }
            #btnCancelar { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 8px; padding: 0 16px; }
            #btnCancelar:hover { background-color: #45475a; }
            QLabel { color: #cdd6f4; }
        """)