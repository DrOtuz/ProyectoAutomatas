"""Paquete vida/: criaturas, comportamiento, herencia y poblacion (Subgrupo B)."""
from .config import ConfigVida
from .estadisticas import Estadisticas
from .tipos import (
    CausaMuerte,
    Dieta,
    Estado,
    EstadoEspecie,
    Objetivo,
    Pos,
    TipoObjetivo,
)

__all__ = [
    "CausaMuerte",
    "ConfigVida",
    "Dieta",
    "Estadisticas",
    "Estado",
    "EstadoEspecie",
    "Objetivo",
    "Pos",
    "TipoObjetivo",
]
