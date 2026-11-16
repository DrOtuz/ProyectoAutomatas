"""Puertos: lo que vida/ necesita de otros subgrupos, como interfaces.

vida/ nunca importa el mapa real del Subgrupo A. Solo conoce `MapaPuerto`.
Cuando A entregue su mapa, se escribe un adaptador (adaptadores/mapa_grupo_a.py)
que cumpla este Protocol. Si A cambia nombres o formas, solo cambia el
adaptador. Si vida/ necesita algo nuevo del mapa, se agrega aqui y se anota en
la tabla de dependencias del plan.

Coordenadas: (x, y), con x = columna e y = fila. Biomasa en unidades u
(una criatura de tamano S equivale a 100*S u).
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from .tipos import Pos

# Valores del argumento `tipo` de MapaPuerto.buscar_en_radio. Son la unica
# "palabra compartida" con el mapa; el adaptador los traduce a lo que use A.
TIPO_COMIDA = "comida"  # casillas con biomasa > 0
TIPO_FUEGO = "fuego"  # casillas en llamas


@runtime_checkable
class MapaPuerto(Protocol):
    """Contrato minimo que debe cumplir el mapa para que Vida funcione."""

    ancho: int
    alto: int

    def en_limites(self, x: int, y: int) -> bool:
        """True si (x, y) esta dentro del mapa."""
        ...

    def es_transitable(self, x: int, y: int) -> bool:
        """True si una criatura puede estar en la casilla (por ejemplo, no es agua)."""
        ...

    def biomasa_en(self, x: int, y: int) -> float:
        """Comida disponible en la casilla, en unidades u (0 si no hay)."""
        ...

    def consumir_biomasa(self, x: int, y: int) -> float:
        """Quita toda la comida de la casilla y devuelve cuanta habia (en u)."""
        ...

    def hay_fuego(self, x: int, y: int) -> bool:
        """True si la casilla esta en llamas."""
        ...

    def buscar_en_radio(self, x: int, y: int, radio: int, tipo: str) -> list[Pos]:
        """Casillas a distancia de Chebyshev <= radio que cumplen `tipo`.

        `tipo` es TIPO_COMIDA o TIPO_FUEGO. Incluye la casilla (x, y) si cumple.
        """
        ...
