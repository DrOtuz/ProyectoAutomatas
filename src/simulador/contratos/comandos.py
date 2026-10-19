"""Comandos que la aplicacion envia al motor con Motor.aplicar.

Son datos inmutables y no validan nada: el motor valida al aplicarlos y lanza
ComandoInvalido si algun valor no es correcto. El efecto ocurre al inicio del
tick siguiente, tambien en pausa.
"""

from dataclasses import dataclass
from enum import Enum


class TipoEvento(Enum):
    """Tipos de evento natural que el usuario puede provocar o cancelar."""

    sequia = "sequia"
    lluvia = "lluvia"
    incendio = "incendio"


@dataclass(frozen=True)
class FijarNutrientes:
    """Fija el nivel global de nutrientes del suelo (0 a 100)."""

    nivel: int


@dataclass(frozen=True)
class ProvocarEvento:
    """Provoca un evento natural. El incendio necesita un foco en el mapa."""

    tipo: TipoEvento
    foco_x: int | None = None
    foco_y: int | None = None
    radio: int = 0  # radio del foco del incendio, de 0 a 3


@dataclass(frozen=True)
class CancelarEvento:
    """Cancela el evento activo de ese tipo."""

    tipo: TipoEvento


@dataclass(frozen=True)
class CrearEspecie:
    """Crea una especie con su cantidad inicial de criaturas.

    Si genes es None se usan los genes base. En modo avanzado se indican en el
    orden V, F, W, T de la especificacion.
    """

    nombre: str
    cantidad: int
    genes: tuple[float, float, float, float] | None = None


@dataclass(frozen=True)
class AgregarCriaturas:
    """Agrega criaturas a una especie activa, hasta el cupo."""

    especie_id: int
    cantidad: int


@dataclass(frozen=True)
class EliminarCriaturas:
    """Retira criaturas al azar de una especie."""

    especie_id: int
    cantidad: int


@dataclass(frozen=True)
class ExtinguirEspecie:
    """Retira todas las criaturas de la especie. Sigue en la lista como extinguida."""

    especie_id: int


@dataclass(frozen=True)
class EliminarEspecie:
    """Elimina la especie y su historial. Su nombre queda bloqueado."""

    especie_id: int