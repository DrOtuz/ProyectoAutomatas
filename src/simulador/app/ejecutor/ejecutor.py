"""Ejecutor: corre el motor en un hilo aparte para que la ventana no se congele."""

from __future__ import annotations

import queue
import threading
import time

from simulador.configuracion.app import ConfiguracionApp
from simulador.contratos.almacenamiento import Almacenamiento
from simulador.contratos.errores import ErrorSimulador
from simulador.contratos.instantanea import Instantanea
from simulador.contratos.motor import Aviso, Comando, Motor


class Ejecutor:
    """Hilo que avanza el motor, recibe comandos y entrega instantaneas.

    Solo el hilo interno llama al motor. La ventana usa unicamente los metodos
    de esta clase, que nunca esperan al motor.
    """

    def __init__(
        self,
        motor: Motor,
        velocidad: int | None = None,
        configuracion: ConfiguracionApp | None = None,
        almacenamiento: Almacenamiento | None = None,
        simulacion_id: int | None = None,
    ) -> None:
        self._configuracion = configuracion or ConfiguracionApp()
        if velocidad is None:
            velocidad = self._configuracion.velocidad_inicial
        self._validarVelocidad(velocidad)
        self._motor = motor
        self._velocidad = velocidad
        self._almacenamiento = almacenamiento
        self._simulacion_id = simulacion_id
        self._cerrojo = threading.Lock()
        self._instantanea: Instantanea = motor.obtenerInstantanea()
        self._ultimo_tick_guardado: int = self._instantanea.tick
        self._solicitar_guardado = False
        self._avisos: list[Aviso] = []
        self._errores: list[ErrorSimulador] = []
        self._fallo: Exception | None = None
        self._comandos: queue.Queue[Comando] = queue.Queue()
        self._pausa = threading.Event()
        self._pausa.set()  # arranca en pausa
        self._detener = threading.Event()
        self._hilo: threading.Thread | None = None

    @property
    def activo(self) -> bool:
        return self._hilo is not None and self._hilo.is_alive()

    @property
    def en_pausa(self) -> bool:
        return self._pausa.is_set()

    @property
    def fallo(self) -> Exception | None:
        """Excepcion inesperada del motor, si el hilo tuvo que detenerse."""
        return self._fallo

    @property
    def velocidad(self) -> int:
        return self._velocidad

    @property
    def simulacion_id(self) -> int | None:
        with self._cerrojo:
            return self._simulacion_id

    @property
    def ultimo_tick_guardado(self) -> int:
        with self._cerrojo:
            return self._ultimo_tick_guardado

    def fijarDestinoGuardado(
        self, almacenamiento: Almacenamiento | None, simulacion_id: int | None
    ) -> None:
        """Asigna o actualiza el almacenamiento y el identificador de la simulacion."""
        with self._cerrojo:
            self._almacenamiento = almacenamiento
            self._simulacion_id = simulacion_id

    def solicitarGuardado(self) -> None:
        """Pide al hilo del motor que realice un guardado."""
        self._solicitar_guardado = True

    def detener(self) -> None:
        self._detener.set()
        if self._hilo is not None:
            self._hilo.join(timeout=5.0)

    def enviar(self, comando: Comando) -> None:
        """Encola un comando; el hilo del motor lo aplica, tambien en pausa."""
        self._comandos.put(comando)

    def fijarVelocidad(self, velocidad: int) -> None:
        self._validarVelocidad(velocidad)
        self._velocidad = velocidad

    def iniciar(self) -> None:
        if self._hilo is not None:
            return
        self._hilo = threading.Thread(target=self._bucle, name="ejecutor", daemon=True)
        self._hilo.start()

    def obtenerInstantanea(self) -> Instantanea:
        with self._cerrojo:
            return self._instantanea

    def pausar(self) -> None:
        self._pausa.set()
        self._solicitar_guardado = True

    def reanudar(self) -> None:
        self._pausa.clear()

    def tomarAvisos(self) -> list[Aviso]:
        with self._cerrojo:
            avisos, self._avisos = self._avisos, []
        return avisos

    def tomarErrores(self) -> list[ErrorSimulador]:
        with self._cerrojo:
            errores, self._errores = self._errores, []
        return errores

    def _validarVelocidad(self, velocidad: int) -> None:
        minima = self._configuracion.velocidad_minima
        maxima = self._configuracion.velocidad_maxima
        if not minima <= velocidad <= maxima:
            raise ValueError(f"La velocidad debe estar entre {minima} y {maxima}")

    def _aplicarPendientes(self) -> None:
        while True:
            try:
                comando = self._comandos.get_nowait()
            except queue.Empty:
                return
            try:
                self._motor.aplicar(comando)
            except ErrorSimulador as error:
                with self._cerrojo:
                    self._errores.append(error)

    def _guardar(self) -> None:
        with self._cerrojo:
            almacenamiento = self._almacenamiento
            simulacion_id = self._simulacion_id
            velocidad = self._velocidad
            tick = self._instantanea.tick

        if almacenamiento is None or simulacion_id is None:
            return

        try:
            estado = self._motor.aEstado()
            almacenamiento.guardar(
                simulacion_id=simulacion_id,
                estado=estado,
                tick=tick,
                velocidad=velocidad,
            )
            with self._cerrojo:
                self._ultimo_tick_guardado = tick
        except ErrorSimulador as error:
            with self._cerrojo:
                self._errores.append(error)

    def _bucle(self) -> None:
        siguiente = time.monotonic()
        try:
            while not self._detener.is_set():
                self._aplicarPendientes()
                if self._solicitar_guardado:
                    self._solicitar_guardado = False
                    self._guardar()
                if self._pausa.is_set():
                    self._detener.wait(0.01)
                    siguiente = time.monotonic()
                    continue
                avisos = self._motor.avanzar()
                instantanea = self._motor.obtenerInstantanea()
                with self._cerrojo:
                    self._instantanea = instantanea
                    self._avisos.extend(avisos)

                if (
                    self._instantanea.tick - self._ultimo_tick_guardado
                    >= self._configuracion.autoguardado_cada_ticks
                ):
                    self._guardar()

                siguiente += 1.0 / self._velocidad
                espera = siguiente - time.monotonic()
                if espera > 0:
                    self._detener.wait(espera)
                else:
                    siguiente = time.monotonic()  # no acumular atraso

            self._guardar()
        except Exception as error:  # noqa: BLE001 - el hilo guarda cualquier fallo del motor
            self._fallo = error