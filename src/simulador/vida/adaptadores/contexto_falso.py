"""ContextoFalso: una poblacion minima para probar el automata sin Poblacion.

Implementa `ContextoVida`: guarda las criaturas en un indice por casilla y
registra las reproducciones pedidas (no crea crias).
"""
from __future__ import annotations

from collections import defaultdict

from ..criatura import Criatura
from ..percepcion import casillas_en_radio
from ..puertos import MapaPuerto
from ..tipos import Pos


class ContextoFalso:
    def __init__(self, ancho: int, alto: int, reproduccion_ok: bool = True) -> None:
        self.ancho = ancho
        self.alto = alto
        self.reproduccion_ok = reproduccion_ok
        self.reproducciones: list[tuple[Criatura, Criatura]] = []
        self._indice: dict[Pos, list[Criatura]] = defaultdict(list)
        self.criaturas: list[Criatura] = []

    def agregar(self, criatura: Criatura) -> Criatura:
        self.criaturas.append(criatura)
        self._indice[criatura.pos].append(criatura)
        return criatura

    # --- ContextoVida ---------------------------------------------------------------

    def criaturas_en(self, pos: Pos) -> list[Criatura]:
        return list(self._indice.get(pos, ()))

    def criaturas_en_radio(self, pos: Pos, radio: int) -> list[Criatura]:
        encontradas: list[Criatura] = []
        for casilla in casillas_en_radio(pos, radio, self.ancho, self.alto):
            encontradas.extend(self._indice.get(casilla, ()))
        return encontradas

    def ocupacion(self, pos: Pos) -> int:
        return sum(1 for c in self._indice.get(pos, ()) if c.viva)

    def mover(self, criatura: Criatura, pos: Pos) -> None:
        self._indice[criatura.pos].remove(criatura)
        criatura.mover_a(pos)
        self._indice[criatura.pos].append(criatura)

    def reproducir(self, madre: Criatura, padre: Criatura, mapa: MapaPuerto) -> bool:
        self.reproducciones.append((madre, padre))
        if not self.reproduccion_ok:
            return False
        madre.turno_hecho = True
        padre.turno_hecho = True
        return True
