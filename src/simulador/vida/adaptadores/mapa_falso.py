"""MapaFalso: un mapa pequeno hecho a mano para probar vida/ sin el Subgrupo A.

Cumple `MapaPuerto`. Sirve para pruebas y para la simulacion sin interfaz.
Los valores de comida son los que se le proponen a A: pasto de hasta 30 u que
regenera 1 u por tick y arbol de hasta 60 u que regenera 2 u por tick.

Dibujo en texto (`desde_texto`):
    .  tierra sin comida     ~  agua
    p  pasto                 A  arbol
    *  fuego (sobre tierra)
"""
from __future__ import annotations

from typing import Iterable

from ..percepcion import casillas_en_radio, vecinos
from ..puertos import TIPO_COMIDA, TIPO_FUEGO
from ..tipos import Pos


class MapaFalso:
    PASTO_MAX = 30.0
    PASTO_REGEN = 1.0
    ARBOL_MAX = 60.0
    ARBOL_REGEN = 2.0

    def __init__(self, ancho: int, alto: int) -> None:
        if ancho <= 0 or alto <= 0:
            raise ValueError("ancho y alto deben ser > 0")
        self.ancho = ancho
        self.alto = alto
        self._agua: set[Pos] = set()
        self._fuego: set[Pos] = set()
        self._biomasa: dict[Pos, float] = {}
        self._maximo: dict[Pos, float] = {}
        self._regen: dict[Pos, float] = {}

    # --- MapaPuerto -----------------------------------------------------------

    def en_limites(self, x: int, y: int) -> bool:
        return 0 <= x < self.ancho and 0 <= y < self.alto

    def es_transitable(self, x: int, y: int) -> bool:
        return self.en_limites(x, y) and (x, y) not in self._agua

    def biomasa_en(self, x: int, y: int) -> float:
        return self._biomasa.get((x, y), 0.0)

    def consumir_biomasa(self, x: int, y: int) -> float:
        consumida = self._biomasa.get((x, y), 0.0)
        if consumida:
            self._biomasa[(x, y)] = 0.0
        return consumida

    def hay_fuego(self, x: int, y: int) -> bool:
        return (x, y) in self._fuego

    def buscar_en_radio(self, x: int, y: int, radio: int, tipo: str) -> list[Pos]:
        if tipo == TIPO_COMIDA:
            return [
                p
                for p in casillas_en_radio((x, y), radio, self.ancho, self.alto)
                if self._biomasa.get(p, 0.0) > 0
            ]
        if tipo == TIPO_FUEGO:
            return [
                p
                for p in casillas_en_radio((x, y), radio, self.ancho, self.alto)
                if p in self._fuego
            ]
        raise ValueError(f"tipo de busqueda desconocido: {tipo!r}")

    # --- armar escenarios -------------------------------------------------------

    def _exigir_casilla_valida(self, x: int, y: int) -> None:
        if not self.en_limites(x, y):
            raise ValueError(f"({x}, {y}) esta fuera del mapa")

    def poner_comida(
        self,
        x: int,
        y: int,
        u: float,
        maximo: float | None = None,
        regeneracion: float = 0.0,
    ) -> None:
        """Pone `u` unidades de comida; con `regeneracion` > 0 vuelve a crecer
        cada tick hasta `maximo` (por defecto, el valor puesto)."""
        self._exigir_casilla_valida(x, y)
        if (x, y) in self._agua:
            raise ValueError(f"({x}, {y}) es agua: no puede tener comida")
        if u < 0 or regeneracion < 0:
            raise ValueError("u y regeneracion deben ser >= 0")
        self._biomasa[(x, y)] = float(u)
        self._maximo[(x, y)] = float(u if maximo is None else maximo)
        self._regen[(x, y)] = float(regeneracion)

    def poner_pasto(self, x: int, y: int) -> None:
        self.poner_comida(x, y, self.PASTO_MAX, self.PASTO_MAX, self.PASTO_REGEN)

    def poner_arbol(self, x: int, y: int) -> None:
        self.poner_comida(x, y, self.ARBOL_MAX, self.ARBOL_MAX, self.ARBOL_REGEN)

    def poner_agua(self, x: int, y: int) -> None:
        self._exigir_casilla_valida(x, y)
        self._agua.add((x, y))
        self._fuego.discard((x, y))
        for tabla in (self._biomasa, self._maximo, self._regen):
            tabla.pop((x, y), None)

    def poner_fuego(self, x: int, y: int) -> None:
        self._exigir_casilla_valida(x, y)
        if (x, y) in self._agua:
            raise ValueError(f"({x}, {y}) es agua: no puede arder")
        self._fuego.add((x, y))

    def apagar_fuego(self, x: int, y: int) -> None:
        self._fuego.discard((x, y))

    def casillas_en_fuego(self) -> list[Pos]:
        """Casillas en llamas, ordenadas. Para que la prueba avise a
        Poblacion.eliminar_en, como hara el automata del incendio de A."""
        return sorted(self._fuego)

    # --- evolucion simple del mapa ---------------------------------------------

    def regenerar(self) -> None:
        """Un tick de crecimiento: la comida con regeneracion sube hasta su maximo.
        La comida no crece en casillas en llamas."""
        for pos, regen in self._regen.items():
            if regen > 0 and pos not in self._fuego:
                self._biomasa[pos] = min(
                    self._maximo[pos], self._biomasa.get(pos, 0.0) + regen
                )

    def propagar_fuego(self) -> list[Pos]:
        """Un tick de incendio muy simple, para probar HUIR.

        Las casillas que ardian se apagan y dejan de tener comida; el fuego
        pasa a las 8 vecinas que tengan comida. Devuelve las casillas que
        arden ahora.
        """
        nuevas: set[Pos] = set()
        for pos in self._fuego:
            for v in vecinos(pos):
                if (
                    self.es_transitable(*v)
                    and v not in self._fuego
                    and self._biomasa.get(v, 0.0) > 0
                ):
                    nuevas.add(v)
        for pos in self._fuego:
            self._biomasa[pos] = 0.0
        self._fuego = nuevas
        return sorted(self._fuego)

    # --- dibujo en texto --------------------------------------------------------

    @classmethod
    def desde_texto(cls, lineas: Iterable[str]) -> "MapaFalso":
        """Construye un mapa desde un dibujo (ver el docstring del modulo)."""
        filas = list(lineas)
        if not filas or not filas[0]:
            raise ValueError("el dibujo esta vacio")
        ancho = len(filas[0])
        if any(len(f) != ancho for f in filas):
            raise ValueError("todas las lineas deben tener el mismo largo")
        mapa = cls(ancho, len(filas))
        for y, fila in enumerate(filas):
            for x, caracter in enumerate(fila):
                if caracter == ".":
                    continue
                elif caracter == "~":
                    mapa.poner_agua(x, y)
                elif caracter == "p":
                    mapa.poner_pasto(x, y)
                elif caracter == "A":
                    mapa.poner_arbol(x, y)
                elif caracter == "*":
                    mapa.poner_fuego(x, y)
                else:
                    raise ValueError(f"caracter desconocido {caracter!r} en ({x}, {y})")
        return mapa

    def a_texto(self) -> str:
        """Dibujo del mapa (inverso de `desde_texto`; la comida sin tipo se ve como 'c')."""
        filas = []
        for y in range(self.alto):
            fila = []
            for x in range(self.ancho):
                pos = (x, y)
                if pos in self._fuego:
                    fila.append("*")
                elif pos in self._agua:
                    fila.append("~")
                elif pos in self._maximo:
                    maximo = self._maximo[pos]
                    if maximo == self.ARBOL_MAX:
                        fila.append("A")
                    elif maximo == self.PASTO_MAX:
                        fila.append("p")
                    else:
                        fila.append("c")
                else:
                    fila.append(".")
            filas.append("".join(fila))
        return "\n".join(filas)
