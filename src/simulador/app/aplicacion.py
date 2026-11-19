"""Aplicacion: arma las ventanas, el almacenamiento y el motor real (A + B) y los conecta.

Flujo: ventana de inicio -> (nueva o cargar) -> ventana de simulacion con el Ejecutor, y
desde ella la ventana de especies.

NOTA: lo que no necesita Qt (mapaInicial, crearMotor, abrirMotor) tiene pruebas; las clases
de ventanas no se pudieron ejecutar en el entorno donde se escribieron (sin PySide6) y hay
que probarlas en Windows.
"""

from __future__ import annotations

import numpy as np

from simulador.contratos.almacenamiento import Almacenamiento
from simulador.contratos.errores import ErrorSimulador
from simulador.contratos.instantanea import EstadoCasilla
from simulador.integracion import SimuladorEcosistema


def mapaInicial(semilla: int = 0, lagos: int = 4) -> np.ndarray:
    """Terreno 100 x 100 de partida: pasto con lagos y algunos grupos de arboles.

    Sirve para pruebas y como mapa de partida si no se dibuja uno.
    """
    rng = np.random.default_rng(semilla)
    terreno = np.full((100, 100), int(EstadoCasilla.pasto), dtype=np.uint8)
    yy, xx = np.mgrid[0:100, 0:100]
    for _ in range(lagos):
        cx, cy = rng.integers(10, 90, size=2)
        rx, ry = rng.integers(4, 11, size=2)
        terreno[((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0] = int(EstadoCasilla.agua)
    for _ in range(12):
        cx, cy = rng.integers(5, 95, size=2)
        r = int(rng.integers(2, 6))
        zona = (abs(xx - cx) <= r) & (abs(yy - cy) <= r) & (terreno != int(EstadoCasilla.agua))
        terreno[zona] = int(EstadoCasilla.arbol)
    return terreno


def crearMotor(terreno: np.ndarray | None = None, semilla: int = 0) -> SimuladorEcosistema:
    """Motor nuevo sobre el terreno dado (o el de partida)."""
    return SimuladorEcosistema(mapaInicial(semilla) if terreno is None else terreno, semilla=semilla)


def abrirMotor(almacenamiento: Almacenamiento, simulacion_id: int) -> SimuladorEcosistema:
    """Motor reconstruido desde una simulacion guardada."""
    return SimuladorEcosistema.desdeEstado(almacenamiento.cargar(simulacion_id))


def crearYGuardar(almacenamiento: Almacenamiento, nombre: str, terreno=None, semilla: int = 0, velocidad: int = 10):
    """Crea el motor, guarda la simulacion nueva y devuelve (motor, resumen)."""
    motor = crearMotor(terreno, semilla)
    resumen = almacenamiento.crear(nombre, motor.aEstado(), motor.tick, velocidad)
    return motor, resumen


# ================================================================================
# Ventanas (requieren PySide6)
# ================================================================================


def ejecutar(argv: list[str] | None = None) -> int:  # pragma: no cover - necesita pantalla
    import sys

    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QStackedWidget, QVBoxLayout, QWidget

    from simulador.app.almacenamiento import AlmacenamientoSqlite, obtenerRutaBiblioteca
    from simulador.app.ejecutor.ejecutor import Ejecutor
    from simulador.app.interfaz.editor_mapa_widget import EditorMapaWidget
    from simulador.app.interfaz.especies import (
        CrearEspecieWidget,
        DetalleEspecieWidget,
        ListaEspeciesWidget,
    )
    from simulador.app.interfaz.ventana.ventana_simulacion import VentanaSimulacion
    from simulador.app.interfaz.ventana_inicio import VentanaInicio
    from simulador.configuracion.app import ConfiguracionApp
    from simulador.contratos.comandos import (
        AgregarCriaturas,
        CrearEspecie,
        EliminarCriaturas,
        EliminarEspecie,
        ExtinguirEspecie,
    )

    app = QApplication(argv if argv is not None else sys.argv)
    configuracion = ConfiguracionApp()
    almacenamiento = AlmacenamientoSqlite(obtenerRutaBiblioteca())
    estado: dict = {"inicio": VentanaInicio(almacenamiento, configuracion), "sim": None, "especies": None}

    class VentanaEspecies(QWidget):
        """Lista, creacion y detalle de especies sobre el ejecutor en marcha."""

        def __init__(self, ejecutor: Ejecutor, nombre: str) -> None:
            super().__init__()
            self.setWindowTitle(f"Especies - {nombre}")
            self.resize(900, 640)
            self._ejecutor = ejecutor
            self._detalle_id: int | None = None
            self._ultimo_tick = -1
            self._pila = QStackedWidget()
            self._lista = ListaEspeciesWidget(nombre)
            self._crear = CrearEspecieWidget()
            self._detalle = DetalleEspecieWidget()
            for w in (self._lista, self._crear, self._detalle):
                self._pila.addWidget(w)
            QVBoxLayout(self).addWidget(self._pila)

            self._lista.volverSimulacion.connect(self.hide)
            self._lista.solicitarCrearEspecie.connect(lambda: self._pila.setCurrentWidget(self._crear))
            self._lista.abrirDetalleEspecie.connect(self._abrirDetalle)
            self._crear.volverLista.connect(lambda: self._pila.setCurrentWidget(self._lista))
            self._crear.crearEspecieSolicitado.connect(self._crearEspecie)
            self._detalle.volverLista.connect(self._volverALista)
            self._detalle.agregarCriaturasSolicitado.connect(lambda i, n: ejecutor.enviar(AgregarCriaturas(i, n)))
            self._detalle.eliminarCriaturasSolicitado.connect(lambda i, n: ejecutor.enviar(EliminarCriaturas(i, n)))
            self._detalle.extinguirEspecieSolicitado.connect(lambda i: ejecutor.enviar(ExtinguirEspecie(i)))
            self._detalle.eliminarEspecieSolicitado.connect(self._eliminarEspecie)

            self._reloj = QTimer(self)
            self._reloj.setInterval(250)
            self._reloj.timeout.connect(self.refrescar)
            self._reloj.start()

        def _crearEspecie(self, nombre: str, cantidad: int, dieta: str, genes) -> None:
            self._ejecutor.enviar(CrearEspecie(nombre, cantidad, dieta, genes))
            self._pila.setCurrentWidget(self._lista)

        def _abrirDetalle(self, especie_id: int) -> None:
            info = next((e for e in self._ejecutor.obtenerInstantanea().especies if e.especie_id == especie_id), None)
            if info is None:
                return
            self._detalle = self._nuevoDetalle()
            self._detalle_id = especie_id
            self._detalle.fijarEspecie(info)
            self._pila.setCurrentWidget(self._detalle)

        def _nuevoDetalle(self) -> DetalleEspecieWidget:
            """Un detalle limpio por especie: sus curvas empiezan vacias."""
            viejo = self._detalle
            nuevo = DetalleEspecieWidget()
            nuevo.volverLista.connect(self._volverALista)
            nuevo.agregarCriaturasSolicitado.connect(lambda i, n: self._ejecutor.enviar(AgregarCriaturas(i, n)))
            nuevo.eliminarCriaturasSolicitado.connect(lambda i, n: self._ejecutor.enviar(EliminarCriaturas(i, n)))
            nuevo.extinguirEspecieSolicitado.connect(lambda i: self._ejecutor.enviar(ExtinguirEspecie(i)))
            nuevo.eliminarEspecieSolicitado.connect(self._eliminarEspecie)
            self._pila.removeWidget(viejo)
            viejo.deleteLater()
            self._pila.addWidget(nuevo)
            return nuevo

        def _eliminarEspecie(self, especie_id: int) -> None:
            self._ejecutor.enviar(EliminarEspecie(especie_id))
            self._volverALista()

        def _volverALista(self) -> None:
            self._detalle_id = None
            self._pila.setCurrentWidget(self._lista)

        def refrescar(self) -> None:
            instantanea = self._ejecutor.obtenerInstantanea()
            self._lista.actualizar(instantanea.especies)
            if self._detalle_id is None or instantanea.tick == self._ultimo_tick:
                return
            self._ultimo_tick = instantanea.tick
            info = next((e for e in instantanea.especies if e.especie_id == self._detalle_id), None)
            if info is None:
                self._volverALista()
                return
            self._detalle.fijarEspecie(info)
            if info.energia is not None:
                self._detalle.registrarMuestra(
                    instantanea.tick, info.poblacion, info.velocidad, info.energia, info.vision, info.tamano
                )

    def abrirSimulacion(motor, nombre: str, simulacion_id: int, velocidad: int) -> None:
        ejecutor = Ejecutor(
            motor,
            velocidad=velocidad,
            configuracion=configuracion,
            almacenamiento=almacenamiento,
            simulacion_id=simulacion_id,
        )
        ventana = VentanaSimulacion(ejecutor, nombre, almacenamiento, simulacion_id, configuracion)
        especies = VentanaEspecies(ejecutor, nombre)
        ventana.abrirEspecies.connect(lambda: (especies.show(), especies.raise_()))

        def volver() -> None:
            especies.close()
            ejecutor.detener()
            ventana.close()
            estado["inicio"].mostrarMenu()
            estado["inicio"].show()

        ventana.volverAlMenu.connect(volver)
        estado["sim"], estado["especies"] = ventana, especies
        ejecutor.iniciar()
        estado["inicio"].hide()
        ventana.show()

    def nueva(nombre: str, _datos) -> None:
        """Muestra el editor de mapa; al confirmar el terreno se crea y se abre la simulacion."""
        editor = EditorMapaWidget()
        editor.setWindowTitle(f"Editor de mapas - {nombre}")

        def confirmado(terreno) -> None:
            try:
                motor, resumen = crearYGuardar(
                    almacenamiento, nombre, terreno, semilla=int.from_bytes(nombre.encode()[:4], "big")
                )
            except ErrorSimulador as error:
                print(f"No se pudo crear la simulacion: {error}", file=sys.stderr)
                return
            editor.close()
            abrirSimulacion(motor, resumen.nombre, resumen.simulacion_id, resumen.velocidad)

        editor.mapaConfirmado.connect(confirmado)
        estado["editor"] = editor
        estado["inicio"].hide()
        editor.show()

    def cargar(simulacion_id: int) -> None:
        resumen = next((r for r in almacenamiento.listar() if r.simulacion_id == simulacion_id), None)
        if resumen is None:
            return
        abrirSimulacion(abrirMotor(almacenamiento, simulacion_id), resumen.nombre, simulacion_id, resumen.velocidad)

    estado["inicio"].iniciarEditor.connect(nueva)
    estado["inicio"].cargarSimulacion.connect(cargar)
    estado["inicio"].show()
    codigo = app.exec()
    almacenamiento.cerrar()
    return codigo
