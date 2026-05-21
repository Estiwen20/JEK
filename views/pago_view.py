from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from datetime import datetime
import os, subprocess, sys

from repositories.pedido_repo import (
    obtener_pedidos, obtener_items_pedido,
    actualizar_estado_pedido
)
from repositories.factura_repo import (
    crear_factura, obtener_factura_por_pedido, obtener_facturas
)
from repositories.mesa_repo import obtener_mesa_por_id
from repositories.plato_repo import obtener_plato_por_id
from models.factura import Factura
from utils.helpers import generar_factura_pdf


class PagoView(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._cargar_pedidos_listos()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── Encabezado ──
        titulo = QLabel("Pagos y Facturación")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #cba6f7;")
        layout.addWidget(titulo)

        # ── Pedidos listos para pagar ──
        lbl_pendientes = QLabel("Pedidos listos para cobrar:")
        lbl_pendientes.setStyleSheet("font-size: 13px; color: #a6adc8;")
        layout.addWidget(lbl_pendientes)

        self.tabla_pedidos = QTableWidget()
        self.tabla_pedidos.setColumnCount(4)
        self.tabla_pedidos.setHorizontalHeaderLabels(["ID Pedido", "Mesa", "Fecha", "Total estimado"])
        self.tabla_pedidos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_pedidos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_pedidos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_pedidos.verticalHeader().setVisible(False)
        self.tabla_pedidos.clicked.connect(self._mostrar_detalle_pago)
        layout.addWidget(self.tabla_pedidos)

        # ── Detalle del pedido seleccionado ──
        lbl_detalle = QLabel("Detalle:")
        lbl_detalle.setStyleSheet("font-size: 13px; color: #a6adc8;")
        layout.addWidget(lbl_detalle)

        self.tabla_detalle = QTableWidget()
        self.tabla_detalle.setColumnCount(3)
        self.tabla_detalle.setHorizontalHeaderLabels(["Plato", "Cantidad", "Subtotal"])
        self.tabla_detalle.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_detalle.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_detalle.verticalHeader().setVisible(False)
        self.tabla_detalle.setMaximumHeight(160)
        layout.addWidget(self.tabla_detalle)

        self.lbl_total = QLabel("Total: $0.00")
        self.lbl_total.setStyleSheet("font-size: 15px; font-weight: bold; color: #a6e3a1;")
        layout.addWidget(self.lbl_total)

        # ── Botón pagar ──
        btn_layout = QHBoxLayout()
        self.btn_pagar = QPushButton("💳  Registrar Pago y Generar Factura")
        self.btn_pagar.setFixedHeight(42)
        self.btn_pagar.setStyleSheet("""
            background-color: #a6e3a1;
            color: #1e1e2e;
            font-weight: bold;
            font-size: 14px;
            border-radius: 8px;
        """)
        self.btn_pagar.clicked.connect(self._registrar_pago)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_pagar)
        layout.addLayout(btn_layout)

        # ── Historial de facturas ──
        lbl_historial = QLabel("Historial de facturas:")
        lbl_historial.setStyleSheet("font-size: 13px; color: #a6adc8; margin-top: 8px;")
        layout.addWidget(lbl_historial)

        self.tabla_facturas = QTableWidget()
        self.tabla_facturas.setColumnCount(4)
        self.tabla_facturas.setHorizontalHeaderLabels(["ID Factura", "Pedido", "Total", "Fecha de pago"])
        self.tabla_facturas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_facturas.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_facturas.verticalHeader().setVisible(False)
        layout.addWidget(self.tabla_facturas)

        btn_abrir = QPushButton("📄  Abrir factura PDF")
        btn_abrir.clicked.connect(self._abrir_factura_pdf)
        btn_abrir.setFixedWidth(180)
        layout.addWidget(btn_abrir, alignment=Qt.AlignmentFlag.AlignRight)

    # ── Carga ──

    def _cargar_pedidos_listos(self):
        self.pedidos = obtener_pedidos(filtro_estado="listo")
        self.tabla_pedidos.setRowCount(len(self.pedidos))
        for row, pedido in enumerate(self.pedidos):
            total = self._calcular_total(pedido.id)
            self.tabla_pedidos.setItem(row, 0, QTableWidgetItem(str(pedido.id)))
            self.tabla_pedidos.setItem(row, 1, QTableWidgetItem(str(pedido.mesa_id)))
            self.tabla_pedidos.setItem(row, 2, QTableWidgetItem(pedido.fecha))
            self.tabla_pedidos.setItem(row, 3, QTableWidgetItem(f"${total:.2f}"))
        self._cargar_historial()

    def _cargar_historial(self):
        facturas = obtener_facturas()
        self.tabla_facturas.setRowCount(len(facturas))
        for row, f in enumerate(facturas):
            self.tabla_facturas.setItem(row, 0, QTableWidgetItem(str(f.id)))
            self.tabla_facturas.setItem(row, 1, QTableWidgetItem(str(f.pedido_id)))
            self.tabla_facturas.setItem(row, 2, QTableWidgetItem(f"${f.total:.2f}"))
            self.tabla_facturas.setItem(row, 3, QTableWidgetItem(f.fecha_pago))

    def _calcular_total(self, pedido_id):
        items = obtener_items_pedido(pedido_id)
        total = 0.0
        for item in items:
            plato = obtener_plato_por_id(item.plato_id)
            if plato:
                total += plato.precio * item.cantidad
        return total

    def _mostrar_detalle_pago(self):
        pedido = self._pedido_seleccionado()
        if not pedido:
            return
        items = obtener_items_pedido(pedido.id)
        self.tabla_detalle.setRowCount(len(items))
        total = 0.0
        for row, item in enumerate(items):
            plato = obtener_plato_por_id(item.plato_id)
            nombre = plato.nombre if plato else "Desconocido"
            subtotal = (plato.precio if plato else 0) * item.cantidad
            total += subtotal
            self.tabla_detalle.setItem(row, 0, QTableWidgetItem(nombre))
            self.tabla_detalle.setItem(row, 1, QTableWidgetItem(str(item.cantidad)))
            self.tabla_detalle.setItem(row, 2, QTableWidgetItem(f"${subtotal:.2f}"))
        self.lbl_total.setText(f"Total: ${total:.2f}")

    # ── Helpers ──

    def _pedido_seleccionado(self):
        fila = self.tabla_pedidos.currentRow()
        if fila < 0:
            return None
        pedido_id = int(self.tabla_pedidos.item(fila, 0).text())
        return next((p for p in self.pedidos if p.id == pedido_id), None)

    # ── Pago ──

    def _registrar_pago(self):
        pedido = self._pedido_seleccionado()
        if not pedido:
            QMessageBox.warning(self, "Aviso", "Selecciona un pedido para cobrar.")
            return

        factura_existente = obtener_factura_por_pedido(pedido.id)
        if factura_existente:
            QMessageBox.information(self, "Info", "Este pedido ya tiene una factura registrada.")
            return

        total = self._calcular_total(pedido.id)
        confirmar = QMessageBox.question(
            self, "Confirmar pago",
            f"¿Registrar pago del pedido #{pedido.id}?\nTotal: ${total:.2f}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar != QMessageBox.StandardButton.Yes:
            return

        try:
            fecha_pago = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            crear_factura(pedido.id, total, fecha_pago)
            actualizar_estado_pedido(pedido.id, "cerrado")

            factura = obtener_factura_por_pedido(pedido.id)
            mesa = obtener_mesa_por_id(pedido.mesa_id)
            items = obtener_items_pedido(pedido.id)
            items_con_platos = [
                (obtener_plato_por_id(item.plato_id), item.cantidad)
                for item in items
                if obtener_plato_por_id(item.plato_id)
            ]

            ruta_pdf = generar_factura_pdf(factura, pedido, items_con_platos, mesa)

            QMessageBox.information(
                self, "Pago registrado",
                f"✅ Pago registrado correctamente.\nFactura guardada en:\n{ruta_pdf}"
            )
            self._cargar_pedidos_listos()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar el pago:\n{e}")

    def _abrir_factura_pdf(self):
        fila = self.tabla_facturas.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Aviso", "Selecciona una factura del historial.")
            return
        factura_id = self.tabla_facturas.item(fila, 0).text()
        ruta = os.path.join("facturas", f"factura_{factura_id}.pdf")
        if not os.path.exists(ruta):
            QMessageBox.warning(self, "Aviso", "No se encontró el archivo PDF.")
            return
        if sys.platform == "win32":
            os.startfile(ruta)
        elif sys.platform == "darwin":
            subprocess.call(["open", ruta])
        else:
            subprocess.call(["xdg-open", ruta])