"""Paquete vida/: criaturas, comportamiento, herencia y poblacion (Subgrupo B)."""
from .automata_criatura import AutomataCriatura, ContextoVida
from .config import ConfigVida
from .criatura import Criatura
from .especie import Especie
from .estadisticas import Estadisticas
from .poblacion import EventoVida, Poblacion
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
    "AutomataCriatura",
    "ContextoVida",
    "CausaMuerte",
    "ConfigVida",
    "Criatura",
    "Dieta",
    "Especie",
    "Estadisticas",
    "EventoVida",
    "Poblacion",
    "Estado",
    "EstadoEspecie",
    "Objetivo",
    "Pos",
    "TipoObjetivo",
]
