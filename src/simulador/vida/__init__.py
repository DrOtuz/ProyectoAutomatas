"""Paquete vida/: criaturas, comportamiento, herencia y poblacion (Subgrupo B)."""
from .config import ConfigVida
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
    "Estado",
    "EstadoEspecie",
    "Objetivo",
    "Pos",
    "TipoObjetivo",
]
