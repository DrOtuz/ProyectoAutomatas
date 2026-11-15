"""Logica pura del editor de mapa previo a la simulacion (RF-08, RF-09).

Permite dibujar casillas de agua sobre una matriz inicial de tierra usando pincel,
borrador, rectangulo o limpiar, manteniendo una pila acotada de deshacer y rehacer.
"""

from collections import deque
from enum import Enum

import numpy as np

from simulador.configuracion.app import ConfiguracionApp
from simulador.contratos.instantanea import EstadoCasilla


class HerramientaEditor(Enum):
    """Herramientas de dibujo disponibles en el editor."""

    pincel_agua = "pincel_agua"
    borrador = "borrador"
    rectangulo = "rectangulo"


class EditorMapa:
    """Maneja el lienzo de terreno y el historial de edicion sin dependencias de Qt."""

    def __init__(
        self,
        tamano: int = 100,
        configuracion: ConfiguracionApp | None = None,
    ) -> None:
        if tamano <= 0:
            raise ValueError("El tamano del mapa debe ser mayor que cero.")

        self._configuracion = configuracion or ConfiguracionApp()
        self._tamano = tamano
        self._terreno = np.full(
            (tamano, tamano),
            fill_value=int(EstadoCasilla.tierra),
            dtype=np.uint8,
        )
        self._herramienta = HerramientaEditor.pincel_agua
        self._tamano_pincel = self._configuracion.pincel_minimo

        self._historial_deshacer: deque[np.ndarray] = deque(
            maxlen=self._configuracion.pasos_deshacer
        )
        self._historial_rehacer: list[np.ndarray] = []

        self._trazo_activo = False
        self._snapshot_trazo: np.ndarray | None = None
        self._modificado_en_trazo = False

    @property
    def tamano(self) -> int:
        """Dimension horizontal y vertical del mapa cuadrado."""
        return self._tamano

    @property
    def configuracion(self) -> ConfiguracionApp:
        """Configuracion con los limites del editor."""
        return self._configuracion

    @property
    def herramienta(self) -> HerramientaEditor:
        """Herramienta activa de dibujo."""
        return self._herramienta

    def fijarHerramienta(self, herramienta: HerramientaEditor) -> None:
        """Cambia la herramienta activa."""
        if not isinstance(herramienta, HerramientaEditor):
            raise TypeError("La herramienta debe ser una instancia de HerramientaEditor.")
        if self._trazo_activo:
            self.finalizarTrazo()
        self._herramienta = herramienta

    @property
    def tamano_pincel(self) -> int:
        """Tamano del trazo del pincel (ancho y alto en casillas)."""
        return self._tamano_pincel

    def fijarTamanoPincel(self, tamano: int) -> None:
        """Asigna el tamano del pincel dentro de los limites de la configuracion."""
        minimo = self._configuracion.pincel_minimo
        maximo = self._configuracion.pincel_maximo
        if not minimo <= tamano <= maximo:
            raise ValueError(f"El tamano del pincel debe estar entre {minimo} y {maximo}.")
        self._tamano_pincel = tamano

    @property
    def puede_deshacer(self) -> bool:
        """Indica si hay pasos previos para revertir."""
        return len(self._historial_deshacer) > 0

    @property
    def puede_rehacer(self) -> bool:
        """Indica si hay pasos revertidos para reaplicar."""
        return len(self._historial_rehacer) > 0

    @property
    def casillas_agua(self) -> int:
        """Cantidad total de casillas de agua en el mapa."""
        return int(np.count_nonzero(self._terreno == int(EstadoCasilla.agua)))

    @property
    def porcentaje_agua(self) -> float:
        """Porcentaje de casillas de agua respecto al area total."""
        return round((self.casillas_agua / self._terreno.size) * 100.0, 1)

    @property
    def tiene_agua(self) -> bool:
        """Determina si existe al menos una casilla de agua en el mapa."""
        return self.casillas_agua > 0

    def obtenerTerreno(self) -> np.ndarray:
        """Entrega una copia editable del arreglo 2D de terreno actual."""
        return self._terreno.copy()

    def cargarTerreno(self, terreno: np.ndarray) -> None:
        """Carga una matriz externa como nuevo estado base del mapa."""
        if terreno.shape != (self._tamano, self._tamano):
            raise ValueError(f"El terreno debe tener dimensiones ({self._tamano}, {self._tamano}).")
        if self._trazo_activo:
            self.cancelarTrazo()
        self._guardarEnDeshacer()
        self._terreno = np.array(terreno, dtype=np.uint8, copy=True)

    def iniciarTrazo(self) -> None:
        """Comienza una secuencia de pintura continua tratada como una sola accion."""
        if self._trazo_activo:
            self.finalizarTrazo()
        self._snapshot_trazo = self._terreno.copy()
        self._trazo_activo = True
        self._modificado_en_trazo = False

    def agregarPunto(self, x: int, y: int) -> None:
        """Aplica la herramienta en una coordenada dentro del trazo activo."""
        if not self._trazo_activo:
            self.iniciarTrazo()

        if self._aplicarEnCoordenada(x, y):
            self._modificado_en_trazo = True

    def finalizarTrazo(self) -> None:
        """Cierra el trazo activo y lo registra en el historial de deshacer si hubo cambios."""
        if not self._trazo_activo:
            return
        if self._modificado_en_trazo and self._snapshot_trazo is not None:
            self._historial_deshacer.append(self._snapshot_trazo)
            self._historial_rehacer.clear()
        self._trazo_activo = False
        self._snapshot_trazo = None
        self._modificado_en_trazo = False

    def cancelarTrazo(self) -> None:
        """Descarta los cambios realizados durante el trazo en curso."""
        if not self._trazo_activo:
            return
        if self._snapshot_trazo is not None:
            self._terreno = self._snapshot_trazo
        self._trazo_activo = False
        self._snapshot_trazo = None
        self._modificado_en_trazo = False

    def pintarCasilla(self, x: int, y: int) -> None:
        """Pinta puntualmente una coordenada registrando la accion en el historial."""
        if self._trazo_activo:
            self.agregarPunto(x, y)
            return

        self.iniciarTrazo()
        self.agregarPunto(x, y)
        self.finalizarTrazo()

    def pintarRectangulo(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Dibuja un rectangulo relleno delimitado por dos esquinas opuestas."""
        if self._trazo_activo:
            self.finalizarTrazo()

        x_min = max(0, min(x1, x2))
        x_max = min(self._tamano, max(x1, x2) + 1)
        y_min = max(0, min(y1, y2))
        y_max = min(self._tamano, max(y1, y2) + 1)

        if x_min >= x_max or y_min >= y_max:
            return

        valor = (
            int(EstadoCasilla.tierra)
            if self._herramienta == HerramientaEditor.borrador
            else int(EstadoCasilla.agua)
        )

        submatriz = self._terreno[y_min:y_max, x_min:x_max]
        if np.any(submatriz != valor):
            self._guardarEnDeshacer()
            submatriz.fill(valor)

    def limpiar(self) -> None:
        """Devuelve todas las casillas del mapa al estado de tierra."""
        if self._trazo_activo:
            self.cancelarTrazo()

        if np.any(self._terreno != int(EstadoCasilla.tierra)):
            self._guardarEnDeshacer()
            self._terreno.fill(int(EstadoCasilla.tierra))

    def deshacer(self) -> bool:
        """Revierte el ultimo trazo o accion registrada."""
        if self._trazo_activo:
            self.finalizarTrazo()

        if not self._historial_deshacer:
            return False

        anterior = self._historial_deshacer.pop()
        self._historial_rehacer.append(self._terreno.copy())
        self._terreno = anterior
        return True

    def rehacer(self) -> bool:
        """Reaplica la ultima accion deshecha."""
        if self._trazo_activo:
            self.finalizarTrazo()

        if not self._historial_rehacer:
            return False

        siguiente = self._historial_rehacer.pop()
        self._historial_deshacer.append(self._terreno.copy())
        self._terreno = siguiente
        return True

    def _guardarEnDeshacer(self) -> None:
        self._historial_deshacer.append(self._terreno.copy())
        self._historial_rehacer.clear()

    def _aplicarEnCoordenada(self, x: int, y: int) -> bool:
        k = self._tamano_pincel
        inicio_x = x - (k // 2)
        fin_x = inicio_x + k
        inicio_y = y - (k // 2)
        fin_y = inicio_y + k

        x_min = max(0, min(self._tamano, inicio_x))
        x_max = max(0, min(self._tamano, fin_x))
        y_min = max(0, min(self._tamano, inicio_y))
        y_max = max(0, min(self._tamano, fin_y))

        if x_min >= x_max or y_min >= y_max:
            return False

        valor = (
            int(EstadoCasilla.tierra)
            if self._herramienta == HerramientaEditor.borrador
            else int(EstadoCasilla.agua)
        )

        submatriz = self._terreno[y_min:y_max, x_min:x_max]
        if np.any(submatriz != valor):
            submatriz.fill(valor)
            return True
        return False

