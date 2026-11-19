"""MapaVida: adaptador que deja a Vida leer el Mapa de Ecosistema (cumple MapaPuerto).

Es el unico lugar donde se traducen los nombres de A a los de B. Si A cambia su mapa, solo
cambia este archivo.
"""
from __future__ import annotations

import numpy as np

from simulador.ecosistema.mapa import AGUA, ARBOL, LLAMAS, PASTO, Mapa
from simulador.vida.puertos import TIPO_COMIDA, TIPO_FUEGO
from simulador.vida.tipos import Pos


class MapaVida:
    def __init__(self, mapa: Mapa, fuego=None) -> None:
        self._mapa = mapa
        # con el automata del fuego se evita recorrer el radio cuando no hay incendio
        self._fuego = fuego
        # copia numpy del alimento para la percepcion rapida; se rehace con sincronizar()
        # al empezar la fase de Vida de cada tick y consumir_biomasa la mantiene al dia
        self._alimento: np.ndarray | None = None

    def sincronizar(self) -> None:
        """Vuelve a leer el alimento del mapa (llamar tras la fase de Ecosistema)."""
        self._alimento = np.array(
            [[c.alimento if c.tipo in (PASTO, ARBOL) else 0.0 for c in fila] for fila in self._mapa._casillas],
            dtype=float,
        )

    def plantas_en_radio(self, x: int, y: int, radio: int):
        """(xs, ys, biomasa) de las casillas con comida en el radio, en orden fila a fila."""
        if self._alimento is None:
            self.sincronizar()
        x0, x1 = max(0, x - radio), min(self.ancho, x + radio + 1)
        y0, y1 = max(0, y - radio), min(self.alto, y + radio + 1)
        ventana = self._alimento[y0:y1, x0:x1]
        filas, cols = np.nonzero(ventana > 0)
        return cols + x0, filas + y0, ventana[filas, cols]

    @property
    def ancho(self) -> int:
        return self._mapa.ancho

    @property
    def alto(self) -> int:
        return self._mapa.alto

    def en_limites(self, x: int, y: int) -> bool:
        return self._mapa.enLimites(x, y)

    def es_transitable(self, x: int, y: int) -> bool:
        return self._mapa.enLimites(x, y) and self._mapa.casilla(x, y).tipo != AGUA

    def biomasa_en(self, x: int, y: int) -> float:
        c = self._mapa.casilla(x, y)
        return c.alimento if c.tipo in (PASTO, ARBOL) else 0.0

    def consumir_biomasa(self, x: int, y: int) -> float:
        c = self._mapa.casilla(x, y)
        if c.tipo not in (PASTO, ARBOL):
            return 0.0
        consumida, c.alimento = c.alimento, 0.0
        if self._alimento is not None:
            self._alimento[y, x] = 0.0
        return consumida

    def hay_fuego(self, x: int, y: int) -> bool:
        return self._mapa.enLimites(x, y) and self._mapa.casilla(x, y).tipo == LLAMAS

    def buscar_en_radio(self, x: int, y: int, radio: int, tipo: str) -> list[Pos]:
        m = self._mapa
        if tipo == TIPO_COMIDA:
            # solo el pasto y el arbol tienen alimento > 0 (encender y quemar lo ponen en 0)
            return [
                (cx, cy)
                for cy in range(max(0, y - radio), min(m.alto, y + radio + 1))
                for cx, c in enumerate(m._casillas[cy][max(0, x - radio) : min(m.ancho, x + radio + 1)], max(0, x - radio))
                if c.alimento > 0
            ]
        if tipo == TIPO_FUEGO:
            if self._fuego is not None and not self._fuego.hayIncendio():
                return []
            return [
                (cx, cy)
                for cy in range(max(0, y - radio), min(m.alto, y + radio + 1))
                for cx, c in enumerate(m._casillas[cy][max(0, x - radio) : min(m.ancho, x + radio + 1)], max(0, x - radio))
                if c.tipo == LLAMAS
            ]
        raise ValueError(f"tipo de busqueda desconocido: {tipo!r}")
