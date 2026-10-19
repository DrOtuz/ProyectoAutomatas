"""Avisos que el motor devuelve en cada tick.

Son datos inmutables. La aplicacion los traduce a mensajes para el usuario
(cupo alcanzado, especie extinguida, evento terminado).
"""

from dataclasses import dataclass
from enum import Enum

from simulador.contratos.comandos import TipoEvento


class OrigenEvento(Enum):
    """Quien inicio el evento natural."""

    natural = "natural"
    manual = "manual"


@dataclass(frozen=True)
class EventoNaturalIniciado:
    """Un evento natural empezo en el tick indicado."""

    tipo: TipoEvento
    origen: OrigenEvento
    tick: int


@dataclass(frozen=True)
class EventoNaturalTerminado:
    """Un evento natural termino. cancelado es True si el usuario lo cancelo."""

    tipo: TipoEvento
    tick: int
    cancelado: bool = False


@dataclass(frozen=True)
class CupoAlcanzado:
    """La poblacion llego al cupo de criaturas."""

    tick: int
    cupo: int


@dataclass(frozen=True)
class EspecieExtinguida:
    """Una especie se quedo sin criaturas."""

    especie_id: int
    nombre: str
    tick: int