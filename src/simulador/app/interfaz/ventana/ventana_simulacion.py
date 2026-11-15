"""Ventana principal de simulacion con mapa, controles, eventos e inspector (P-06, RF-11 a RF-20, RNF-03)."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from simulador.app.ejecutor.ejecutor import Ejecutor
from simulador.app.interfaz.dialogos import confirmarEliminarSimulacion
from simulador.app.interfaz.ventana.barra_estado import BarraEstado
from simulador.app.interfaz.ventana.inspector import InspectorWidget
from simulador.app.interfaz.ventana.panel_eventos import PanelEventos
from simulador.app.interfaz.ventana.visor_mapa import VisorMapa
from simulador.configuracion.app import ConfiguracionApp
from simulador.contratos.almacenamiento import Almacenamiento, validarNombre
from simulador.contratos.comandos import CancelarEvento, FijarNutrientes, ProvocarEvento
from simulador.contratos.errores import ErrorSimulador


class VentanaSimulacion(QMainWindow):
    """Ventana central de la aplicacion conectada al hilo en segundo plano del Ejecutor."""

    volverAlMenu = Signal()
    abrirEspecies = Signal()

    def __init__(
        self,
        ejecutor: Ejecutor,
        nombre: str = "Nueva Simulación",
        almacenamiento: Almacenamiento | None = None,
        simulacion_id: int | None = None,
        configuracion: ConfiguracionApp | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._ejecutor = ejecutor
        self._nombre = nombre
        self._almacenamiento = almacenamiento
        self._simulacion_id = simulacion_id
        self._configuracion = configuracion or ConfiguracionApp()

        self.setWindowTitle(f"Simulador de ecosistemas - {self._nombre}")
        self.resize(1050, 720)

        self._construirInterfaz()
        self._iniciarTemporizadorRefresco()

    def _construirInterfaz(self) -> None:
        contenedor_central = QWidget()
        self.setCentralWidget(contenedor_central)
        layout_principal = QVBoxLayout(contenedor_central)
        layout_principal.setContentsMargins(15, 10, 15, 10)
        layout_principal.setSpacing(10)

        # 1. Barra superior
        layout_superior = self._construirBarraSuperior()
        layout_principal.addLayout(layout_superior)

        # 2. Area central (Lienzo mapa + Panel de control lateral)
        layout_medio = QHBoxLayout()
        layout_medio.setSpacing(15)

        # Visor con Inspector flotante
        self.visor = VisorMapa(self._configuracion)
        self.visor.casillaSeleccionada.connect(self._alSeleccionarCasilla)

        self.inspector = InspectorWidget(self.visor)
        self.inspector.hide()
        self.inspector.cerrarSolicitado.connect(self.inspector.hide)

        layout_medio.addWidget(self.visor, 3)

        # Panel lateral derecho
        panel_lateral = self._construirPanelLateral()
        layout_medio.addWidget(panel_lateral, 1)

        layout_principal.addLayout(layout_medio, 1)

        # 3. Barra inferior de estado (RF-17)
        self.barra_estado = BarraEstado()
        layout_principal.addWidget(self.barra_estado)

    def _construirBarraSuperior(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        self.btn_menu = QPushButton("< Menú")
        self.btn_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_menu.setStyleSheet(
            "QPushButton { border: none; font-size: 14px; font-weight: bold; color: #555555; }"
            "QPushButton:hover { color: #1E1E1E; }"
        )
        self.btn_menu.clicked.connect(self.volverAlMenu.emit)

        self.lbl_nombre = QLabel(self._nombre)
        self.lbl_nombre.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E1E1E;")

        self.btn_renombrar = QPushButton("✏️")
        self.btn_renombrar.setToolTip("Renombrar simulación")
        self.btn_renombrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_renombrar.setStyleSheet("QPushButton { border: none; font-size: 14px; }")
        self.btn_renombrar.clicked.connect(self._onRenombrar)

        self.btn_especies = QPushButton("👥 Especies")
        self.btn_especies.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_especies.setStyleSheet(
            "QPushButton {"
            "  background-color: white; border: 1px solid #D0C9BE; border-radius: 6px;"
            "  padding: 6px 14px; font-size: 13px; font-weight: 500; color: #1E1E1E;"
            "}"
            "QPushButton:hover { background-color: #F5F3EF; }"
        )
        self.btn_especies.clicked.connect(self.abrirEspecies.emit)

        self.btn_guardar = QPushButton("💾 Guardar")
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setStyleSheet(
            "QPushButton {"
            "  background-color: white; border: 1px solid #D0C9BE; border-radius: 6px;"
            "  padding: 6px 14px; font-size: 13px; font-weight: 500; color: #1E1E1E;"
            "}"
            "QPushButton:hover { background-color: #F5F3EF; }"
        )
        self.btn_guardar.clicked.connect(self._onGuardar)

        self.btn_eliminar = QPushButton("🗑️")
        self.btn_eliminar.setToolTip("Eliminar simulación")
        self.btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_eliminar.setStyleSheet("QPushButton { border: none; font-size: 16px; color: #D32F2F; }")
        self.btn_eliminar.clicked.connect(self._onEliminar)

        layout.addWidget(self.btn_menu)
        layout.addSpacing(10)
        layout.addWidget(self.lbl_nombre)
        layout.addWidget(self.btn_renombrar)
        layout.addStretch()
        layout.addWidget(self.btn_especies)
        layout.addWidget(self.btn_guardar)
        layout.addWidget(self.btn_eliminar)
        return layout

    def _construirPanelLateral(self) -> QWidget:
        panel = QFrame()
        panel.setStyleSheet(
            "QFrame {"
            "  background-color: #FBF9F5; border: 1px solid #E5E0D8; border-radius: 10px;"
            "  padding: 10px;"
            "}"
        )
        layout = QVBoxLayout(panel)
        layout.setSpacing(14)

        # Boton de Pausa / Reanudar (RF-14)
        self.btn_pausa = QPushButton("▶️ Reanudar" if self._ejecutor.en_pausa else "⏸️ Pausar")
        self.btn_pausa.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pausa.setStyleSheet(
            "QPushButton {"
            "  background-color: #1B5E20; color: white; border-radius: 8px;"
            "  padding: 10px; font-size: 14px; font-weight: bold; border: none;"
            "}"
            "QPushButton:hover { background-color: #2E7D32; }"
        )
        self.btn_pausa.clicked.connect(self._alternarPausa)
        layout.addWidget(self.btn_pausa)

        # Deslizador de Velocidad (RF-15)
        layout_vel = QVBoxLayout()
        self.lbl_vel = QLabel(f"Velocidad: {self._ejecutor.velocidad} t/s")
        self.lbl_vel.setStyleSheet("font-size: 13px; font-weight: 500; color: #333333;")

        self.slider_vel = QSlider(Qt.Orientation.Horizontal)
        self.slider_vel.setRange(
            self._configuracion.velocidad_minima, self._configuracion.velocidad_maxima
        )
        self.slider_vel.setValue(self._ejecutor.velocidad)
        self.slider_vel.valueChanged.connect(self._alCambiarVelocidad)

        layout_vel.addWidget(self.lbl_vel)
        layout_vel.addWidget(self.slider_vel)
        layout.addLayout(layout_vel)

        # Deslizador de Nutrientes (RF-16)
        layout_nut = QVBoxLayout()
        nut_inicial = self._ejecutor.obtenerInstantanea().nutrientes
        self.lbl_nut = QLabel(f"Nutrientes: {nut_inicial}")
        self.lbl_nut.setStyleSheet("font-size: 13px; font-weight: 500; color: #333333;")

        self.slider_nut = QSlider(Qt.Orientation.Horizontal)
        self.slider_nut.setRange(0, 100)
        self.slider_nut.setValue(nut_inicial)
        self.slider_nut.valueChanged.connect(self._alCambiarNutrientes)

        layout_nut.addWidget(self.lbl_nut)
        layout_nut.addWidget(self.slider_nut)
        layout.addLayout(layout_nut)

        # Panel de eventos (RF-18, RF-28, RF-51)
        self.panel_eventos = PanelEventos()
        self.panel_eventos.provocarEvento.connect(
            lambda tipo: self._ejecutor.enviar(ProvocarEvento(tipo))
        )
        self.panel_eventos.cancelarEvento.connect(
            lambda tipo: self._ejecutor.enviar(CancelarEvento(tipo))
        )
        layout.addWidget(self.panel_eventos)

        layout.addStretch()
        return panel

    def _iniciarTemporizadorRefresco(self) -> None:
        """Inicia el refresco a ~30 FPS cumpliendo RNF-03."""
        self._temporizador = QTimer(self)
        self._temporizador.setInterval(33)  # ~30 FPS
        self._temporizador.timeout.connect(self.actualizar)
        self._temporizador.start()

    def actualizar(self) -> None:
        """Lee la instantanea del ejecutor y refresca la interfaz sin bloquear."""
        instantanea = self._ejecutor.obtenerInstantanea()
        self.visor.actualizarInstantanea(instantanea)
        self.barra_estado.actualizar(instantanea)
        self.panel_eventos.actualizarEventos(instantanea.eventos)

        # Sincronizar estado del botón de pausa
        en_pausa = self._ejecutor.en_pausa
        self.btn_pausa.setText("▶️ Reanudar" if en_pausa else "⏸️ Pausar")

    def _alternarPausa(self) -> None:
        if self._ejecutor.en_pausa:
            self._ejecutor.reanudar()
            self.btn_pausa.setText("⏸️ Pausar")
        else:
            self._ejecutor.pausar()
            self.btn_pausa.setText("▶️ Reanudar")

    def _alCambiarVelocidad(self, valor: int) -> None:
        self._ejecutor.fijarVelocidad(valor)
        self.lbl_vel.setText(f"Velocidad: {valor} t/s")

    def _alCambiarNutrientes(self, valor: int) -> None:
        self._ejecutor.enviar(FijarNutrientes(valor))
        self.lbl_nut.setText(f"Nutrientes: {valor}")

    def _alSeleccionarCasilla(self, x: int, y: int) -> None:
        instantanea = self._ejecutor.obtenerInstantanea()
        criaturas = instantanea.criaturas
        # Buscar criatura en esa coordenada
        encontrada = None
        for i in range(criaturas.shape[0]):
            if int(criaturas[i, 0]) == x and int(criaturas[i, 1]) == y:
                encontrada = criaturas[i]
                break

        if encontrada is not None:
            especie_id = int(encontrada[2])
            nombre_esp = "Especie"
            for esp in instantanea.especies:
                if esp.especie_id == especie_id:
                    nombre_esp = esp.nombre
                    break
            self.inspector.mostrarCriatura(especie_nombre=nombre_esp, edad=instantanea.tick)
        else:
            # Mostrar datos de casilla
            tipo_codigo = int(instantanea.terreno[y, x])
            self.inspector.mostrarCasilla(x, y, tipo=f"Tipo {tipo_codigo}")

    def _onGuardar(self) -> None:
        if hasattr(self._ejecutor, "solicitarGuardado"):
            self._ejecutor.solicitarGuardado()

    def _onRenombrar(self) -> None:
        nuevo_nombre, ok = QInputDialog.getText(
            self,
            "Renombrar simulación",
            "Nuevo nombre:",
            text=self._nombre,
        )
        if not ok or not nuevo_nombre:
            return

        try:
            validarNombre(nuevo_nombre, self._configuracion.largo_maximo_nombre)
            if self._almacenamiento and self._simulacion_id is not None:
                self._almacenamiento.renombrar(self._simulacion_id, nuevo_nombre)
            self._nombre = nuevo_nombre
            self.lbl_nombre.setText(nuevo_nombre)
            self.setWindowTitle(f"Simulador de ecosistemas - {nuevo_nombre}")
        except ErrorSimulador:
            pass

    def _onEliminar(self) -> None:
        if confirmarEliminarSimulacion(self, self._nombre):
            if self._almacenamiento and self._simulacion_id is not None:
                self._almacenamiento.eliminar(self._simulacion_id)
            self._ejecutor.detener()
            self.volverAlMenu.emit()
