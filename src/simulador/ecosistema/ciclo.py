"""CicloTick: orden fijo de los pasos de un tick.

Orden: 1) el reloj avanza, 2) los eventos (sequia, lluvia, foco natural), 3 en adelante los
pasos registrados con registrarPaso(orden, funcion) en orden creciente. El fuego es el
paso 4. Un paso recibe el ciclo y puede leer ciclo.reloj, ciclo.eventos, ciclo.rng y
ciclo.foco_natural.
"""
from __future__ import annotations


class CicloTick:
    def __init__(self, rng, reloj, eventos) -> None:
        self.rng = rng
        self.reloj = reloj
        self.eventos = eventos
        self.foco_natural = False
        self._pasos: list[tuple[int, int, object]] = []
        self._contador = 0

    def registrarPaso(self, orden: int, funcion) -> None:
        self._pasos.append((orden, self._contador, funcion))
        self._contador += 1
        self._pasos.sort(key=lambda p: (p[0], p[1]))

    def ejecutarTick(self) -> None:
        self.reloj.avanzar()
        self.eventos.paso(self.reloj)
        self.reloj.delta_temperatura = self.eventos.deltaTemperatura()
        self.foco_natural = self.eventos.foco
        for _, _, funcion in list(self._pasos):
            funcion(self)
