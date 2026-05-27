from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QGridLayout,
    QGraphicsOpacityEffect, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor
from datetime import datetime
import matplotlib
import matplotlib.ticker
matplotlib.use("QtAgg")
import matplotlib 
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from backend.repositories.dashboard_repo import (
    obtener_ventas_por_hora_hoy,
    obtener_platos_mas_pedidos_hoy,
    obtener_pedidos_por_estado,
    obtener_ingresos_ultimos_7_dias,
    obtener_metricas_hoy,
)


BG       = "#1e1e2e"
BG_CARD  = "#181825"
BORDER   = "#313244"
PURPLE   = "#cba6f7"
BLUE     = "#89b4fa"
GREEN    = "#a6e3a1"
ORANGE   = "#fab387"
RED      = "#f38ba8"
MUTED    = "#585b70"
TEXT     = "#cdd6f4"


def _make_figure(w=4, h=2.2):
    fig = Figure(figsize=(w, h), facecolor=BG_CARD)
    ax = fig.add_subplot(111)
    ax.set_facecolor(BG_CARD)
    ax.tick_params(colors=MUTED, labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
    ax.yaxis.label.set_color(MUTED)
    ax.xaxis.label.set_color(MUTED)
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
        self._build_ui()
        self.refrescar()

        # Auto-refresh cada 30 segundos
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
        self.lbl_fecha = QLabel("")
        self.lbl_fecha.setStyleSheet(f"font-size: 11px; color: {MUTED};")

        btn_refresh = QPushButton("🔄  Actualizar")
        btn_refresh.setFixedWidth(130)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: {BORDER}; color: {TEXT};
                border: 1px solid #45475a; border-radius: 6px; padding: 7px 14px; font-size: 12px;
            }}
            QPushButton:hover {{ background: #45475a; }}
            QPushButton:pressed {{ background: {PURPLE}; color: {BG}; }}
        """)
        btn_refresh.clicked.connect(self.refrescar)

        header.addWidget(titulo)
        header.addWidget(self.lbl_fecha)
        header.addStretch()
        header.addWidget(btn_refresh)
        self.layout_main.addLayout(header)

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

        self.layout_main.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    def refrescar(self):
        self.lbl_fecha.setText(
            datetime.now().strftime("Hoy — %d de %B de %Y · %H:%M")
        )
        self._actualizar_metricas()
        self._actualizar_graficas()

    def _limpiar_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _actualizar_metricas(self):
        self._limpiar_layout(self.metrics_layout)
        m = obtener_metricas_hoy()

        tarjetas = [
            ("Ventas hoy",      f"${m['ventas_hoy']:,.0f}",                          "ingresos del día",              GREEN),
            ("Pedidos activos", str(m["pedidos_activos"]),                            f"{m['pedidos_listos']} listos", BLUE),
            ("Mesas ocupadas",  f"{m['mesas_ocupadas']} / {m['total_mesas']}",        "ocupación actual",              RED),
            ("Facturas hoy",    str(m["facturas_hoy"]),                               "emitidas hoy",                  PURPLE),
        ]
        for label, val, sub, color in tarjetas:
            card = MetricCard(label, val, sub, color)
            card.setFixedHeight(90)
            self.metrics_layout.addWidget(card)

    def _actualizar_graficas(self):
        self._limpiar_layout(self.row1)
        self._limpiar_layout(self.row2)

        # ── Gráfica 1: Ventas por hora ──
        ventas_hora = obtener_ventas_por_hora_hoy()
        horas = [f"{h}h" for h in range(8, 23)]
        valores = [ventas_hora.get(f"{h:02d}", 0) for h in range(8, 23)]

        fig1, ax1 = _make_figure(5, 2.4)
        ax1.plot(horas, valores, color=GREEN, linewidth=2, marker="o",
                 markersize=4, markerfacecolor=GREEN)
        ax1.fill_between(range(len(horas)), valores, alpha=0.08, color=GREEN)
        ax1.set_xticks(range(len(horas)))
        ax1.set_xticklabels(horas, rotation=45, fontsize=7)
        ax1.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k")
        )
        ax1.grid(axis="y", color=BORDER, linewidth=0.5)
        canvas1 = FigureCanvas(fig1)
        canvas1.setFixedHeight(200)
        self.row1.addWidget(ChartCard("Ventas por hora", canvas1))

        # ── Gráfica 2: Platos más pedidos (donut) ──
        platos_data = obtener_platos_mas_pedidos_hoy()
        if platos_data:
            nombres = [p[0][:14] for p in platos_data]
            cantidades = [p[1] for p in platos_data]
            colores_donut = [PURPLE, BLUE, GREEN, ORANGE, RED][:len(nombres)]

            fig2, ax2 = _make_figure(3.5, 2.4)
            wedges, _ = ax2.pie(
                cantidades, colors=colores_donut,
                wedgeprops={"width": 0.55, "edgecolor": BG_CARD, "linewidth": 2},
                startangle=90
            )
            ax2.legend(
                wedges, [f"{n} ({c})" for n, c in zip(nombres, cantidades)],
                loc="center left", bbox_to_anchor=(0.85, 0.5),
                fontsize=7, frameon=False,
                labelcolor=TEXT
            )
        else:
            fig2, ax2 = _make_figure(3.5, 2.4)
            ax2.text(0.5, 0.5, "Sin datos hoy", ha="center", va="center",
                     color=MUTED, fontsize=10)
            ax2.axis("off")

        canvas2 = FigureCanvas(fig2)
        canvas2.setFixedHeight(200)
        self.row1.addWidget(ChartCard("Platos más pedidos", canvas2))

        # ── Gráfica 3: Pedidos por estado ──
        estados_data = obtener_pedidos_por_estado()
        estados = ["abierto", "en preparación", "listo"]
        estado_labels = ["Abierto", "En prep.", "Listo"]
        estado_vals = [estados_data.get(e, 0) for e in estados]
        estado_colores = [BLUE, ORANGE, GREEN]

        fig3, ax3 = _make_figure(3.5, 2.4)
        bars = ax3.bar(
            estado_labels, estado_vals,
            color=estado_colores,
            width=0.5,
            zorder=2
        )
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
        canvas3.setFixedHeight(200)
        self.row2.addWidget(ChartCard("Pedidos por estado", canvas3))

        # ── Gráfica 4: Ingresos últimos 7 días ──
        semana = obtener_ingresos_ultimos_7_dias()
        dias_labels = []
        for fecha, _ in semana:
            from datetime import datetime as dt
            d = dt.strptime(fecha, "%Y-%m-%d")
            dias_labels.append(d.strftime("%a %d"))
        ingresos = [v for _, v in semana]
        bar_colors = [PURPLE if i == 6 else "#3d3555" for i in range(7)]

        fig4, ax4 = _make_figure(5, 2.4)
        ax4.bar(dias_labels, ingresos, color=bar_colors, width=0.6, zorder=2)
        ax4.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k")
        )
        ax4.grid(axis="y", color=BORDER, linewidth=0.5, zorder=0)
        ax4.set_axisbelow(True)
        ax4.tick_params(axis="x", rotation=30, labelsize=7)

        canvas4 = FigureCanvas(fig4)
        canvas4.setFixedHeight(200)
        self.row2.addWidget(ChartCard("Ingresos últimos 7 días", canvas4))