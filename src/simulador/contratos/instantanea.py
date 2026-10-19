"""Instantanea: lo que la interfaz puede leer del estado del motor en un tick.

Es de solo lectura: los arreglos de NumPy se marcan como no escribibles. El motor
debe entregar copias, porque marcar un arreglo lo bloquea para todos.
"""

from dataclasses import dataclass
from enum import Enum, IntEnum

import numpy as np

from simulador.contratos.comandos import TipoEvento


class Estacion(Enum):
    """Estaciones del calendario."""

    primavera = "primavera"
    verano = "verano"
    otono = "otono"
    invierno = "invierno"


class EstadoCasilla(IntEnum):
    """Codigos del arreglo terreno (propuesta; los confirma Ecosistema)."""

    tierra = 0
    agua = 1
    pasto = 2
    arbol = 3
    llamas = 4
    quemada = 5


@dataclass(frozen=True)
class InfoEspecie:
    """Resumen de una especie para la lista de especies."""

    especie_id: int
    nombre: str
    color: int  # indice en la paleta de 12 colores
    poblacion: int
    extinguida: bool


@dataclass(frozen=True)
class InfoEvento:
    """Evento activo. El incendio informa casillas en llamas; los demas, ticks."""

    tipo: TipoEvento
    ticks_restantes: int | None = None
    casillas_en_llamas: int | None = None


@dataclass(frozen=True, eq=False)
class Instantanea:
    """Estado visible del motor en un tick.

    terreno: arreglo de 100 x 100, uint8, con codigos de EstadoCasilla.
    criaturas: arreglo de n x 3, int32, con las columnas x, y, especie_id.
    """

    tick: int
    estacion: Estacion
    temperatura: float
    nutrientes: int
    terreno: np.ndarray
    criaturas: np.ndarray
    especies: tuple[InfoEspecie, ...]
    eventos: tuple[InfoEvento, ...]
    cupo: int

    def __post_init__(self):
        self.terreno.flags.writeable = False
        self.criaturas.flags.writeable = False

    @property
    def total_criaturas(self) -> int:
        return len(self.criaturas)