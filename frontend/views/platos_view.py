from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QSpinBox, QComboBox,
    QLineEdit, QMessageBox, QHeaderView,
    QDoubleSpinBox, QTextEdit, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from backend.repositories.plato_repo import (
    crear_plato, obtener_platos,
    actualizar_plato, eliminar_plato
)


class PlatosView(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._cargar_platos()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── Encabezado ──
        header = QHBoxLayout()
        titulo = QLabel("Gestión de Platos")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #cba6f7;")
        btn_nuevo = QPushButton("+ Nuevo Plato")
        btn_nuevo.setFixedWidth(140)
        btn_nuevo.setStyleSheet("background-color: #cba6f7; color: #1e1e2e; font-weight: bold; border-radius: 6px; padding: 7px;")
        btn_nuevo.clicked.connect(self._abrir_dialog_crear)
        header.addWidget(titulo)
        header.addStretch()
        header.addWidget(btn_nuevo)
        layout.addLayout(header)

        # ── Buscador ──
        buscar_layout = QHBoxLayout()
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("🔍  Buscar plato por nombre...")
        self.input_buscar.textChanged.connect(self._filtrar_platos)
        buscar_layout.addWidget(self.input_buscar)
        layout.addLayout(buscar_layout)

        # ── Tabla ──
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Descripción", "Precio", "Disponible"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        layout.addWidget(self.tabla)

        # ── Botones de acción ──
        acciones = QHBoxLayout()
        btn_editar = QPushButton("✏  Editar")
        btn_eliminar = QPushButton("🗑  Eliminar")
        btn_toggle = QPushButton("🔄  Cambiar disponibilidad")
        btn_editar.clicked.connect(self._abrir_dialog_editar)
        btn_eliminar.clicked.connect(self._eliminar_plato)
        btn_toggle.clicked.connect(self._toggle_disponibilidad)
        acciones.addStretch()
        acciones.addWidget(btn_toggle)
        acciones.addWidget(btn_editar)
        acciones.addWidget(btn_eliminar)
        layout.addLayout(acciones)

    def _cargar_platos(self):
        self.platos = obtener_platos()
        self._renderizar(self.platos)

    def _renderizar(self, platos):
        self.tabla.setRowCount(len(platos))
        for row, plato in enumerate(platos):
            self.tabla.setItem(row, 0, QTableWidgetItem(str(plato.id)))
            self.tabla.setItem(row, 1, QTableWidgetItem(plato.nombre))
            self.tabla.setItem(row, 2, QTableWidgetItem(plato.descripcion or ""))
            self.tabla.setItem(row, 3, QTableWidgetItem(f"${plato.precio:.2f}"))

            disp_item = QTableWidgetItem("Sí" if plato.disponible else "No")
            disp_item.setForeground(Qt.GlobalColor.white)
            disp_item.setBackground(
                QColor("#a6e3a1") if plato.disponible else QColor("#f38ba8")
            )
            self.tabla.setItem(row, 4, disp_item)

    def _filtrar_platos(self, texto):
        texto = texto.lower()
        filtrados = [p for p in self.platos if texto in p.nombre.lower()]
        self._renderizar(filtrados)

    def _fila_seleccionada(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Aviso", "Selecciona un plato primero.")
            return None
        return {
            "id": int(self.tabla.item(fila, 0).text()),
            "nombre": self.tabla.item(fila, 1).text(),
            "descripcion": self.tabla.item(fila, 2).text(),
            "precio": float(self.tabla.item(fila, 3).text().replace("$", "")),
            "disponible": self.tabla.item(fila, 4).text() == "Sí",
        }

    def _abrir_dialog_crear(self):
        dialog = PlatoDialog(self)
        if dialog.exec():
            datos = dialog.obtener_datos()
            try:
                crear_plato(datos["nombre"], datos["descripcion"],
                            datos["precio"], datos["disponible"])
                self._cargar_platos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear el plato:\n{e}")

    def _abrir_dialog_editar(self):
        plato = self._fila_seleccionada()
        if not plato:
            return
        dialog = PlatoDialog(self, plato)
        if dialog.exec():
            datos = dialog.obtener_datos()
            try:
                actualizar_plato(plato["id"], datos["nombre"], datos["descripcion"],
                                 datos["precio"], datos["disponible"])
                self._cargar_platos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar:\n{e}")

    def _eliminar_plato(self):
        plato = self._fila_seleccionada()
        if not plato:
            return
        confirmar = QMessageBox.question(
            self, "Confirmar",
            f"¿Eliminar el plato '{plato['nombre']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar == QMessageBox.StandardButton.Yes:
            try:
                eliminar_plato(plato["id"])
                self._cargar_platos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar:\n{e}")

    def _toggle_disponibilidad(self):
        plato = self._fila_seleccionada()
        if not plato:
            return
        try:
            actualizar_plato(
                plato["id"], plato["nombre"], plato["descripcion"],
                plato["precio"], not plato["disponible"]
            )
            self._cargar_platos()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cambiar disponibilidad:\n{e}")


class PlatoDialog(QDialog):
    def __init__(self, parent=None, plato=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Plato" if not plato else "Editar Plato")
        self.setFixedSize(360, 280)
        self._build_ui(plato)

    def _build_ui(self, plato):
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ej: Bandeja Paisa")
        if plato:
            self.input_nombre.setText(plato["nombre"])

        self.input_descripcion = QLineEdit()
        self.input_descripcion.setPlaceholderText("Descripción breve...")
        if plato:
            self.input_descripcion.setText(plato["descripcion"])

        self.input_precio = QDoubleSpinBox()
        self.input_precio.setRange(0.0, 999999.0)
        self.input_precio.setDecimals(2)
        self.input_precio.setPrefix("$ ")
        if plato:
            self.input_precio.setValue(plato["precio"])

        self.input_disponible = QCheckBox("Disponible")
        self.input_disponible.setChecked(plato["disponible"] if plato else True)

        layout.addRow("Nombre:", self.input_nombre)
        layout.addRow("Descripción:", self.input_descripcion)
        layout.addRow("Precio:", self.input_precio)
        layout.addRow("", self.input_disponible)

        botones = QHBoxLayout()
        btn_guardar = QPushButton("Guardar")
        btn_cancelar = QPushButton("Cancelar")
        btn_guardar.setStyleSheet("background-color: #cba6f7; color: #1e1e2e; font-weight: bold;")
        btn_guardar.clicked.connect(self._validar)
        btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_guardar)
        layout.addRow(botones)

    def _validar(self):
        if not self.input_nombre.text().strip():
            QMessageBox.warning(self, "Aviso", "El nombre no puede estar vacío.")
            return
        self.accept()

    def obtener_datos(self):
        return {
            "nombre": self.input_nombre.text().strip(),
            "descripcion": self.input_descripcion.text().strip(),
            "precio": self.input_precio.value(),
            "disponible": self.input_disponible.isChecked(),
        }
