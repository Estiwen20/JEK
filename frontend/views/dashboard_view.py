import matplotlib
import matplotlib.ticker
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame,
    QGraphicsOpacityEffect, QDateEdit,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, QDate, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor
from datetime import datetime, timedelta

from backend.repositories.dashboard_repo import (
    obtener_ventas_por_hora,
    obtener_platos_mas_pedidos,
    obtener_pedidos_por_estado,
    obtener_ingresos_rango,
    obtener_metricas,
    obtener_facturas_rango,
)

BG      = "#1e1e2e"
BG_CARD = "#181825"
BORDER  = "#313244"
PURPLE  = "#cba6f7"
BLUE    = "#89b4fa"
GREEN   = "#a6e3a1"
ORANGE  = "#fab387"
RED     = "#f38ba8"
MUTED   = "#585b70"
TEXT    = "#cdd6f4"


def _make_figure(w=4, h=2.2):
    fig = Figure(figsize=(w, h), facecolor=BG_CARD)
    ax = fig.add_subplot(111)
    ax.set_facecolor(BG_CARD)
    ax.tick_params(colors=MUTED, labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
    fig.tight_layout(pad=1.2)
    return fig, ax


class MetricCard(QFrame):
    def __init__(self, label, valor, sub, color, parent=None):
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.setStyleSheet(f"""
            #metricCard {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-left: 3px solid {color};
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        lbl = QLabel(label.upper())
        lbl.setStyleSheet(f"font-size: 10px; color: {MUTED}; letter-spacing: 1px; border: none; background: transparent;")
        val = QLabel(valor)
        val.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color}; border: none; background: transparent;")
        sub_lbl = QLabel(sub)
        sub_lbl.setStyleSheet(f"font-size: 10px; color: {MUTED}; border: none; background: transparent;")

        layout.addWidget(lbl)
        layout.addWidget(val)
        layout.addWidget(sub_lbl)


class ChartCard(QFrame):
    def __init__(self, titulo, canvas, parent=None):
        super().__init__(parent)
        self.setObjectName("chartCard")
        self.setStyleSheet(f"""
            #chartCard {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        lbl = QLabel(titulo.upper())
        lbl.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {MUTED}; letter-spacing: 1px; border: none; background: transparent;")
        layout.addWidget(lbl)
        layout.addWidget(canvas)


class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self.fecha_inicio = datetime.now().strftime("%Y-%m-%d")
        self.fecha_fin = datetime.now().strftime("%Y-%m-%d")
        self._build_ui()
        self.refrescar()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refrescar)
        self._timer.start(30000)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        container = QWidget()
        container.setStyleSheet(f"background: {BG};")
        self.layout_main = QVBoxLayout(container)
        self.layout_main.setContentsMargins(24, 24, 24, 24)
        self.layout_main.setSpacing(16)

        # ── Encabezado ──
        header = QHBoxLayout()
        titulo = QLabel("Dashboard")
        titulo.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {PURPLE};")
        self.lbl_rango = QLabel("")
        self.lbl_rango.setStyleSheet(f"font-size: 11px; color: {MUTED};")
        header.addWidget(titulo)
        header.addWidget(self.lbl_rango)
        header.addStretch()
        self.layout_main.addLayout(header)

        # ── Controles de fecha ──
        fecha_row = QHBoxLayout()
        fecha_row.setSpacing(8)

        # Botones rápidos
        for label, dias in [("Hoy", 0), ("Ayer", 1), ("7 días", 6), ("30 días", 29)]:
            btn = QPushButton(label)
            btn.setFixedHeight(30)
            btn.setFixedWidth(70)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {BORDER}; color: {TEXT};
                    border: 1px solid #45475a; border-radius: 6px; font-size: 11px;
                }}
                QPushButton:hover {{ background: #45475a; }}
                QPushButton:pressed {{ background: {PURPLE}; color: {BG}; }}
            """)
            d = dias
            btn.clicked.connect(lambda _, d=d: self._aplicar_rapido(d))
            fecha_row.addWidget(btn)

        fecha_row.addSpacing(16)

        # Desde
        lbl_desde = QLabel("Desde:")
        lbl_desde.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(QDate.currentDate())
        self.date_desde.setFixedHeight(30)
        self.date_desde.setStyleSheet(f"""
            QDateEdit {{
                background: {BORDER}; color: {TEXT};
                border: 1px solid #45475a; border-radius: 6px;
                padding: 2px 8px; font-size: 11px;
            }}
            QDateEdit:focus {{ border: 1px solid {PURPLE}; }}
        """)

        # Hasta
        lbl_hasta = QLabel("Hasta:")
        lbl_hasta.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(QDate.currentDate())
        self.date_hasta.setFixedHeight(30)
        self.date_hasta.setStyleSheet(self.date_desde.styleSheet())

        btn_aplicar = QPushButton("Aplicar")
        btn_aplicar.setFixedHeight(30)
        btn_aplicar.setFixedWidth(80)
        btn_aplicar.setStyleSheet(f"""
            QPushButton {{
                background: {PURPLE}; color: {BG};
                border: none; border-radius: 6px; font-size: 11px; font-weight: bold;
            }}
            QPushButton:hover {{ background: #b48ef0; }}
        """)
        btn_aplicar.clicked.connect(self._aplicar_rango)

        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedSize(30, 30)
        btn_refresh.setToolTip("Actualizar")
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: {BORDER}; color: {TEXT};
                border: 1px solid #45475a; border-radius: 6px; font-size: 13px;
            }}
            QPushButton:hover {{ background: #45475a; }}
        """)
        btn_refresh.clicked.connect(self.refrescar)

        fecha_row.addWidget(lbl_desde)
        fecha_row.addWidget(self.date_desde)
        fecha_row.addWidget(lbl_hasta)
        fecha_row.addWidget(self.date_hasta)
        fecha_row.addWidget(btn_aplicar)
        fecha_row.addSpacing(8)
        fecha_row.addWidget(btn_refresh)
        fecha_row.addStretch()
        self.layout_main.addLayout(fecha_row)

        # ── Separador ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {BORDER}; border: none; max-height: 1px;")
        self.layout_main.addWidget(sep)

        # ── Métricas ──
        self.metrics_layout = QHBoxLayout()
        self.metrics_layout.setSpacing(10)
        self.layout_main.addLayout(self.metrics_layout)

        # ── Fila 1 gráficas ──
        self.row1 = QHBoxLayout()
        self.row1.setSpacing(12)
        self.layout_main.addLayout(self.row1)

        # ── Fila 2 gráficas ──
        self.row2 = QHBoxLayout()
        self.row2.setSpacing(12)
        self.layout_main.addLayout(self.row2)

        # ── Comparativa hoy vs ayer ──
        self.row3 = QHBoxLayout()
        self.row3.setSpacing(12)
        self.layout_main.addLayout(self.row3)

        # ── Tabla de facturas ──
        lbl_fact = QLabel("FACTURAS DEL PERÍODO")
        lbl_fact.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {MUTED}; letter-spacing: 1px;")
        self.layout_main.addWidget(lbl_fact)

        self.tabla_facturas = QTableWidget()
        self.tabla_facturas.setColumnCount(5)
        self.tabla_facturas.setHorizontalHeaderLabels(
            ["Factura", "Pedido", "Mesa", "Total", "Fecha y hora"]
        )
        self.tabla_facturas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_facturas.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_facturas.verticalHeader().setVisible(False)
        self.tabla_facturas.setMaximumHeight(200)
        self.tabla_facturas.setStyleSheet(f"""
            QTableWidget {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 8px;
                gridline-color: {BORDER};
            }}
            QHeaderView::section {{
                background: #252535;
                color: {PURPLE};
                border: none;
                padding: 6px;
                font-weight: bold;
                font-size: 11px;
            }}
            QTableWidget::item:selected {{ background: #2a2a42; color: {PURPLE}; }}
        """)
        self.layout_main.addWidget(self.tabla_facturas)
        self.layout_main.addStretch()

        scroll.setWidget(container)
        outer.addWidget(scroll)

    # ── Navegación ──

    def _aplicar_rapido(self, dias_atras):
        hoy = QDate.currentDate()
        inicio = hoy.addDays(-dias_atras)
        self.date_desde.setDate(inicio)
        self.date_hasta.setDate(hoy)
        self._aplicar_rango()

    def _aplicar_rango(self):
        self.fecha_inicio = self.date_desde.date().toString("yyyy-MM-dd")
        self.fecha_fin = self.date_hasta.date().toString("yyyy-MM-dd")
        self.refrescar()

    # ── Refresco ──

    def refrescar(self):
        self.fecha_inicio = self.date_desde.date().toString("yyyy-MM-dd")
        self.fecha_fin = self.date_hasta.date().toString("yyyy-MM-dd")

        if self.fecha_inicio == self.fecha_fin:
            fecha_fmt = datetime.strptime(self.fecha_inicio, "%Y-%m-%d").strftime("%d de %B de %Y")
            self.lbl_rango.setText(f"📅  {fecha_fmt}")
        else:
            ini_fmt = datetime.strptime(self.fecha_inicio, "%Y-%m-%d").strftime("%d %b")
            fin_fmt = datetime.strptime(self.fecha_fin, "%Y-%m-%d").strftime("%d %b %Y")
            self.lbl_rango.setText(f"📅  {ini_fmt} — {fin_fmt}")

        self._actualizar_metricas()
        self._actualizar_graficas()
        self._actualizar_tabla_facturas()

    def _limpiar_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ── Métricas ──

    def _actualizar_metricas(self):
        self._limpiar_layout(self.metrics_layout)
        m = obtener_metricas(self.fecha_inicio, self.fecha_fin)

        variacion = m["variacion"]
        if variacion > 0:
            var_txt = f"↑ {variacion:.1f}% vs período anterior"
            var_color = GREEN
        elif variacion < 0:
            var_txt = f"↓ {abs(variacion):.1f}% vs período anterior"
            var_color = RED
        else:
            var_txt = "Sin cambio vs período anterior"
            var_color = MUTED

        tarjetas = [
            ("Ventas",         f"${m['ventas']:,.0f}",                        var_txt,                GREEN),
            ("Pedidos activos",str(m["pedidos_activos"]),                      f"{m['pedidos_listos']} listos", BLUE),
            ("Mesas ocupadas", f"{m['mesas_ocupadas']} / {m['total_mesas']}",  "ocupación actual",     RED),
            ("Facturas",       str(m["facturas"]),                             "en el período",        PURPLE),
        ]
        for label, val, sub, color in tarjetas:
            if label == "Ventas":
                card = MetricCard(label, val, var_txt, color)
            else:
                card = MetricCard(label, val, sub, color)
            card.setFixedHeight(90)
            self.metrics_layout.addWidget(card)

    # ── Gráficas ──

    def _actualizar_graficas(self):
        self._limpiar_layout(self.row1)
        self._limpiar_layout(self.row2)
        self._limpiar_layout(self.row3)

        es_un_dia = self.fecha_inicio == self.fecha_fin

        # ── Gráfica 1: Ventas por hora (si es un día) o por día (si es rango) ──
        fig1, ax1 = _make_figure(5, 2.4)
        if es_un_dia:
            ventas_hora = obtener_ventas_por_hora(self.fecha_inicio)
            horas = [f"{h}h" for h in range(8, 23)]
            valores = [ventas_hora.get(f"{h:02d}", 0) for h in range(8, 23)]
            ax1.plot(horas, valores, color=GREEN, linewidth=2,
                     marker="o", markersize=4, markerfacecolor=GREEN)
            ax1.fill_between(range(len(horas)), valores, alpha=0.1, color=GREEN)
            ax1.set_xticks(range(len(horas)))
            ax1.set_xticklabels(horas, rotation=45, fontsize=7)
            titulo1 = "Ventas por hora"
        else:
            semana = obtener_ingresos_rango(self.fecha_inicio, self.fecha_fin)
            dias_labels = [
                datetime.strptime(f, "%Y-%m-%d").strftime("%d %b")
                for f, _ in semana
            ]
            valores = [v for _, v in semana]
            ax1.plot(dias_labels, valores, color=GREEN, linewidth=2,
                     marker="o", markersize=4, markerfacecolor=GREEN)
            ax1.fill_between(range(len(dias_labels)), valores, alpha=0.1, color=GREEN)
            ax1.set_xticks(range(len(dias_labels)))
            ax1.set_xticklabels(dias_labels, rotation=45, fontsize=7)
            titulo1 = "Ventas por día"

        ax1.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k")
        )
        ax1.grid(axis="y", color=BORDER, linewidth=0.5)
        canvas1 = FigureCanvas(fig1)
        canvas1.setFixedHeight(210)
        self.row1.addWidget(ChartCard(titulo1, canvas1))

        # ── Gráfica 2: Platos más pedidos ──
        platos_data = obtener_platos_mas_pedidos(self.fecha_inicio, self.fecha_fin)
        fig2, ax2 = _make_figure(3.5, 2.4)
        if platos_data:
            nombres = [p[0][:14] for p in platos_data]
            cantidades = [p[1] for p in platos_data]
            colores_donut = [PURPLE, BLUE, GREEN, ORANGE, RED][:len(nombres)]
            wedges, _ = ax2.pie(
                cantidades, colors=colores_donut,
                wedgeprops={"width": 0.55, "edgecolor": BG_CARD, "linewidth": 2},
                startangle=90
            )
            ax2.legend(
                wedges, [f"{n} ({c})" for n, c in zip(nombres, cantidades)],
                loc="center left", bbox_to_anchor=(0.82, 0.5),
                fontsize=7, frameon=False, labelcolor=TEXT
            )
        else:
            ax2.text(0.5, 0.5, "Sin datos", ha="center", va="center",
                     color=MUTED, fontsize=10)
            ax2.axis("off")
        canvas2 = FigureCanvas(fig2)
        canvas2.setFixedHeight(210)
        self.row1.addWidget(ChartCard("Platos más pedidos", canvas2))

        # ── Gráfica 3: Pedidos por estado ──
        estados_data = obtener_pedidos_por_estado()
        estados = ["abierto", "en preparación", "listo"]
        estado_labels = ["Abierto", "En prep.", "Listo"]
        estado_vals = [estados_data.get(e, 0) for e in estados]
        estado_colores = [BLUE, ORANGE, GREEN]

        fig3, ax3 = _make_figure(3.5, 2.4)
        bars = ax3.bar(estado_labels, estado_vals,
                       color=estado_colores, width=0.5, zorder=2)
        for bar, val in zip(bars, estado_vals):
            if val > 0:
                ax3.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.1,
                    str(val), ha="center", va="bottom",
                    color=TEXT, fontsize=9
                )
        ax3.set_ylim(0, max(estado_vals + [1]) + 2)
        ax3.grid(axis="y", color=BORDER, linewidth=0.5, zorder=0)
        ax3.set_axisbelow(True)
        canvas3 = FigureCanvas(fig3)
        canvas3.setFixedHeight(210)
        self.row2.addWidget(ChartCard("Pedidos por estado", canvas3))

        # ── Gráfica 4: Ingresos últimos 7 días (siempre fija para contexto) ──
        semana = obtener_ingresos_rango(
            (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d"),
            datetime.now().strftime("%Y-%m-%d")
        )
        dias_labels = [
            datetime.strptime(f, "%Y-%m-%d").strftime("%a %d")
            for f, _ in semana
        ]
        ingresos = [v for _, v in semana]
        hoy_str = datetime.now().strftime("%Y-%m-%d")
        bar_colors = [
            PURPLE if semana[i][0] == hoy_str else "#3d3555"
            for i in range(len(semana))
        ]

        fig4, ax4 = _make_figure(5, 2.4)
        ax4.bar(dias_labels, ingresos, color=bar_colors, width=0.6, zorder=2)
        ax4.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k")
        )
        ax4.grid(axis="y", color=BORDER, linewidth=0.5, zorder=0)
        ax4.set_axisbelow(True)
        ax4.tick_params(axis="x", rotation=30, labelsize=7)
        canvas4 = FigureCanvas(fig4)
        canvas4.setFixedHeight(210)
        self.row2.addWidget(ChartCard("Últimos 7 días", canvas4))

        # ── Comparativa hoy vs ayer ──
        hoy = datetime.now().strftime("%Y-%m-%d")
        ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        m_hoy = obtener_metricas(hoy, hoy)
        m_ayer = obtener_metricas(ayer, ayer)

        fig5, ax5 = _make_figure(8, 2.0)
        categorias = ["Ventas", "Pedidos", "Facturas"]
        vals_hoy = [m_hoy["ventas"] / 1000, m_hoy["pedidos_activos"], m_hoy["facturas"]]
        vals_ayer = [m_ayer["ventas"] / 1000, m_ayer["pedidos_activos"], m_ayer["facturas"]]

        x = range(len(categorias))
        ancho = 0.35
        ax5.bar([i - ancho/2 for i in x], vals_hoy,
                width=ancho, color=PURPLE, label="Hoy",
                zorder=2, alpha=0.9)
        ax5.bar([i + ancho/2 for i in x], vals_ayer,
                width=ancho, color="#3d3555", label="Ayer",
                zorder=2, alpha=0.9)
        ax5.set_xticks(list(x))
        ax5.set_xticklabels(categorias, fontsize=9)
        ax5.legend(fontsize=8, frameon=False, labelcolor=TEXT)
        ax5.grid(axis="y", color=BORDER, linewidth=0.5, zorder=0)
        ax5.set_axisbelow(True)
        canvas5 = FigureCanvas(fig5)
        canvas5.setFixedHeight(180)
        self.row3.addWidget(ChartCard("Comparativa hoy vs ayer", canvas5))

    # ── Tabla facturas ──

    def _actualizar_tabla_facturas(self):
        facturas = obtener_facturas_rango(self.fecha_inicio, self.fecha_fin)
        self.tabla_facturas.setRowCount(len(facturas))
        for row, f in enumerate(facturas):
            self.tabla_facturas.setItem(row, 0, QTableWidgetItem(str(f["id"])))
            self.tabla_facturas.setItem(row, 1, QTableWidgetItem(str(f["pedido_id"])))
            self.tabla_facturas.setItem(row, 2, QTableWidgetItem(f"#{f['mesa_numero']}"))
            total_item = QTableWidgetItem(f"${f['total']:,.0f}")
            total_item.setForeground(QColor(GREEN))
            self.tabla_facturas.setItem(row, 3, total_item)
            self.tabla_facturas.setItem(row, 4, QTableWidgetItem(f["fecha_pago"]))