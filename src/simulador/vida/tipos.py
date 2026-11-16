"""Tipos basicos compartidos por todo el paquete vida/.

Este modulo no importa nada del resto del paquete (solo, para anotaciones,
Criatura), asi que cualquier otro modulo puede importarlo sin ciclos.
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:  # solo para anotaciones; evita un ciclo de importacion
    from .criatura import Criatura

# Posicion en el mapa: (x, y). x es la columna e y la fila.
Pos = tuple[int, int]

# Lo que una criatura "quiere" segun su energia (con histeresis). Lo usan el
# automata y EXPLORAR para saber que buscar cuando no hay nada a la vista.
INTENCION_ALIMENTO = "alimento"
INTENCION_PAREJA = "pareja"


class Dieta(Enum):
    """Dieta de una especie. Se define al crear la especie y no muta."""

    HERBIVORO = "herbivoro"
    CARNIVORO = "carnivoro"
    OMNIVORO = "omnivoro"

    @property
    def come_plantas(self) -> bool:
        return self in (Dieta.HERBIVORO, Dieta.OMNIVORO)

    @property
    def come_carne(self) -> bool:
        return self in (Dieta.CARNIVORO, Dieta.OMNIVORO)


class Estado(Enum):
    """Estados del automata de estados finitos de una criatura."""

    HUIR = "huir"
    BUSCAR_ALIMENTO = "buscar_alimento"
    BUSCAR_PAREJA = "buscar_pareja"
    EXPLORAR = "explorar"
    MUERTA = "muerta"


class CausaMuerte(Enum):
    """Por que murio una criatura (para depuracion y estadisticas)."""

    HAMBRE = "hambre"
    VEJEZ = "vejez"
    DEPREDACION = "depredacion"
    FUEGO = "fuego"
    ELIMINACION = "eliminacion"  # el usuario elimino la especie


class EstadoEspecie(Enum):
    """Ciclo de vida de una especie."""

    ACTIVA = "activa"
    EXTINTA = "extinta"
    ELIMINADA = "eliminada"


class TipoObjetivo(Enum):
    """Que clase de cosa persigue o evita una criatura."""

    PLANTA = "planta"
    PRESA = "presa"
    PAREJA = "pareja"
    AMENAZA = "amenaza"


class Objetivo(NamedTuple):
    """Un objetivo percibido: algo hacia lo que ir (o de lo que huir).

    Inmutable (es una tupla con nombres: barata de crear, y se crean muchas por tick).
    `criatura` es None cuando el objetivo es una casilla (planta o fuego).
    `ganancia` es el porcentaje de energia que daria comerlo (0 si no aplica).
    `distancia` es la distancia de Chebyshev desde la criatura que percibe.
    """

    tipo: TipoObjetivo
    pos: Pos
    criatura: Criatura | None = None
    ganancia: float = 0.0
    distancia: int = 0
