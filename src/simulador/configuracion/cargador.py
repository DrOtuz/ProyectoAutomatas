"""Carga la configuracion completa desde un archivo TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from simulador.configuracion.app import ConfiguracionApp
from simulador.configuracion.base import ErrorConfiguracion, construirSeccion
from simulador.configuracion.ecosistema import ConfiguracionEcosistema
from simulador.configuracion.vida import ConfiguracionVida

RUTA_POR_DEFECTO = Path(__file__).with_name("por_defecto.toml")


@dataclass(frozen=True)
class Configuracion:
    app: ConfiguracionApp
    ecosistema: ConfiguracionEcosistema
    vida: ConfiguracionVida


def cargarConfiguracion(ruta: Path | None = None) -> Configuracion:
    """Lee y valida la configuracion. Sin ruta, usa `por_defecto.toml`."""
    ruta = ruta or RUTA_POR_DEFECTO
    try:
        with ruta.open("rb") as archivo:
            datos = tomllib.load(archivo)
    except FileNotFoundError as error:
        raise ErrorConfiguracion(f"No se encontro el archivo de configuracion: {ruta}") from error
    except tomllib.TOMLDecodeError as error:
        raise ErrorConfiguracion(f"El archivo de configuracion no es valido: {error}") from error
    desconocidas = sorted(set(datos) - {"app", "ecosistema", "vida"})
    if desconocidas:
        raise ErrorConfiguracion(f"Seccion desconocida: {', '.join(desconocidas)}")
    return Configuracion(
        app=construirSeccion(ConfiguracionApp, datos.get("app", {})),
        ecosistema=construirSeccion(ConfiguracionEcosistema, datos.get("ecosistema", {})),
        vida=construirSeccion(ConfiguracionVida, datos.get("vida", {})),
    )