"""Reloj: tick, estacion y temperatura del ecosistema.

El tick empieza en 0 y sube en 1 al inicio de cada CicloTick, asi que el primer tick que
ven los pasos es el 1. Lee el diccionario CALENDARIO de configuracion/ecosistema.py.
"""
from __future__ import annotations

import math


class Reloj:
    def __init__(self, config: dict | None = None) -> None:
        if config is None:
            from simulador.configuracion.ecosistema import CALENDARIO

            config = CALENDARIO
        self._cfg = config
        self.tick = 0
        # ajuste de temperatura que pone el ciclo (sequia); no es parte del calendario
        self.delta_temperatura = 0.0

    @property
    def ticks_por_estacion(self) -> int:
        return self._cfg["ticks_por_estacion"]

    @property
    def estacion(self) -> str:
        estaciones = self._cfg["estaciones"]
        return estaciones[(self.tick // self.ticks_por_estacion) % len(estaciones)]

    @property
    def temperatura(self) -> float:
        base = self._cfg["por_estacion"][self.estacion]["temperatura_base"]
        fase = (self.tick % self._cfg["ticks_por_dia"]) / self._cfg["ticks_por_dia"]
        return base + self._cfg["amplitud_dia"] * math.sin(2 * math.pi * fase) + self.delta_temperatura

    def factoresEstacion(self) -> dict:
        return self._cfg["por_estacion"][self.estacion]

    def avanzar(self) -> int:
        self.tick += 1
        return self.tick

    def aEstado(self) -> dict:
        return {"tick": self.tick}

    def cargarEstado(self, estado: dict) -> None:
        self.tick = int(estado["tick"])
        self.delta_temperatura = 0.0
