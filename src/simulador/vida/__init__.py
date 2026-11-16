"""Paquete vida/: criaturas, comportamiento, herencia y poblacion (Subgrupo B)."""
from .config import ConfigVida
from .criatura import Criatura
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
    "Criatura",
    "Dieta",
    "Estadisticas",
    "Estado",
    "EstadoEspecie",
    "Objetivo",
    "Pos",
    "TipoObjetivo",
]
