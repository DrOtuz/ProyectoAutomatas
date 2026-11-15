"""Registro de errores inesperados en archivo local y mensajes al usuario (RNF-12)."""

from __future__ import annotations

import os
import traceback
from datetime import datetime
from pathlib import Path

VARIABLE_CARPETA_DATOS = "SIMULADOR_CARPETA_DATOS"
NOMBRE_ARCHIVO_LOG = "errores.log"


def obtenerCarpetaDatos() -> Path:
    """Devuelve la carpeta donde viven los datos y registros de la aplicacion."""
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


def obtenerRutaRegistroErrores() -> Path:
    """Devuelve la ruta al archivo local de registro de errores."""
    return obtenerCarpetaDatos() / NOMBRE_ARCHIVO_LOG


def registrarError(error: Exception | str, contexto: str = "") -> Path:
    """Escribe el error con fecha, contexto y traceback en el archivo local de registro."""
    ruta_log = obtenerRutaRegistroErrores()
    ahora = datetime.now().isoformat()
    lineas = [
        f"\n{'=' * 60}\n",
        f"FECHA: {ahora}\n",
    ]
    if contexto:
        lineas.append(f"CONTEXTO: {contexto}\n")
    if isinstance(error, Exception):
        lineas.append(f"TIPO: {type(error).__name__}\n")
        lineas.append(f"MENSAJE: {error}\n")
        lineas.append("DETALLE:\n")
        lineas.append(traceback.format_exc())
    else:
        lineas.append(f"MENSAJE: {error}\n")

    with ruta_log.open("a", encoding="utf-8") as archivo:
        archivo.writelines(lineas)
    return ruta_log


def formatearMensajeUsuario(error: Exception | str, ruta_log: Path | None = None) -> str:
    """Genera mensaje legible confirmando que el ultimo guardado sigue seguro (RNF-12)."""
    ruta = ruta_log or obtenerRutaRegistroErrores()
    detalle = str(error) if error else "Error desconocido"
    return (
        "Se ha producido un error inesperado en la simulacion.\n\n"
        f"Detalle: {detalle}\n\n"
        "Su ultima simulacion guardada permanece segura y sin danos.\n"
        f"El informe tecnico se ha guardado en:\n{ruta}"
    )
