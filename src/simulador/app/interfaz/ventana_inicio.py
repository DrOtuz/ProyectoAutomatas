"""Ventana y orquestador del flujo de inicio (P-02 a P-05, RF-06, RF-07, RF-10)."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QWidget

from simulador.app.interfaz.pantallas.cargar import CargarSimulacionWidget
from simulador.app.interfaz.pantallas.menu_principal import MenuPrincipalWidget
from simulador.app.interfaz.pantallas.nueva_simulacion import NuevaSimulacionWidget
from simulador.configuracion.app import ConfiguracionApp
from simulador.contratos.almacenamiento import Almacenamiento


class VentanaInicio(QMainWindow):
    """Ventana inicial que administra el menu, la creacion y la carga de simulaciones."""

    iniciarEditor = Signal(str, object)
    cargarSimulacion = Signal(int)

    def __init__(
        self,
        almacenamiento: Almacenamiento,
        configuracion: ConfiguracionApp | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Simulador de ecosistemas")
        self.resize(850, 550)

        self._almacenamiento = almacenamiento
        self._configuracion = configuracion or ConfiguracionApp()

        self._pila = QStackedWidget()
        self.setCentralWidget(self._pila)

        self._menu = MenuPrincipalWidget()
        self._nueva = NuevaSimulacionWidget(self._almacenamiento, self._configuracion)
        self._cargar = CargarSimulacionWidget(self._almacenamiento)

        self._pila.addWidget(self._menu)
        self._pila.addWidget(self._nueva)
        self._pila.addWidget(self._cargar)

        self._conectarSenales()
        self.mostrarMenu()

    @property
    def pantalla_actual(self) -> QWidget:
        """Devuelve el widget visible actualmente en la pila."""
        return self._pila.currentWidget()

    def mostrarMenu(self) -> None:
        """Cambia la vista visible al menu principal."""
        self._pila.setCurrentWidget(self._menu)

    def mostrarNuevaSimulacion(self) -> None:
        """Prepara y muestra el formulario de creacion."""
        self._nueva.limpiar()
        self._pila.setCurrentWidget(self._nueva)

    def mostrarCargarSimulacion(self) -> None:
        """Actualiza y muestra la lista de simulaciones guardadas."""
        self._cargar.actualizarLista()
        self._pila.setCurrentWidget(self._cargar)

    def _conectarSenales(self) -> None:
        # Menú
        self._menu.solicitarCrear.connect(self.mostrarNuevaSimulacion)
        self._menu.solicitarCargar.connect(self.mostrarCargarSimulacion)

        # Nueva simulación
        self._nueva.cancelar.connect(self.mostrarMenu)
        self._nueva.continuarEditor.connect(self.iniciarEditor.emit)

        # Cargar simulación
        self._cargar.cancelar.connect(self.mostrarMenu)
        self._cargar.solicitarCrear.connect(self.mostrarNuevaSimulacion)
        self._cargar.abrirSimulacion.connect(self.cargarSimulacion.emit)

