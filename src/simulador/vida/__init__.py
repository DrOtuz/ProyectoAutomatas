"""Paquete vida/: criaturas, comportamiento, herencia y poblacion (Subgrupo B)."""
from .automata_criatura import AutomataCriatura, ContextoVida
from .config import ConfigVida
from .criatura import Criatura
from .especie import Especie
from .estadisticas import Estadisticas
from .historial import GestorHistorial, HistorialEspecie
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
    "CausaMuerte",
    "ConfigVida",
    "ContextoVida",
    "Criatura",
    "Dieta",
    "Especie",
    "Estadisticas",
    "Estado",
    "EstadoEspecie",
    "EventoVida",
    "GestorHistorial",
    "HistorialEspecie",
    "Objetivo",
    "Poblacion",
    "Pos",
    "TipoObjetivo",
]
