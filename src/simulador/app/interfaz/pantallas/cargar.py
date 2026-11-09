"""Pantalla de seleccion y carga de simulaciones guardadas (P-05, RF-10, RF-12)."""

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from simulador.app.interfaz.dialogos import confirmarEliminarSimulacion
from simulador.contratos.almacenamiento import Almacenamiento, ResumenSimulacion


def _formatearFecha(fecha: datetime) -> str:
    ahora = datetime.now()
    if fecha.date() == ahora.date():
        return f"Hoy, {fecha.strftime('%H:%M')}"
    delta_dias = (ahora.date() - fecha.date()).days
    if delta_dias == 1:
        return f"Ayer, {fecha.strftime('%H:%M')}"
    return fecha.strftime("%d %b, %H:%M")


class CargarSimulacionWidget(QWidget):
    """Permite explorar las simulaciones existentes, abrirlas o eliminarlas."""

    abrirSimulacion = Signal(int)
    solicitarCrear = Signal()
    cancelar = Signal()

    def __init__(
        self,
        almacenamiento: Almacenamiento,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._almacenamiento = almacenamiento
        self._simulaciones: list[ResumenSimulacion] = []
        self._construirInterfaz()

    def _construirInterfaz(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 30, 40, 30)
        layout_principal.setSpacing(20)

        # Encabezado de navegacion
        layout_nav = QHBoxLayout()
        self.btn_volver = QPushButton("< Menú")
        self.btn_volver.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_volver.setStyleSheet(
            "QPushButton { border: none; font-size: 14px; font-weight: bold; color: #555555; }"
            "QPushButton:hover { color: #1E1E1E; }"
        )
        self.btn_volver.clicked.connect(self.cancelar.emit)

        separador_nav = QLabel(" |  Cargar simulación")
        separador_nav.setStyleSheet("font-size: 14px; color: #888888;")

        layout_nav.addWidget(self.btn_volver)
        layout_nav.addWidget(separador_nav)
        layout_nav.addStretch()
        layout_principal.addLayout(layout_nav)

        # Titulo
        titulo = QLabel("Tus simulaciones")
        titulo.setStyleSheet("font-size: 28px; font-weight: bold; color: #1E1E1E;")
        subtitulo = QLabel("Elige una y se abre en pausa, justo donde la dejaste.")
        subtitulo.setStyleSheet("font-size: 14px; color: #666666;")
        layout_principal.addWidget(titulo)
        layout_principal.addWidget(subtitulo)

        # Contenedor apilado: estado con tabla o estado vacio
        self.pila_contenido = QStackedWidget()

        # 1. Vista vacia
        self.vista_vacia = self._construirVistaVacia()
        self.pila_contenido.addWidget(self.vista_vacia)

        # 2. Vista con tabla
        self.vista_tabla = self._construirVistaTabla()
        self.pila_contenido.addWidget(self.vista_tabla)

        layout_principal.addWidget(self.pila_contenido)

        # Barra inferior de acciones
        layout_pie = QHBoxLayout()
        lbl_info = QLabel("Se abre con el estado exacto que guardaste.")
        lbl_info.setStyleSheet("font-size: 13px; color: #777777;")

        self.btn_abrir = QPushButton("Abrir simulación >")
        self.btn_abrir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_abrir.setEnabled(False)
        self.btn_abrir.setStyleSheet(
            "QPushButton {"
            "  background-color: #1B5E20; border: none; border-radius: 8px;"
            "  padding: 10px 22px; font-size: 14px; font-weight: bold; color: white;"
            "}"
            "QPushButton:hover { background-color: #2E7D32; }"
            "QPushButton:disabled { background-color: #CCCCCC; color: #777777; }"
        )
        self.btn_abrir.clicked.connect(self._onAbrirSeleccionada)

        layout_pie.addWidget(lbl_info)
        layout_pie.addStretch()
        layout_pie.addWidget(self.btn_abrir)
        layout_principal.addLayout(layout_pie)

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

        icono = QLabel("📁")
        icono.setStyleSheet("font-size: 48px;")
        icono.setAlignment(Qt.AlignmentFlag.AlignCenter)

        mensaje = QLabel("Aún no tienes simulaciones")
        mensaje.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E1E1E;")
        mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_crear_vacio = QPushButton("Crear simulación")
        self.btn_crear_vacio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_crear_vacio.setStyleSheet(
            "QPushButton {"
            "  background-color: #1B5E20; color: white; font-size: 14px; font-weight: bold;"
            "  padding: 10px 20px; border-radius: 8px; border: none;"
            "}"
            "QPushButton:hover { background-color: #2E7D32; }"
        )
        self.btn_crear_vacio.clicked.connect(self.solicitarCrear.emit)

        layout.addWidget(icono)
        layout.addWidget(mensaje)
        layout.addWidget(self.btn_crear_vacio)
        return contenedor

    def _construirVistaTabla(self) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "Nombre",
            "Tick",
            "Última modificación",
            "Velocidad",
            "",
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla.itemSelectionChanged.connect(self._alCambiarSeleccion)
        self.tabla.cellDoubleClicked.connect(lambda row, col: self._onAbrirSeleccionada())

        layout.addWidget(self.tabla)
        return contenedor

    def actualizarLista(self) -> None:
        """Consulta el almacenamiento y refresca las filas de la tabla."""
        self._simulaciones = self._almacenamiento.listar()
        if not self._simulaciones:
            self.pila_contenido.setCurrentWidget(self.vista_vacia)
            self.btn_abrir.setEnabled(False)
            return

        self.pila_contenido.setCurrentWidget(self.vista_tabla)
        self.tabla.setRowCount(len(self._simulaciones))

        for fila, sim in enumerate(self._simulaciones):
            item_nombre = QTableWidgetItem(sim.nombre)
            item_nombre.setFlags(item_nombre.flags() & ~Qt.ItemFlag.ItemIsEditable)

            item_tick = QTableWidgetItem(f"{sim.tick:,}")
            item_tick.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_tick.setFlags(item_tick.flags() & ~Qt.ItemFlag.ItemIsEditable)

            item_fecha = QTableWidgetItem(_formatearFecha(sim.fecha_guardado))
            item_fecha.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_fecha.setFlags(item_fecha.flags() & ~Qt.ItemFlag.ItemIsEditable)

            item_vel = QTableWidgetItem(f"{sim.velocidad} t/s")
            item_vel.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_vel.setFlags(item_vel.flags() & ~Qt.ItemFlag.ItemIsEditable)

            btn_eliminar = QPushButton("🗑️")
            btn_eliminar.setToolTip("Eliminar simulación")
            btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_eliminar.setStyleSheet(
                "QPushButton { border: none; font-size: 16px; color: #D32F2F; }"
                "QPushButton:hover { background-color: #FFEBEE; border-radius: 4px; }"
            )
            btn_eliminar.clicked.connect(
                lambda _, s=sim: self._confirmarYEliminar(s)
            )

            self.tabla.setItem(fila, 0, item_nombre)
            self.tabla.setItem(fila, 1, item_tick)
            self.tabla.setItem(fila, 2, item_fecha)
            self.tabla.setItem(fila, 3, item_vel)
            self.tabla.setCellWidget(fila, 4, btn_eliminar)

        self._alCambiarSeleccion()

    def _alCambiarSeleccion(self) -> None:
        tiene_seleccion = len(self.tabla.selectedItems()) > 0
        self.btn_abrir.setEnabled(tiene_seleccion)

    def _confirmarYEliminar(self, sim: ResumenSimulacion) -> None:
        if confirmarEliminarSimulacion(self, sim.nombre):
            self._almacenamiento.eliminar(sim.simulacion_id)
            self.actualizarLista()

    def _onAbrirSeleccionada(self) -> None:
        fila = self.tabla.currentRow()
        if 0 <= fila < len(self._simulaciones):
            sim = self._simulaciones[fila]
            self.abrirSimulacion.emit(sim.simulacion_id)

