"""Almacenamiento de simulaciones de la aplicacion."""

from simulador.app.almacenamiento.memoria import AlmacenamientoMemoria
from simulador.app.almacenamiento.rutas import (
    NOMBRE_ARCHIVO_BIBLIOTECA,
    VARIABLE_CARPETA_DATOS,
    obtenerCarpetaDatos,
    obtenerRutaBiblioteca,
)
from simulador.app.almacenamiento.sqlite import AlmacenamientoSqlite

__all__ = [
    "NOMBRE_ARCHIVO_BIBLIOTECA",
    "VARIABLE_CARPETA_DATOS",
    "AlmacenamientoMemoria",
    "AlmacenamientoSqlite",
    "obtenerCarpetaDatos",
    "obtenerRutaBiblioteca",
]
