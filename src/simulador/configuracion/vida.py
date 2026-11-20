"""Seccion de configuracion de Vida.

Los valores los define Vida a partir de la tabla de parametros de la especificacion.
Cada parametro se declara con `campo(valor, minimo=..., maximo=...)`, igual que en app.py.
"""

from __future__ import annotations

from dataclasses import dataclass

from simulador.configuracion.base import validarSeccion


@dataclass(frozen=True)
class ConfiguracionVida:
    def __post_init__(self):
        validarSeccion(self)