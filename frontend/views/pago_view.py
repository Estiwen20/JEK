from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from datetime import datetime
import os, subprocess, sys

from backend.repositories.pedido_repo import (
    obtener_pedidos, obtener_items_pedido,
    actualizar_estado_pedido
)
from backend.repositories.factura_repo import (
    crear_factura, obtener_factura_por_pedido, obtener_facturas
)
from backend.repositories.mesa_repo import obtener_mesa_por_id
from backend.repositories.plato_repo import obtener_plato_por_id
from frontend.utils.helpers import generar_factura_pdf


class PagoView(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._cargar_mesas_con_pedidos()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── Encabezado ──
        header = QHBoxLayout()
        titulo = QLabel("Pagos y Facturación")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #cba6f7;")
        btn_actualizar = QPushButton("🔄  Actualizar")
        btn_actualizar.setFixedWidth(130)
        btn_actualizar.clicked.connect(self._actualizar)
        header.addWidget(titulo)
        header.addStretch()
        header.addWidget(btn_actualizar)
        layout.addLayout(header)

        # ── Mesas listas para cobrar ──
        lbl_pendientes = QLabel("Mesas listas para cobrar:")
        lbl_pendientes.setStyleSheet("font-size: 13px; color: #a6adc8;")
        layout.addWidget(lbl_pendientes)

        self.tabla_mesas = QTableWidget()
        self.tabla_mesas.setColumnCount(4)
        self.tabla_mesas.setHorizontalHeaderLabels(["Mesa", "N° Pedidos", "Fecha último pedido", "Total"])
        self.tabla_mesas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_mesas.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_mesas.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_mesas.verticalHeader().setVisible(False)
        self.tabla_mesas.clicked.connect(self._mostrar_detalle_mesa)
        layout.addWidget(self.tabla_mesas)

        # ── Detalle de pedidos de la mesa seleccionada ──
        lbl_detalle = QLabel("Detalle:")
        lbl_detalle.setStyleSheet("font-size: 13px; color: #a6adc8;")
        layout.addWidget(lbl_detalle)

        self.tabla_detalle = QTableWidget()
        self.tabla_detalle.setColumnCount(4)
        self.tabla_detalle.setHorizontalHeaderLabels(["Pedido #", "Plato", "Cantidad", "Subtotal"])
        self.tabla_detalle.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_detalle.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_detalle.verticalHeader().setVisible(False)
        self.tabla_detalle.setMaximumHeight(180)
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

    def _actualizar(self):
        self._cargar_mesas_con_pedidos()
        self.tabla_detalle.setRowCount(0)
        self.lbl_total.setText("Total: $0.00")

    def _cargar_mesas_con_pedidos(self):
        """Agrupa todos los pedidos 'listo' por mesa."""
        pedidos = obtener_pedidos(filtro_estado="listo")

        # Agrupar por mesa_id
        self.grupos = {}  # mesa_id -> [pedidos]
        for p in pedidos:
            self.grupos.setdefault(p.mesa_id, []).append(p)

        self.tabla_mesas.setRowCount(len(self.grupos))
        for row, (mesa_id, pedidos_mesa) in enumerate(self.grupos.items()):
            mesa = obtener_mesa_por_id(mesa_id)
            total = sum(self._calcular_total(p.id) for p in pedidos_mesa)
            fecha_ultimo = max(p.fecha for p in pedidos_mesa)
            nombre_mesa = f"Mesa #{mesa.numero}" if mesa else f"Mesa ID {mesa_id}"

            item_mesa = QTableWidgetItem(nombre_mesa)
            item_mesa.setData(Qt.ItemDataRole.UserRole, mesa_id)  # guardamos mesa_id
            self.tabla_mesas.setItem(row, 0, item_mesa)
            self.tabla_mesas.setItem(row, 1, QTableWidgetItem(str(len(pedidos_mesa))))
            self.tabla_mesas.setItem(row, 2, QTableWidgetItem(fecha_ultimo))
            self.tabla_mesas.setItem(row, 3, QTableWidgetItem(f"${total:.2f}"))

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

    def _mostrar_detalle_mesa(self):
        mesa_id = self._mesa_id_seleccionada()
        if mesa_id is None:
            return

        pedidos_mesa = self.grupos.get(mesa_id, [])
        filas = []
        total = 0.0
        for pedido in pedidos_mesa:
            items = obtener_items_pedido(pedido.id)
            for item in items:
                plato = obtener_plato_por_id(item.plato_id)
                nombre = plato.nombre if plato else "Desconocido"
                subtotal = (plato.precio if plato else 0) * item.cantidad
                total += subtotal
                filas.append((pedido.id, nombre, item.cantidad, subtotal))

        self.tabla_detalle.setRowCount(len(filas))
        for row, (pid, nombre, cantidad, subtotal) in enumerate(filas):
            item_pid = QTableWidgetItem(str(pid))
            item_pid.setForeground(QColor("#cba6f7"))
            self.tabla_detalle.setItem(row, 0, item_pid)
            self.tabla_detalle.setItem(row, 1, QTableWidgetItem(nombre))
            self.tabla_detalle.setItem(row, 2, QTableWidgetItem(str(cantidad)))
            self.tabla_detalle.setItem(row, 3, QTableWidgetItem(f"${subtotal:.2f}"))

        self.lbl_total.setText(f"Total: ${total:.2f}")

    # ── Helpers ──

    def _mesa_id_seleccionada(self):
        fila = self.tabla_mesas.currentRow()
        if fila < 0:
            return None
        item = self.tabla_mesas.item(fila, 0)
        if not item:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    # ── Pago ──

    def _registrar_pago(self):
        mesa_id = self._mesa_id_seleccionada()
        if mesa_id is None:
            QMessageBox.warning(self, "Aviso", "Selecciona una mesa para cobrar.")
            return

        pedidos_mesa = self.grupos.get(mesa_id, [])
        if not pedidos_mesa:
            QMessageBox.warning(self, "Aviso", "No hay pedidos listos para esta mesa.")
            return

        # Verificar que ninguno ya tenga factura
        ya_facturados = [p for p in pedidos_mesa if obtener_factura_por_pedido(p.id)]
        if ya_facturados:
            QMessageBox.information(self, "Info",
                f"{len(ya_facturados)} pedido(s) ya tienen factura registrada.")
            return

        total = sum(self._calcular_total(p.id) for p in pedidos_mesa)
        mesa = obtener_mesa_por_id(mesa_id)
        nombre_mesa = f"Mesa #{mesa.numero}" if mesa else f"Mesa ID {mesa_id}"
        n_pedidos = len(pedidos_mesa)

        confirmar = QMessageBox.question(
            self, "Confirmar pago",
            f"¿Registrar pago de {nombre_mesa}?\n"
            f"Pedidos incluidos: {n_pedidos}\n"
            f"Total: ${total:.2f}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar != QMessageBox.StandardButton.Yes:
            return

        try:
            fecha_pago = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Recolectar todos los items de todos los pedidos
            todos_items_con_platos = []
            for pedido in pedidos_mesa:
                items = obtener_items_pedido(pedido.id)
                for item in items:
                    plato = obtener_plato_por_id(item.plato_id)
                    if plato:
                        todos_items_con_platos.append((plato, item.cantidad))

            # Crear una factura por el total (asociada al primer pedido)
            pedido_principal = pedidos_mesa[0]
            crear_factura(pedido_principal.id, total, fecha_pago)
            factura = obtener_factura_por_pedido(pedido_principal.id)

            # Cerrar todos los pedidos de la mesa
            for pedido in pedidos_mesa:
                actualizar_estado_pedido(pedido.id, "cerrado")

            # Generar UN solo PDF con todos los items
            ruta_pdf = generar_factura_pdf(
                factura, pedido_principal,
                todos_items_con_platos, mesa
            )

            QMessageBox.information(
                self, "Pago registrado",
                f"✅ Pago registrado correctamente.\n"
                f"{n_pedidos} pedido(s) cerrados.\n"
                f"Factura guardada en:\n{ruta_pdf}"
            )
            self._cargar_mesas_con_pedidos()
            self.tabla_detalle.setRowCount(0)
            self.lbl_total.setText("Total: $0.00")

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
