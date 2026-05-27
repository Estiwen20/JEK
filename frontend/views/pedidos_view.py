from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QComboBox, QMessageBox,
    QHeaderView, QSpinBox, QScrollArea, QFrame,
    QGridLayout, QGroupBox, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QPoint, QSequentialAnimationGroup, QPauseAnimation,
    pyqtSignal
)
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QBrush
from datetime import datetime
import threading
import sys

from backend.repositories.pedido_repo import (
    crear_pedido, agregar_plato_a_pedido, quitar_plato_de_pedido,
    obtener_pedidos, obtener_items_pedido, actualizar_estado_pedido,
    eliminar_pedido
)
from backend.repositories.mesa_repo import obtener_mesas
from backend.repositories.plato_repo import obtener_platos, obtener_plato_por_id


def _tocar_campana():
    def _play():
        try:
            if sys.platform == "win32":
                import winsound
                for freq, dur in [(880, 120), (1100, 120), (1320, 200)]:
                    winsound.Beep(freq, dur)
            else:
                print("\a", end="", flush=True)
        except Exception:
            pass
    threading.Thread(target=_play, daemon=True).start()


COLORES_ESTADO = {
    "abierto":        {"fondo": "#1e2535", "borde": "#89b4fa", "badge": "#89b4fa", "badge_txt": "#1e1e2e"},
    "en preparación": {"fondo": "#2a1e0e", "borde": "#fab387", "badge": "#fab387", "badge_txt": "#1e1e2e"},
    "listo":          {"fondo": "#1e3a2f", "borde": "#a6e3a1", "badge": "#a6e3a1", "badge_txt": "#1e1e2e"},
    "cerrado":        {"fondo": "#1a1a1a", "borde": "#45475a", "badge": "#45475a", "badge_txt": "#cdd6f4"},
}


class ComandaCard(QFrame):
    """Tarjeta de comanda con animaciones de caída y degradado."""

    campana_presionada      = pyqtSignal(int)  # emite pedido_id
    preparacion_presionada  = pyqtSignal(int)  # emite pedido_id
    eliminar_presionado     = pyqtSignal(int)  # emite pedido_id

    def __init__(self, pedido, items_con_platos, total, es_admin=False, parent=None):
        super().__init__(parent)
        self.pedido = pedido
        self.es_admin = es_admin
        self._animando = False
        self.setObjectName("comandaCard")
        self.setFixedWidth(260)
        self._build_ui(items_con_platos, total)
        self._apply_shadow()

    def _apply_shadow(self):
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        s = QGraphicsDropShadowEffect()
        s.setBlurRadius(18)
        s.setOffset(0, 4)
        s.setColor(QColor(0, 0, 0, 110))
        self.setGraphicsEffect(s)

    def _build_ui(self, items_con_platos, total):
        colores = COLORES_ESTADO.get(self.pedido.estado, COLORES_ESTADO["abierto"])
        self.setStyleSheet(f"""
            QFrame#comandaCard {{
                background-color: {colores['fondo']};
                border: 2px solid {colores['borde']};
                border-radius: 14px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Cabecera ──
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {colores['borde']}22;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid {colores['borde']}55;
                border-left: none; border-right: none;
            }}
        """)
        header.setFixedHeight(54)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(14, 8, 14, 8)

        lbl_id = QLabel(f"Pedido #{self.pedido.id}")
        lbl_id.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {colores['borde']}; border: none; background: transparent;")

        badge = QLabel(self.pedido.estado.capitalize())
        badge.setStyleSheet(f"""
            font-size: 10px; font-weight: bold;
            color: {colores['badge_txt']};
            background-color: {colores['badge']};
            border-radius: 8px; padding: 2px 8px; border: none;
        """)

        h_layout.addWidget(lbl_id)
        h_layout.addStretch()
        h_layout.addWidget(badge)
        root.addWidget(header)

        # ── Info mesa y hora ──
        info = QWidget()
        info.setStyleSheet("background: transparent;")
        info_layout = QHBoxLayout(info)
        info_layout.setContentsMargins(14, 6, 14, 2)

        lbl_mesa = QLabel(f"🪑  Mesa #{self.pedido.mesa_id}")
        lbl_mesa.setStyleSheet("font-size: 11px; color: #a6adc8; border: none; background: transparent;")

        hora = self.pedido.fecha.split(" ")[1][:5] if " " in self.pedido.fecha else self.pedido.fecha[-5:]
        lbl_hora = QLabel(f"🕐  {hora}")
        lbl_hora.setStyleSheet("font-size: 11px; color: #585b70; border: none; background: transparent;")

        info_layout.addWidget(lbl_mesa)
        info_layout.addStretch()
        info_layout.addWidget(lbl_hora)
        root.addWidget(info)

        # ── Separador ──
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {colores['borde']}33; border: none; margin: 0 14px;")
        root.addWidget(sep)

        # ── Items ──
        items_widget = QWidget()
        items_widget.setStyleSheet("background: transparent;")
        items_layout = QVBoxLayout(items_widget)
        items_layout.setContentsMargins(14, 8, 14, 8)
        items_layout.setSpacing(4)

        for plato, cantidad in items_con_platos:
            fila = QHBoxLayout()
            lbl_nombre = QLabel(f"• {plato.nombre}")
            lbl_nombre.setStyleSheet("font-size: 12px; color: #cdd6f4; border: none; background: transparent;")
            lbl_nombre.setWordWrap(True)
            lbl_cant = QLabel(f"×{cantidad}")
            lbl_cant.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {colores['borde']}; border: none; background: transparent;")
            lbl_cant.setFixedWidth(28)
            lbl_cant.setAlignment(Qt.AlignmentFlag.AlignRight)
            fila.addWidget(lbl_nombre, stretch=1)
            fila.addWidget(lbl_cant)
            items_layout.addLayout(fila)

        root.addWidget(items_widget)

        # ── Total ──
        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background-color: {colores['borde']}33; border: none; margin: 0 14px;")
        root.addWidget(sep2)

        total_row = QWidget()
        total_row.setStyleSheet("background: transparent;")
        total_layout = QHBoxLayout(total_row)
        total_layout.setContentsMargins(14, 6, 14, 6)
        lbl_t = QLabel("Total:")
        lbl_t.setStyleSheet("font-size: 12px; color: #a6adc8; border: none; background: transparent;")
        lbl_val = QLabel(f"${total:,.0f}")
        lbl_val.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {colores['borde']}; border: none; background: transparent;")
        total_layout.addWidget(lbl_t)
        total_layout.addStretch()
        total_layout.addWidget(lbl_val)
        root.addWidget(total_row)

        # ── Botones de acción ──
        footer = QFrame()
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {colores['borde']}0d;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                border-top: 1px solid {colores['borde']}33;
                border-left: none; border-right: none;
            }}
        """)

        if self.pedido.estado == "cerrado":
            # Estado final — solo mostrar etiqueta
            footer.setFixedHeight(38)
            f_layout = QHBoxLayout(footer)
            f_layout.setContentsMargins(14, 0, 14, 0)
            lbl_done = QLabel("✅  Cobrado")
            lbl_done.setStyleSheet("font-size: 11px; color: #585b70; border: none; background: transparent;")
            f_layout.addStretch()
            f_layout.addWidget(lbl_done)
            f_layout.addStretch()

        elif self.pedido.estado == "listo":
            # Listo para cobrar — solo etiqueta + eliminar
            footer.setFixedHeight(42)
            f_layout = QHBoxLayout(footer)
            f_layout.setContentsMargins(12, 6, 12, 6)
            f_layout.setSpacing(6)
            lbl_done = QLabel("✅  Listo para cobrar")
            lbl_done.setStyleSheet("font-size: 11px; color: #a6e3a1; border: none; background: transparent;")
            f_layout.addWidget(lbl_done)
            f_layout.addStretch()
            if self.es_admin:
                btn_del = self._btn_eliminar()
                f_layout.addWidget(btn_del)

        elif self.pedido.estado == "en preparación":
            # En preparación — botón Listo + eliminar
            footer.setFixedHeight(50)
            f_layout = QVBoxLayout(footer)
            f_layout.setContentsMargins(10, 6, 10, 6)
            f_layout.setSpacing(5)

            fila = QHBoxLayout()
            fila.setSpacing(6)

            self.btn_campana = QPushButton("🔔  Marcar como listo")
            self.btn_campana.setFixedHeight(32)
            self.btn_campana.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_campana.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #1e3a2f, stop:1 #2a4a3a);
                    color: #a6e3a1;
                    font-weight: bold; font-size: 11px;
                    border-radius: 8px;
                    border: 1px solid #a6e3a155;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #a6e3a1, stop:1 #8fd4a0);
                    color: #1e1e2e;
                    border: 1px solid #a6e3a1;
                }
                QPushButton:pressed { background: #7ec48a; color: #1e1e2e; }
            """)
            self.btn_campana.clicked.connect(
                lambda: self.campana_presionada.emit(self.pedido.id)
            )
            fila.addWidget(self.btn_campana)
            if self.es_admin:
                fila.addWidget(self._btn_eliminar())
            f_layout.addLayout(fila)

        else:
            # Estado "abierto" — 2 botones en fila + eliminar
            footer.setFixedHeight(50)
            f_layout = QVBoxLayout(footer)
            f_layout.setContentsMargins(10, 6, 10, 6)
            f_layout.setSpacing(5)

            fila = QHBoxLayout()
            fila.setSpacing(6)

            # Botón "En preparación"
            btn_prep = QPushButton("🍳  Preparar")
            btn_prep.setFixedHeight(32)
            btn_prep.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_prep.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #2a1e0e, stop:1 #3a2a10);
                    color: #fab387;
                    font-weight: bold; font-size: 11px;
                    border-radius: 8px;
                    border: 1px solid #fab38755;
                    padding: 0 8px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #fab387, stop:1 #f9a06a);
                    color: #1e1e2e;
                    border: 1px solid #fab387;
                }
                QPushButton:pressed { background: #e8935a; color: #1e1e2e; }
            """)
            btn_prep.clicked.connect(
                lambda: self.preparacion_presionada.emit(self.pedido.id)
            )

            # Botón "Listo"
            self.btn_campana = QPushButton("🔔  Listo")
            self.btn_campana.setFixedHeight(32)
            self.btn_campana.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_campana.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #1e3a2f, stop:1 #2a4a3a);
                    color: #a6e3a1;
                    font-weight: bold; font-size: 11px;
                    border-radius: 8px;
                    border: 1px solid #a6e3a155;
                    padding: 0 8px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #a6e3a1, stop:1 #8fd4a0);
                    color: #1e1e2e;
                    border: 1px solid #a6e3a1;
                }
                QPushButton:pressed { background: #7ec48a; color: #1e1e2e; }
            """)
            self.btn_campana.clicked.connect(
                lambda: self.campana_presionada.emit(self.pedido.id)
            )

            fila.addWidget(btn_prep)
            fila.addWidget(self.btn_campana)
            if self.es_admin:
                fila.addWidget(self._btn_eliminar())
            f_layout.addLayout(fila)

        root.addWidget(footer)

    def _btn_eliminar(self):
        """Crea y retorna el botón de eliminar reutilizable."""
        btn = QPushButton("🗑")
        btn.setFixedSize(32, 32)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip("Eliminar pedido")
        btn.setStyleSheet("""
            QPushButton {
                background: #3a1e1e; color: #f38ba8;
                border: 1px solid #f38ba833;
                border-radius: 8px; font-size: 13px;
            }
            QPushButton:hover { background: #f38ba8; color: #1e1e2e; border: 1px solid #f38ba8; }
            QPushButton:pressed { background: #e06c8a; color: #1e1e2e; }
        """)
        btn.clicked.connect(lambda: self.eliminar_presionado.emit(self.pedido.id))
        return btn

    # ── Animación de caída (campana) ──
    def animar_caida(self, callback):
        """Cae hacia abajo con bounce y luego llama a callback."""
        if self._animando:
            return
        self._animando = True

        pos_orig = self.pos()

        # Secuencia: rebote arriba → caída al fondo → fade out
        seq = QSequentialAnimationGroup(self)

        # 1. Pequeño salto hacia arriba
        a1 = QPropertyAnimation(self, b"pos")
        a1.setDuration(120)
        a1.setStartValue(pos_orig)
        a1.setEndValue(pos_orig + QPoint(0, -12))
        a1.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 2. Caída rápida hacia abajo (fuera de vista)
        a2 = QPropertyAnimation(self, b"pos")
        a2.setDuration(380)
        a2.setStartValue(pos_orig + QPoint(0, -12))
        a2.setEndValue(pos_orig + QPoint(0, 340))
        a2.setEasingCurve(QEasingCurve.Type.InCubic)

        seq.addAnimation(a1)
        seq.addAnimation(a2)
        seq.finished.connect(callback)
        self._seq_caida = seq
        seq.start()

    # ── Animación de fade-out con degradado (eliminar) ──
    def animar_eliminar(self, callback):
        """Fade out suave y luego llama a callback."""
        if self._animando:
            return
        self._animando = True

        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(450)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(callback)
        self._anim_fade = anim
        anim.start()


class PedidosView(QWidget):
    def __init__(self, usuario=None):
        super().__init__()
        self.usuario = usuario
        self.pedidos = []
        self._cards = {}   # pedido_id -> ComandaCard
        self._build_ui()
        self._cargar_pedidos()

    def _es_admin(self):
        return self.usuario is not None and self.usuario.es_admin()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Topbar ──
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(64)
        topbar.setStyleSheet("""
            #topbar { background-color: #181825; border-bottom: 1px solid #313244; }
        """)
        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(24, 0, 24, 0)

        titulo = QLabel("🍽  Comandas")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #cba6f7; background: transparent;")

        self.filtro_estado = QComboBox()
        self.filtro_estado.addItems(["Todos", "abierto", "en preparación", "listo", "cerrado"])
        self.filtro_estado.setFixedHeight(34)
        self.filtro_estado.setStyleSheet("""
            QComboBox {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 8px;
                padding: 0 12px; font-size: 13px;
            }
            QComboBox:focus { border: 1px solid #cba6f7; }
        """)
        self.filtro_estado.currentTextChanged.connect(self._cargar_pedidos)

        self.filtro_mesa = QComboBox()
        self.filtro_mesa.setFixedHeight(34)
        self.filtro_mesa.setStyleSheet(self.filtro_estado.styleSheet())
        self.filtro_mesa.addItem("Todas las mesas", None)
        for mesa in obtener_mesas():
            self.filtro_mesa.addItem(f"Mesa #{mesa.numero}", mesa.id)
        self.filtro_mesa.currentIndexChanged.connect(self._cargar_pedidos)

        btn_nuevo = QPushButton("＋  Nuevo Pedido")
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

        _btn_style_sec = """
            QPushButton {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 8px;
                font-size: 12px; padding: 0 14px;
            }
            QPushButton:hover { background-color: #45475a; }
            QPushButton:pressed { background-color: #585b70; }
        """

        btn_actualizar = QPushButton("🔄  Actualizar")
        btn_actualizar.setFixedHeight(36)
        btn_actualizar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_actualizar.setStyleSheet(_btn_style_sec)
        btn_actualizar.clicked.connect(self._cargar_pedidos)

        btn_limpiar = QPushButton("🧹  Limpiar listos")
        btn_limpiar.setFixedHeight(36)
        btn_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_limpiar.setStyleSheet("""
            QPushButton {
                background-color: #2a1e0e; color: #fab387;
                border: 1px solid #fab38755; border-radius: 8px;
                font-size: 12px; padding: 0 14px;
            }
            QPushButton:hover { background-color: #3a2a10; }
            QPushButton:pressed { background-color: #fab387; color: #1e1e2e; }
        """)
        btn_limpiar.clicked.connect(self._limpiar_listos)

        top_layout.addWidget(titulo)
        top_layout.addStretch()
        top_layout.addWidget(QLabel("Estado:"))
        top_layout.addSpacing(6)
        top_layout.addWidget(self.filtro_estado)
        top_layout.addSpacing(16)
        top_layout.addWidget(QLabel("Mesa:"))
        top_layout.addSpacing(6)
        top_layout.addWidget(self.filtro_mesa)
        top_layout.addSpacing(16)
        top_layout.addWidget(btn_actualizar)
        top_layout.addSpacing(8)
        top_layout.addWidget(btn_limpiar)
        top_layout.addSpacing(8)
        top_layout.addWidget(btn_nuevo)
        root.addWidget(topbar)

        # ── Área de comandas (scroll) ──
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background-color: #1e1e2e; }
            QScrollBar:vertical { background: #181825; width: 6px; border-radius: 3px; }
            QScrollBar::handle:vertical { background: #45475a; border-radius: 3px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: #cba6f7; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar:horizontal { height: 0; }
        """)

        self.canvas = QWidget()
        self.canvas.setStyleSheet("background-color: #1e1e2e;")
        self.canvas_layout = QHBoxLayout(self.canvas)
        self.canvas_layout.setContentsMargins(24, 24, 24, 24)
        self.canvas_layout.setSpacing(0)
        self.canvas_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Columnas de estados
        self._columnas = {}
        estados = [
            ("abierto",        "🟦  Abiertos",        "#89b4fa"),
            ("en preparación", "🟧  En preparación",  "#fab387"),
            ("listo",          "🟩  Listos",           "#a6e3a1"),
            ("cerrado",        "⬛  Cerrados",         "#585b70"),
        ]
        for estado, titulo_col, color in estados:
            col_widget = QWidget()
            col_widget.setStyleSheet("background: transparent;")
            col_widget.setFixedWidth(290)
            col_layout = QVBoxLayout(col_widget)
            col_layout.setContentsMargins(0, 0, 16, 0)
            col_layout.setSpacing(12)
            col_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            # Encabezado columna
            col_header = QLabel(titulo_col)
            col_header.setFixedHeight(32)
            col_header.setStyleSheet(f"""
                font-size: 13px; font-weight: bold; color: {color};
                background-color: {color}18;
                border-radius: 8px; padding: 4px 12px; border: none;
            """)
            col_layout.addWidget(col_header)

            # Contador
            lbl_cnt = QLabel("0 comandas")
            lbl_cnt.setStyleSheet("font-size: 11px; color: #585b70; padding-left: 4px;")
            col_layout.addWidget(lbl_cnt)

            self._columnas[estado] = {
                "widget": col_widget,
                "layout": col_layout,
                "contador": lbl_cnt,
                "cards": [],
            }
            self.canvas_layout.addWidget(col_widget)

        self.canvas_layout.addStretch()
        self.scroll.setWidget(self.canvas)
        root.addWidget(self.scroll)

        # ── Barra inferior (acciones sobre comanda seleccionada) ──
        self.bottombar = QFrame()
        self.bottombar.setObjectName("bottombar")
        self.bottombar.setFixedHeight(54)
        self.bottombar.setStyleSheet("""
            #bottombar {
                background-color: #181825;
                border-top: 1px solid #313244;
            }
        """)
        bot_layout = QHBoxLayout(self.bottombar)
        bot_layout.setContentsMargins(24, 0, 24, 0)
        bot_layout.setSpacing(10)

        self.lbl_seleccionada = QLabel("Selecciona una comanda para ver acciones")
        self.lbl_seleccionada.setStyleSheet("font-size: 12px; color: #585b70;")

        btn_agregar = QPushButton("➕  Agregar plato")
        btn_quitar  = QPushButton("➖  Quitar plato")
        btn_estado  = QPushButton("🔄  Cambiar estado")

        for b in (btn_agregar, btn_quitar, btn_estado):
            b.setFixedHeight(34)
            b.setStyleSheet("""
                QPushButton {
                    background-color: #313244; color: #cdd6f4;
                    border: 1px solid #45475a; border-radius: 6px;
                    padding: 0 14px; font-size: 12px;
                }
                QPushButton:hover { background-color: #45475a; }
                QPushButton:pressed { background-color: #cba6f7; color: #1e1e2e; }
            """)

        btn_agregar.clicked.connect(self._agregar_plato)
        btn_quitar.clicked.connect(self._quitar_plato)
        btn_estado.clicked.connect(self._cambiar_estado)

        bot_layout.addWidget(self.lbl_seleccionada)
        bot_layout.addStretch()
        bot_layout.addWidget(btn_agregar)
        bot_layout.addWidget(btn_quitar)
        bot_layout.addWidget(btn_estado)

        root.addWidget(self.bottombar)

        self._pedido_activo_id = None

    # ── Carga ──

    def _cargar_pedidos(self):
        estado_filtro = self.filtro_estado.currentText()
        mesa_id = self.filtro_mesa.currentData()
        filtro_estado = None if estado_filtro == "Todos" else estado_filtro

        self.pedidos = obtener_pedidos(
            filtro_estado=filtro_estado,
            filtro_mesa_id=mesa_id
        )

        # Limpiar columnas
        for info in self._columnas.values():
            for card in info["cards"]:
                card.setParent(None)
                card.deleteLater()
            info["cards"].clear()
        self._cards.clear()

        # Distribuir pedidos en columnas
        for pedido in self.pedidos:
            items = obtener_items_pedido(pedido.id)
            items_con_platos = []
            total = 0.0
            for item in items:
                plato = obtener_plato_por_id(item.plato_id)
                if plato:
                    items_con_platos.append((plato, item.cantidad))
                    total += plato.precio * item.cantidad

            col_estado = pedido.estado if pedido.estado in self._columnas else "cerrado"

            # Si hay filtro de estado y no coincide, saltar
            if filtro_estado and pedido.estado != filtro_estado:
                continue

            card = ComandaCard(
                pedido, items_con_platos, total,
                es_admin=self._es_admin()
            )
            card.campana_presionada.connect(self._on_campana)
            card.preparacion_presionada.connect(self._on_preparacion)
            card.eliminar_presionado.connect(self._on_eliminar)
            card.mousePressEvent = lambda e, pid=pedido.id: self._seleccionar(pid)

            col = self._columnas[col_estado]
            col["layout"].addWidget(card)
            col["cards"].append(card)
            self._cards[pedido.id] = card

        # Actualizar contadores
        for estado, info in self._columnas.items():
            n = len(info["cards"])
            info["contador"].setText(f"{n} comanda{'s' if n != 1 else ''}")

        self._pedido_activo_id = None
        self.lbl_seleccionada.setText("Selecciona una comanda para ver acciones")

    def _limpiar_listos(self):
        """Marca como cerrados todos los pedidos en estado 'listo'."""
        listos = [p for p in self.pedidos if p.estado == "listo"]
        if not listos:
            QMessageBox.information(self, "Sin pendientes", "No hay comandas listas para limpiar.")
            return

        confirmar = QMessageBox.question(
            self, "Limpiar listos",
            f"¿Marcar como cerrados {len(listos)} pedido(s) en estado 'listo'?\n"
            "Esto los moverá a la columna de Cerrados.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar != QMessageBox.StandardButton.Yes:
            return

        pendientes = [p.id for p in listos]
        self._limpiar_pendientes = len(pendientes)

        def _tras_animacion():
            self._limpiar_pendientes -= 1
            if self._limpiar_pendientes <= 0:
                try:
                    for pedido in listos:
                        actualizar_estado_pedido(pedido.id, "cerrado")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error al limpiar:\n{e}")
                    return
                QTimer.singleShot(80, self._cargar_pedidos)

        for pid in pendientes:
            card = self._cards.get(pid)
            if card:
                card.animar_eliminar(_tras_animacion)
            else:
                _tras_animacion()

    def _seleccionar(self, pedido_id):
        # Deseleccionar anterior
        if self._pedido_activo_id and self._pedido_activo_id in self._cards:
            prev = self._cards[self._pedido_activo_id]
            pedido_prev = next((p for p in self.pedidos if p.id == self._pedido_activo_id), None)
            if pedido_prev:
                col = COLORES_ESTADO.get(pedido_prev.estado, COLORES_ESTADO["abierto"])
                prev.setStyleSheet(f"""
                    QFrame#comandaCard {{
                        background-color: {col['fondo']};
                        border: 2px solid {col['borde']};
                        border-radius: 14px;
                    }}
                """)

        self._pedido_activo_id = pedido_id
        pedido = next((p for p in self.pedidos if p.id == pedido_id), None)
        if not pedido:
            return

        # Resaltar seleccionada
        card = self._cards[pedido_id]
        card.setStyleSheet("""
            QFrame#comandaCard {
                background-color: #2a2a42;
                border: 2px solid #cba6f7;
                border-radius: 14px;
            }
        """)
        self.lbl_seleccionada.setText(
            f"Comanda seleccionada: Pedido #{pedido_id}  ·  Mesa #{pedido.mesa_id}  ·  {pedido.estado.capitalize()}"
        )

    # ── Preparación: animación de deslizamiento lateral ──

    def _on_preparacion(self, pedido_id):
        card = self._cards.get(pedido_id)
        if not card:
            return

        # Animación: desplazamiento horizontal hacia la derecha y fade
        from PyQt6.QtWidgets import QGraphicsOpacityEffect as _OEff
        effect = _OEff(card)
        card.setGraphicsEffect(effect)

        anim_op = QPropertyAnimation(effect, b"opacity")
        anim_op.setDuration(300)
        anim_op.setStartValue(1.0)
        anim_op.setEndValue(0.0)
        anim_op.setEasingCurve(QEasingCurve.Type.OutCubic)

        anim_pos = QPropertyAnimation(card, b"pos")
        anim_pos.setDuration(300)
        anim_pos.setStartValue(card.pos())
        anim_pos.setEndValue(card.pos() + QPoint(60, 0))
        anim_pos.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _tras_anim():
            try:
                actualizar_estado_pedido(pedido_id, "en preparación")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar:\n{e}")
                return
            QTimer.singleShot(80, self._cargar_pedidos)

        anim_op.finished.connect(_tras_anim)
        self._anim_prep_op  = anim_op
        self._anim_prep_pos = anim_pos
        anim_op.start()
        anim_pos.start()

    # ── Campana: animación de caída ──

    def _on_campana(self, pedido_id):
        card = self._cards.get(pedido_id)
        if not card:
            return
        _tocar_campana()

        def _después_caída():
            try:
                actualizar_estado_pedido(pedido_id, "listo")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo marcar como listo:\n{e}")
                return
            QTimer.singleShot(100, self._cargar_pedidos)

        card.animar_caida(_después_caída)

    # ── Eliminar: animación de fade/degradado ──

    def _on_eliminar(self, pedido_id):
        if not self._es_admin():
            QMessageBox.warning(self, "Sin permiso", "Solo el administrador puede eliminar pedidos.")
            return

        confirmar = QMessageBox.question(
            self, "Confirmar", f"¿Eliminar el pedido #{pedido_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar != QMessageBox.StandardButton.Yes:
            return

        card = self._cards.get(pedido_id)
        if not card:
            return

        def _después_fade():
            try:
                eliminar_pedido(pedido_id)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar:\n{e}")
                return
            QTimer.singleShot(60, self._cargar_pedidos)

        card.animar_eliminar(_después_fade)

    # ── Acciones sobre comanda seleccionada ──

    def _pedido_activo(self):
        if not self._pedido_activo_id:
            QMessageBox.warning(self, "Aviso", "Selecciona una comanda primero.")
            return None
        return next((p for p in self.pedidos if p.id == self._pedido_activo_id), None)

    def _abrir_dialog_crear(self):
        dialog = NuevoPedidoDialog(self)
        if dialog.exec():
            mesa_id, platos_seleccionados = dialog.obtener_datos()
            try:
                fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                pedido_id = crear_pedido(mesa_id, fecha)
                for plato_id, cantidad in platos_seleccionados:
                    agregar_plato_a_pedido(pedido_id, plato_id, cantidad)
                self._cargar_pedidos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear el pedido:\n{e}")

    def _agregar_plato(self):
        pedido = self._pedido_activo()
        if not pedido:
            return
        dialog = AgregarPlatoDialog(self)
        if dialog.exec():
            plato_id, cantidad = dialog.obtener_datos()
            try:
                agregar_plato_a_pedido(pedido.id, plato_id, cantidad)
                self._cargar_pedidos()
                self._seleccionar(pedido.id)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al agregar plato:\n{e}")

    def _quitar_plato(self):
        pedido = self._pedido_activo()
        if not pedido:
            return
        items = obtener_items_pedido(pedido.id)
        if not items:
            QMessageBox.warning(self, "Aviso", "Este pedido no tiene platos.")
            return
        dialog = QuitarPlatoDialog(self, items)
        if dialog.exec():
            item_id = dialog.obtener_item_id()
            if item_id:
                quitar_plato_de_pedido(item_id)
                self._cargar_pedidos()

    def _cambiar_estado(self):
        pedido = self._pedido_activo()
        if not pedido:
            return
        dialog = CambiarEstadoDialog(self, pedido.estado)
        if dialog.exec():
            nuevo_estado = dialog.obtener_estado()
            try:
                actualizar_estado_pedido(pedido.id, nuevo_estado)
                self._cargar_pedidos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al cambiar estado:\n{e}")


# ── Diálogos ──

class NuevoPedidoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Pedido")
        self.setFixedSize(420, 420)
        self.platos_agregados = []
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        mesa_layout = QHBoxLayout()
        mesa_layout.addWidget(QLabel("Mesa:"))
        self.combo_mesa = QComboBox()
        for mesa in obtener_mesas():
            self.combo_mesa.addItem(f"Mesa #{mesa.numero} ({mesa.estado})", mesa.id)
        mesa_layout.addWidget(self.combo_mesa)
        layout.addLayout(mesa_layout)

        grupo = QGroupBox("Agregar platos al pedido")
        grupo_layout = QVBoxLayout(grupo)

        plato_row = QHBoxLayout()
        self.combo_plato = QComboBox()
        self.platos = obtener_platos()
        for plato in self.platos:
            if plato.disponible:
                self.combo_plato.addItem(f"{plato.nombre} (${plato.precio:.2f})", plato.id)
        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setRange(1, 50)
        self.spin_cantidad.setFixedWidth(60)
        btn_add = QPushButton("Agregar")
        btn_add.clicked.connect(self._agregar_a_lista)
        plato_row.addWidget(self.combo_plato)
        plato_row.addWidget(self.spin_cantidad)
        plato_row.addWidget(btn_add)
        grupo_layout.addLayout(plato_row)

        self.lista = QTableWidget()
        self.lista.setColumnCount(3)
        self.lista.setHorizontalHeaderLabels(["Plato", "Cant.", "Subtotal"])
        self.lista.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.lista.verticalHeader().setVisible(False)
        self.lista.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        grupo_layout.addWidget(self.lista)

        btn_quitar = QPushButton("Quitar seleccionado")
        btn_quitar.clicked.connect(self._quitar_de_lista)
        grupo_layout.addWidget(btn_quitar)
        layout.addWidget(grupo)

        self.lbl_total = QLabel("Total: $0.00")
        self.lbl_total.setStyleSheet("font-weight: bold; color: #a6e3a1;")
        layout.addWidget(self.lbl_total)

        botones = QHBoxLayout()
        btn_guardar = QPushButton("Crear Pedido")
        btn_cancelar = QPushButton("Cancelar")
        btn_guardar.setStyleSheet("background-color: #cba6f7; color: #1e1e2e; font-weight: bold; border-radius: 6px;")
        btn_guardar.clicked.connect(self._validar)
        btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_guardar)
        layout.addLayout(botones)

    def _agregar_a_lista(self):
        plato_id = self.combo_plato.currentData()
        cantidad = self.spin_cantidad.value()
        plato = next((p for p in self.platos if p.id == plato_id), None)
        if plato:
            self.platos_agregados.append((plato_id, cantidad))
            row = self.lista.rowCount()
            self.lista.insertRow(row)
            self.lista.setItem(row, 0, QTableWidgetItem(plato.nombre))
            self.lista.setItem(row, 1, QTableWidgetItem(str(cantidad)))
            self.lista.setItem(row, 2, QTableWidgetItem(f"${plato.precio * cantidad:.2f}"))
            self._actualizar_total()

    def _quitar_de_lista(self):
        fila = self.lista.currentRow()
        if fila >= 0:
            self.lista.removeRow(fila)
            self.platos_agregados.pop(fila)
            self._actualizar_total()

    def _actualizar_total(self):
        total = sum(
            next((p.precio for p in self.platos if p.id == pid), 0) * cant
            for pid, cant in self.platos_agregados
        )
        self.lbl_total.setText(f"Total: ${total:.2f}")

    def _validar(self):
        if not self.platos_agregados:
            QMessageBox.warning(self, "Aviso", "Agrega al menos un plato al pedido.")
            return
        self.accept()

    def obtener_datos(self):
        return self.combo_mesa.currentData(), self.platos_agregados

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI'; }
            QLabel { color: #cdd6f4; }
            QComboBox, QSpinBox {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px; padding: 4px 10px;
            }
            QGroupBox { color: #a6adc8; border: 1px solid #313244; border-radius: 8px; margin-top: 8px; padding-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; }
            QTableWidget { background-color: #181825; border: 1px solid #313244; border-radius: 6px; gridline-color: #252535; }
            QHeaderView::section { background-color: #252535; color: #cba6f7; border: none; padding: 4px; }
            QPushButton { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 5px 14px; }
            QPushButton:hover { background-color: #45475a; }
        """)


class AgregarPlatoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar Plato")
        self.setFixedSize(320, 160)
        self._build_ui()
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI'; }
            QLabel { color: #cdd6f4; }
            QComboBox, QSpinBox { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 4px 10px; }
            QPushButton { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 5px 14px; }
            QPushButton:hover { background-color: #45475a; }
        """)

    def _build_ui(self):
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        self.combo_plato = QComboBox()
        self.platos = obtener_platos()
        for plato in self.platos:
            if plato.disponible:
                self.combo_plato.addItem(f"{plato.nombre} (${plato.precio:.2f})", plato.id)
        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setRange(1, 50)
        layout.addRow("Plato:", self.combo_plato)
        layout.addRow("Cantidad:", self.spin_cantidad)
        botones = QHBoxLayout()
        btn_guardar = QPushButton("Agregar")
        btn_cancelar = QPushButton("Cancelar")
        btn_guardar.setStyleSheet("background-color: #cba6f7; color: #1e1e2e; font-weight: bold;")
        btn_guardar.clicked.connect(self.accept)
        btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_guardar)
        layout.addRow(botones)

    def obtener_datos(self):
        return self.combo_plato.currentData(), self.spin_cantidad.value()


class QuitarPlatoDialog(QDialog):
    """Diálogo para seleccionar qué plato quitar de la comanda."""
    def __init__(self, parent=None, items=None):
        super().__init__(parent)
        self.setWindowTitle("Quitar Plato")
        self.setFixedSize(340, 200)
        self._item_id = None
        self.items = items or []
        self._build_ui()
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI'; }
            QLabel { color: #cdd6f4; }
            QComboBox { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 4px 10px; }
            QPushButton { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 5px 14px; }
            QPushButton:hover { background-color: #45475a; }
        """)

    def _build_ui(self):
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        self.combo = QComboBox()
        for item in self.items:
            plato = obtener_plato_por_id(item.plato_id)
            nombre = plato.nombre if plato else f"Plato #{item.plato_id}"
            self.combo.addItem(f"{nombre}  ×{item.cantidad}", item.id)
        layout.addRow("Plato a quitar:", self.combo)
        botones = QHBoxLayout()
        btn_ok = QPushButton("Quitar")
        btn_cancelar = QPushButton("Cancelar")
        btn_ok.setStyleSheet("background-color: #f38ba8; color: #1e1e2e; font-weight: bold;")
        btn_ok.clicked.connect(self._confirmar)
        btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_ok)
        layout.addRow(botones)

    def _confirmar(self):
        self._item_id = self.combo.currentData()
        self.accept()

    def obtener_item_id(self):
        return self._item_id


class CambiarEstadoDialog(QDialog):
    def __init__(self, parent=None, estado_actual="abierto"):
        super().__init__(parent)
        self.setWindowTitle("Cambiar Estado")
        self.setFixedSize(280, 140)
        self._build_ui(estado_actual)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI'; }
            QLabel { color: #cdd6f4; }
            QComboBox { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 4px 10px; }
            QPushButton { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 5px 14px; }
            QPushButton:hover { background-color: #45475a; }
        """)

    def _build_ui(self, estado_actual):
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["abierto", "en preparación", "listo", "cerrado"])
        self.combo_estado.setCurrentText(estado_actual)
        layout.addRow("Nuevo estado:", self.combo_estado)
        botones = QHBoxLayout()
        btn_guardar = QPushButton("Guardar")
        btn_cancelar = QPushButton("Cancelar")
        btn_guardar.setStyleSheet("background-color: #cba6f7; color: #1e1e2e; font-weight: bold;")
        btn_guardar.clicked.connect(self.accept)
        btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_guardar)
        layout.addRow(botones)

    def obtener_estado(self):
        return self.combo_estado.currentText()