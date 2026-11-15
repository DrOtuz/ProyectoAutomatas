"""Rutas y carpetas de almacenamiento de la aplicacion."""

from __future__ import annotations

import os
from pathlib import Path

VARIABLE_CARPETA_DATOS = "SIMULADOR_CARPETA_DATOS"
NOMBRE_ARCHIVO_BIBLIOTECA = "biblioteca.db"


def obtenerCarpetaDatos() -> Path:
    """Devuelve la carpeta donde viven los datos persistentes del simulador.

    Si la variable de entorno SIMULADOR_CARPETA_DATOS esta fijada y no esta vacia,
    se usa esa ruta. En caso contrario, se usa %LOCALAPPDATA%\\Simulador en Windows.
    Crea la carpeta si no existe antes de devolverla.
    """
    ruta_env = os.environ.get(VARIABLE_CARPETA_DATOS, "").strip()
    if ruta_env:
        carpeta = Path(ruta_env)
    else:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            carpeta = Path(local_app_data) / "Simulador"
        else:
            carpeta = Path.home() / "AppData" / "Local" / "Simulador"

    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def obtenerRutaBiblioteca() -> Path:
    """Devuelve la ruta completa al archivo SQLite de la biblioteca de simulaciones."""
    return obtenerCarpetaDatos() / NOMBRE_ARCHIVO_BIBLIOTECA
