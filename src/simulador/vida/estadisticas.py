"""Estadisticas heredables de una criatura: tamano (S), velocidad (V) y vision (R).

Son inmutables: cada criatura nace con unas estadisticas que no cambian en toda
su vida. La evolucion ocurre entre generaciones, en `cruzar`.

Herencia de cada rasgo x (formula del documento):

    x_hijo = sqrt(x_madre * x_padre) * exp(eps),   eps ~ Normal(0, SIGMA^2)

es decir, el promedio de los logaritmos de los padres mas una mutacion
gaussiana. Siempre da un valor positivo, sin necesidad de limites, y la
mutacion es proporcional al valor del rasgo.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from random import Random
from typing import Any, Mapping

from .config import ConfigVida
from .tipos import Dieta

_RASGOS = ("tamano", "velocidad", "vision")


def _heredar_rasgo(x_madre: float, x_padre: float, sigma: float, rng: Random) -> float:
    """Un rasgo heredado: media geometrica de los padres por exp(mutacion).

    Siempre consume un numero al azar (aunque sigma sea 0) para que la
    secuencia del generador no dependa de la configuracion.
    """
    mutacion = rng.gauss(0.0, sigma)
    return math.sqrt(x_madre * x_padre) * math.exp(mutacion)


@dataclass(frozen=True)
class Estadisticas:
    """S, V y R de una criatura (todos > 0)."""

    tamano: float  # S: masa relativa (1.0 es la referencia)
    velocidad: float  # V: casillas por tick (admite decimales)
    vision: float  # R: radio de vision en casillas (puede ser decimal)

    def __post_init__(self) -> None:
        for nombre in _RASGOS:
            valor = getattr(self, nombre)
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                raise ValueError(f"{nombre} debe ser un numero, no {valor!r}")
            if not math.isfinite(valor) or valor <= 0:
                raise ValueError(f"{nombre} debe ser finito y > 0, no {valor!r}")
            object.__setattr__(self, nombre, float(valor))

    # --- creacion ---------------------------------------------------------------

    @classmethod
    def desde_plantilla(cls, dieta: Dieta, cfg: ConfigVida, rng: Random) -> "Estadisticas":
        """Estadisticas de una criatura inicial de la especie.

        Toma S, V y R de la plantilla de la dieta y multiplica cada rasgo por
        1 + uniforme(-VARIACION_INICIAL, +VARIACION_INICIAL).
        """
        variacion = cfg.VARIACION_INICIAL
        s, v, r = cfg.PLANTILLAS[dieta]
        return cls(
            tamano=s * (1 + rng.uniform(-variacion, variacion)),
            velocidad=v * (1 + rng.uniform(-variacion, variacion)),
            vision=r * (1 + rng.uniform(-variacion, variacion)),
        )

    @classmethod
    def cruzar(
        cls, madre: "Estadisticas", padre: "Estadisticas", cfg: ConfigVida, rng: Random
    ) -> "Estadisticas":
        """Estadisticas de la cria: herencia con mutacion de cada rasgo."""
        return cls(
            tamano=_heredar_rasgo(madre.tamano, padre.tamano, cfg.SIGMA, rng),
            velocidad=_heredar_rasgo(madre.velocidad, padre.velocidad, cfg.SIGMA, rng),
            vision=_heredar_rasgo(madre.vision, padre.vision, cfg.SIGMA, rng),
        )

    # --- derivados --------------------------------------------------------------

    def radio_entero(self) -> int:
        """Radio (en casillas) con el que la criatura mira el mapa: max(1, round(R)).

        El costo metabolico usa R decimal; solo la percepcion redondea.
        """
        return max(1, round(self.vision))

    def masa_u(self, cfg: ConfigVida) -> float:
        """Biomasa del cuerpo en unidades u (lo que da como presa): 100 * S."""
        return cfg.UNIDADES_POR_TAMANO * self.tamano

    # --- guardado y carga ----------------------------------------------------------

    def a_dict(self) -> dict[str, float]:
        return {nombre: getattr(self, nombre) for nombre in _RASGOS}

    @classmethod
    def desde_dict(cls, datos: Mapping[str, Any]) -> "Estadisticas":
        return cls(**{nombre: datos[nombre] for nombre in _RASGOS})
