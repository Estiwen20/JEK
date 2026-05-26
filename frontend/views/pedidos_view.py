from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QComboBox, QMessageBox,
    QHeaderView, QSpinBox, QListWidget, QListWidgetItem,
    QSplitter, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
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


class PedidosView(QWidget):
    def __init__(self, usuario=None):
        super().__init__()
        self.usuario = usuario
        self._build_ui()
        self._cargar_pedidos()

    def _es_admin(self):
        return self.usuario is not None and self.usuario.es_admin()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        titulo = QLabel("Gestión de Pedidos")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #cba6f7;")
        header.addWidget(titulo)
        header.addStretch()

        # Tanto admin como mesero pueden crear pedidos
        btn_nuevo = QPushButton("+ Nuevo Pedido")
        btn_nuevo.setFixedWidth(150)
        btn_nuevo.setStyleSheet("background-color: #cba6f7; color: #1e1e2e; font-weight: bold; border-radius: 6px; padding: 7px;")
        btn_nuevo.clicked.connect(self._abrir_dialog_crear)
        header.addWidget(btn_nuevo)
        layout.addLayout(header)

        filtros = QHBoxLayout()
        self.filtro_estado = QComboBox()
        self.filtro_estado.addItems(["Todos", "abierto", "en preparación", "listo", "cerrado"])
        self.filtro_estado.currentTextChanged.connect(self._cargar_pedidos)

        self.filtro_mesa = QComboBox()
        self.filtro_mesa.addItem("Todas las mesas", None)
        for mesa in obtener_mesas():
            self.filtro_mesa.addItem(f"Mesa #{mesa.numero}", mesa.id)
        self.filtro_mesa.currentIndexChanged.connect(self._cargar_pedidos)

        filtros.addWidget(QLabel("Estado:"))
        filtros.addWidget(self.filtro_estado)
        filtros.addSpacing(16)
        filtros.addWidget(QLabel("Mesa:"))
        filtros.addWidget(self.filtro_mesa)
        filtros.addStretch()
        layout.addLayout(filtros)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Mesa", "Estado", "Fecha", "🔔"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(4, 54)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.clicked.connect(self._mostrar_detalle)
        splitter.addWidget(self.tabla)

        detalle_widget = QWidget()
        detalle_layout = QVBoxLayout(detalle_widget)
        detalle_layout.setContentsMargins(12, 0, 0, 0)

        lbl_detalle = QLabel("Detalle del pedido")
        lbl_detalle.setStyleSheet("font-size: 15px; font-weight: bold; color: #cba6f7;")
        detalle_layout.addWidget(lbl_detalle)

        self.lista_items = QTableWidget()
        self.lista_items.setColumnCount(3)
        self.lista_items.setHorizontalHeaderLabels(["Plato", "Cantidad", "Subtotal"])
        self.lista_items.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.lista_items.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.lista_items.verticalHeader().setVisible(False)
        detalle_layout.addWidget(self.lista_items)

        self.lbl_total = QLabel("Total: $0.00")
        self.lbl_total.setStyleSheet("font-size: 14px; font-weight: bold; color: #a6e3a1;")
        detalle_layout.addWidget(self.lbl_total)

        splitter.addWidget(detalle_widget)
        splitter.setSizes([500, 350])
        layout.addWidget(splitter)

        # ── Botones de acción según rol ──
        acciones = QHBoxLayout()
        acciones.addStretch()

        # Mesero y admin pueden agregar/quitar platos y cambiar estado
        btn_agregar_plato = QPushButton("➕  Agregar plato")
        btn_quitar_plato = QPushButton("➖  Quitar plato")
        btn_estado = QPushButton("🔄  Cambiar estado")

        btn_agregar_plato.clicked.connect(self._agregar_plato)
        btn_quitar_plato.clicked.connect(self._quitar_plato)
        btn_estado.clicked.connect(self._cambiar_estado)

        acciones.addWidget(btn_agregar_plato)
        acciones.addWidget(btn_quitar_plato)
        acciones.addWidget(btn_estado)

        # ── Solo el admin puede eliminar pedidos ──
        if self._es_admin():
            btn_eliminar = QPushButton("🗑  Eliminar pedido")
            btn_eliminar.clicked.connect(self._eliminar_pedido)
            acciones.addWidget(btn_eliminar)

        layout.addLayout(acciones)

    def _cargar_pedidos(self):
        estado = self.filtro_estado.currentText()
        mesa_id = self.filtro_mesa.currentData()
        filtro_estado = None if estado == "Todos" else estado
        self.pedidos = obtener_pedidos(
            filtro_estado=filtro_estado,
            filtro_mesa_id=mesa_id
        )
        self.tabla.setRowCount(len(self.pedidos))

        colores_estado = {
            "abierto":        "#89b4fa",
            "en preparación": "#fab387",
            "listo":          "#a6e3a1",
            "cerrado":        "#585b70",
        }

        for row, pedido in enumerate(self.pedidos):
            self.tabla.setItem(row, 0, QTableWidgetItem(str(pedido.id)))
            self.tabla.setItem(row, 1, QTableWidgetItem(str(pedido.mesa_id)))

            estado_item = QTableWidgetItem(pedido.estado.capitalize())
            color = colores_estado.get(pedido.estado, "#cdd6f4")
            estado_item.setForeground(QColor(color))
            self.tabla.setItem(row, 2, estado_item)
            self.tabla.setItem(row, 3, QTableWidgetItem(pedido.fecha))

            btn_campana = QPushButton("🔔")
            btn_campana.setToolTip("Marcar como listo y pasar a facturación")
            btn_campana.setCursor(Qt.CursorShape.PointingHandCursor)

            if pedido.estado in ("listo", "cerrado"):
                btn_campana.setEnabled(False)
                btn_campana.setStyleSheet("""
                    QPushButton { background: transparent; border: none; font-size: 18px; color: #45475a; }
                """)
            else:
                btn_campana.setStyleSheet("""
                    QPushButton { background: transparent; border: none; font-size: 18px; color: #f9e2af; }
                    QPushButton:hover { background-color: #2a2a1e; border-radius: 6px; color: #f9e2af; }
                    QPushButton:pressed { color: #a6e3a1; background-color: #1e3a2f; border-radius: 6px; }
                """)
                pedido_id = pedido.id
                btn_campana.clicked.connect(
                    lambda _, pid=pedido_id, btn=btn_campana, r=row: self._marcar_listo(pid, btn, r)
                )

            self.tabla.setCellWidget(row, 4, btn_campana)
            self.tabla.setRowHeight(row, 42)

        self.lista_items.setRowCount(0)
        self.lbl_total.setText("Total: $0.00")

    def _marcar_listo(self, pedido_id, btn, row):
        btn.setText("✅")
        btn.setEnabled(False)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #1e3a2f; border: none;
                font-size: 18px; color: #a6e3a1; border-radius: 6px;
            }
        """)
        _tocar_campana()
        try:
            actualizar_estado_pedido(pedido_id, "listo")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo marcar como listo:\n{e}")
            return
        QTimer.singleShot(600, self._cargar_pedidos)

    def _mostrar_detalle(self):
        pedido = self._pedido_seleccionado()
        if not pedido:
            return
        items = obtener_items_pedido(pedido.id)
        self.lista_items.setRowCount(len(items))
        total = 0.0
        for row, item in enumerate(items):
            plato = obtener_plato_por_id(item.plato_id)
            nombre = plato.nombre if plato else "Desconocido"
            subtotal = (plato.precio if plato else 0) * item.cantidad
            total += subtotal
            self.lista_items.setItem(row, 0, QTableWidgetItem(nombre))
            self.lista_items.setItem(row, 1, QTableWidgetItem(str(item.cantidad)))
            self.lista_items.setItem(row, 2, QTableWidgetItem(f"${subtotal:.2f}"))
        self.lbl_total.setText(f"Total: ${total:.2f}")

    def _pedido_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            return None
        pedido_id = int(self.tabla.item(fila, 0).text())
        return next((p for p in self.pedidos if p.id == pedido_id), None)

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
        pedido = self._pedido_seleccionado()
        if not pedido:
            QMessageBox.warning(self, "Aviso", "Selecciona un pedido primero.")
            return
        dialog = AgregarPlatoDialog(self)
        if dialog.exec():
            plato_id, cantidad = dialog.obtener_datos()
            try:
                agregar_plato_a_pedido(pedido.id, plato_id, cantidad)
                self._mostrar_detalle()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al agregar plato:\n{e}")

    def _quitar_plato(self):
        pedido = self._pedido_seleccionado()
        if not pedido:
            QMessageBox.warning(self, "Aviso", "Selecciona un pedido primero.")
            return
        fila_item = self.lista_items.currentRow()
        if fila_item < 0:
            QMessageBox.warning(self, "Aviso", "Selecciona un plato del detalle.")
            return
        items = obtener_items_pedido(pedido.id)
        if fila_item >= len(items):
            return
        item_id = items[fila_item].id
        confirmar = QMessageBox.question(
            self, "Confirmar", "¿Quitar este plato del pedido?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            quitar_plato_de_pedido(item_id)
            self._mostrar_detalle()

    def _cambiar_estado(self):
        pedido = self._pedido_seleccionado()
        if not pedido:
            QMessageBox.warning(self, "Aviso", "Selecciona un pedido primero.")
            return
        dialog = CambiarEstadoDialog(self, pedido.estado)
        if dialog.exec():
            nuevo_estado = dialog.obtener_estado()
            try:
                actualizar_estado_pedido(pedido.id, nuevo_estado)
                self._cargar_pedidos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al cambiar estado:\n{e}")

    def _eliminar_pedido(self):
        # Protección extra por si se llama directamente
        if not self._es_admin():
            QMessageBox.warning(self, "Sin permiso", "Solo el administrador puede eliminar pedidos.")
            return
        pedido = self._pedido_seleccionado()
        if not pedido:
            QMessageBox.warning(self, "Aviso", "Selecciona un pedido primero.")
            return
        confirmar = QMessageBox.question(
            self, "Confirmar", f"¿Eliminar el pedido #{pedido.id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            try:
                eliminar_pedido(pedido.id)
                self._cargar_pedidos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar:\n{e}")


class NuevoPedidoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Pedido")
        self.setFixedSize(420, 420)
        self.platos_agregados = []
        self._build_ui()

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
        btn_guardar.setStyleSheet("background-color: #cba6f7; color: #1e1e2e; font-weight: bold;")
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


class AgregarPlatoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar Plato")
        self.setFixedSize(320, 160)
        self._build_ui()

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


class CambiarEstadoDialog(QDialog):
    def __init__(self, parent=None, estado_actual="abierto"):
        super().__init__(parent)
        self.setWindowTitle("Cambiar Estado")
        self.setFixedSize(280, 140)
        self._build_ui(estado_actual)

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