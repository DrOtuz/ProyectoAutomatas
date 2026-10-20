"""Seccion de configuracion de Ecosistema.

Los valores los define Ecosistema a partir de la tabla de parametros de la especificacion.
Cada parametro se declara con `campo(valor, minimo=..., maximo=...)`, igual que en app.py.
"""

from __future__ import annotations

from dataclasses import dataclass

from simulador.configuracion.base import validarSeccion


@dataclass(frozen=True)
class ConfiguracionEcosistema:
    def __post_init__(self):
        validarSeccion(self)