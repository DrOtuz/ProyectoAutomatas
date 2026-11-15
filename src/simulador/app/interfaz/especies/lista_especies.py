"""Pantalla con la lista de especies en el mundo (P-07, RF-37, RF-52)."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from simulador.contratos.instantanea import InfoEspecie

LIMITE_ESPECIES_ACTIVAS = 12


class ListaEspeciesWidget(QWidget):
    """Lista las especies vivas y extintas del ecosistema y permite navegar a su detalle o crear."""

    volverSimulacion = Signal()
    solicitarCrearEspecie = Signal()
    abrirDetalleEspecie = Signal(int)

    def __init__(self, nombre_simulacion: str = "Simulación", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._nombre_simulacion = nombre_simulacion
        self._especies: list[InfoEspecie] = []
        self._construirInterfaz()

    def _construirInterfaz(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 30, 40, 30)
        layout_principal.setSpacing(20)

        # Encabezado
        layout_nav = QHBoxLayout()
        self.btn_volver = QPushButton("< Simulación")
        self.btn_volver.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_volver.setStyleSheet(
            "QPushButton { border: none; font-size: 14px; font-weight: bold; color: #555555; }"
            "QPushButton:hover { color: #1E1E1E; }"
        )
        self.btn_volver.clicked.connect(self.volverSimulacion.emit)

        self.lbl_nav_titulo = QLabel(f" |  Especies  |  {self._nombre_simulacion}")
        self.lbl_nav_titulo.setStyleSheet("font-size: 14px; color: #888888;")

        layout_nav.addWidget(self.btn_volver)
        layout_nav.addWidget(self.lbl_nav_titulo)
        layout_nav.addStretch()
        layout_principal.addLayout(layout_nav)

        # Título y botón superior de Crear Especie
        layout_titulos = QHBoxLayout()
        col_titulos = QVBoxLayout()
        col_titulos.setSpacing(4)

        titulo = QLabel("Quién vive en tu mundo")
        titulo.setStyleSheet("font-size: 28px; font-weight: bold; color: #1E1E1E;")

        self.lbl_conteo_especies = QLabel("0 de 12 especies activas")
        self.lbl_conteo_especies.setStyleSheet("font-size: 14px; color: #666666;")

        col_titulos.addWidget(titulo)
        col_titulos.addWidget(self.lbl_conteo_especies)
        layout_titulos.addLayout(col_titulos)
        layout_titulos.addStretch()

        self.btn_crear = QPushButton("+  Crear especie")
        self.btn_crear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_crear.setStyleSheet(
            "QPushButton {"
            "  background-color: #1B5E20; color: white; font-size: 14px; font-weight: bold;"
            "  padding: 10px 20px; border-radius: 8px; border: none;"
            "}"
            "QPushButton:hover { background-color: #2E7D32; }"
        )
        self.btn_crear.clicked.connect(self._alIntentarCrearEspecie)
        layout_titulos.addWidget(self.btn_crear)

        layout_principal.addLayout(layout_titulos)

        # Contenedor apilado: estado vacío o tabla de especies
        self.pila = QStackedWidget()
        self.vista_vacia = self._construirVistaVacia()
        self.vista_tabla = self._construirVistaTabla()
        self.pila.addWidget(self.vista_vacia)
        self.pila.addWidget(self.vista_tabla)
        layout_principal.addWidget(self.pila)

    def _construirVistaVacia(self) -> QWidget:
        contenedor = QFrame()
        contenedor.setStyleSheet(
            "QFrame {"
            "  background-color: #FBF9F5; border: 1px dashed #D0C9BE; border-radius: 12px;"
            "}"
        )
        layout = QVBoxLayout(contenedor)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        icono = QLabel("👥")
        icono.setStyleSheet("font-size: 48px;")
        icono.setAlignment(Qt.AlignmentFlag.AlignCenter)

        mensaje = QLabel("Tu mundo aún está vacío")
        mensaje.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E1E1E;")
        mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_crear_primera = QPushButton("Crear la primera especie")
        self.btn_crear_primera.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_crear_primera.setStyleSheet(
            "QPushButton {"
            "  background-color: #1B5E20; color: white; font-size: 14px; font-weight: bold;"
            "  padding: 10px 20px; border-radius: 8px; border: none;"
            "}"
            "QPushButton:hover { background-color: #2E7D32; }"
        )
        self.btn_crear_primera.clicked.connect(self._alIntentarCrearEspecie)

        layout.addWidget(icono)
        layout.addWidget(mensaje)
        layout.addWidget(self.btn_crear_primera)
        return contenedor

    def _construirVistaTabla(self) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Especie", "Estado", "Población", ""])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla.cellClicked.connect(lambda row, col: self._onFilaClic(row))

        layout.addWidget(self.tabla)
        return contenedor

    def actualizar(self, especies: tuple[InfoEspecie, ...] | list[InfoEspecie]) -> None:
        """Refresca la tabla a partir de la lista de especies."""
        self._especies = list(especies)
        activas = sum(1 for e in self._especies if not e.extinguida)
        self.lbl_conteo_especies.setText(f"{activas} de {LIMITE_ESPECIES_ACTIVAS} especies activas")

        if not self._especies:
            self.pila.setCurrentWidget(self.vista_vacia)
            return

        self.pila.setCurrentWidget(self.vista_tabla)
        self.tabla.setRowCount(len(self._especies))

        for fila, esp in enumerate(self._especies):
            item_esp = QTableWidgetItem(f"●  {esp.nombre}")
            item_esp.setFlags(item_esp.flags() & ~Qt.ItemFlag.ItemIsEditable)

            estado_txt = "○ Extinta" if esp.extinguida else "● Viva"
            item_estado = QTableWidgetItem(estado_txt)
            item_estado.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_estado.setFlags(item_estado.flags() & ~Qt.ItemFlag.ItemIsEditable)

            item_pob = QTableWidgetItem(f"{esp.poblacion:,}")
            item_pob.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_pob.setFlags(item_pob.flags() & ~Qt.ItemFlag.ItemIsEditable)

            btn_flecha = QPushButton("›")
            btn_flecha.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_flecha.setStyleSheet("QPushButton { border: none; font-size: 20px; color: #888888; }")
            btn_flecha.clicked.connect(lambda _, e_id=esp.especie_id: self.abrirDetalleEspecie.emit(e_id))

            self.tabla.setItem(fila, 0, item_esp)
            self.tabla.setItem(fila, 1, item_estado)
            self.tabla.setItem(fila, 2, item_pob)
            self.tabla.setCellWidget(fila, 3, btn_flecha)

    def _alIntentarCrearEspecie(self) -> None:
        activas = sum(1 for e in self._especies if not e.extinguida)
        if activas >= LIMITE_ESPECIES_ACTIVAS:
            QMessageBox.information(
                self,
                "Límite de especies",
                "Ya hay 12 especies activas. Extingue o elimina una para continuar.",
            )
            return
        self.solicitarCrearEspecie.emit()

    def _onFilaClic(self, fila: int) -> None:
        if 0 <= fila < len(self._especies):
            self.abrirDetalleEspecie.emit(self._especies[fila].especie_id)
