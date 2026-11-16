"""Funciones puras de distancia, vision y movimiento sobre la cuadricula.

No guardan estado y no conocen criaturas ni mapas: reciben una funcion
`es_libre(pos) -> bool` que dice si una casilla se puede pisar (el que llama
decide que significa "libre": dentro del mapa, transitable, sin fuego, sin
criatura de mas, etc.). El azar siempre llega por un `random.Random`.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from random import Random

from .tipos import Pos

# Las 8 direcciones (dx, dy), en orden fijo para que los empates sean
# deterministas.
DIRECCIONES: tuple[tuple[int, int], ...] = (
    (-1, -1), (0, -1), (1, -1),
    (-1, 0),           (1, 0),
    (-1, 1),  (0, 1),  (1, 1),
)

EsLibre = Callable[[Pos], bool]


def distancia(a: Pos, b: Pos) -> int:
    """Distancia de Chebyshev: max(|dx|, |dy|). Coherente con moverse en 8 direcciones."""
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _dist2(a: Pos, b: Pos) -> int:
    """Distancia euclidiana al cuadrado (solo para desempatar)."""
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def vecinos(pos: Pos) -> list[Pos]:
    """Las 8 casillas alrededor de `pos` (pueden quedar fuera del mapa)."""
    x, y = pos
    return [(x + dx, y + dy) for dx, dy in DIRECCIONES]


def casillas_en_radio(
    pos: Pos, radio: int, ancho: int, alto: int, incluir_centro: bool = True
) -> list[Pos]:
    """Casillas del cuadrado de Chebyshev de lado 2*radio+1, recortado al mapa.

    Se recorre por filas (de arriba a abajo, de izquierda a derecha). Sirve de
    respaldo si el mapa de A no entrega `buscar_en_radio`.
    """
    if radio < 0:
        raise ValueError("radio no puede ser negativo")
    x, y = pos
    x0, x1 = max(0, x - radio), min(ancho - 1, x + radio)
    y0, y1 = max(0, y - radio), min(alto - 1, y + radio)
    return [
        (i, j)
        for j in range(y0, y1 + 1)
        for i in range(x0, x1 + 1)
        if incluir_centro or (i, j) != pos
    ]


def paso_hacia(origen: Pos, destino: Pos, pasos: int, es_libre: EsLibre) -> Pos:
    """Avanza hasta `pasos` casillas hacia `destino` y devuelve donde queda.

    En cada paso elige la casilla libre vecina que mas acerca (distancia de
    Chebyshev y, para desempatar, euclidiana). Si ninguna acerca, se detiene.
    Nunca pisa el propio `destino` si no es libre: queda al lado.
    """
    pos = origen
    for _ in range(pasos):
        if pos == destino:
            break
        mejor: Pos | None = None
        mejor_clave = (distancia(pos, destino), _dist2(pos, destino))
        for vecino in vecinos(pos):
            if not es_libre(vecino):
                continue
            clave = (distancia(vecino, destino), _dist2(vecino, destino))
            if clave < mejor_clave:
                mejor, mejor_clave = vecino, clave
        if mejor is None:
            break
        pos = mejor
    return pos


def _clave_huida(pos: Pos, amenazas: list[Pos]) -> tuple[int, int]:
    """Mayor es mejor: primero la distancia a la amenaza mas cercana."""
    return (
        min(distancia(pos, a) for a in amenazas),
        sum(_dist2(pos, a) for a in amenazas),
    )


def paso_alejando(
    origen: Pos, amenazas: Iterable[Pos], pasos: int, es_libre: EsLibre
) -> Pos:
    """Avanza hasta `pasos` casillas dando, en cada una, el paso que mas
    aumenta la distancia a la amenaza mas cercana. Si no hay paso que mejore
    (acorralada), se queda quieta. Sin amenazas, no se mueve.
    """
    lista = list(amenazas)
    if not lista:
        return origen
    pos = origen
    for _ in range(pasos):
        mejor: Pos | None = None
        mejor_clave = _clave_huida(pos, lista)
        for vecino in vecinos(pos):
            if not es_libre(vecino):
                continue
            clave = _clave_huida(vecino, lista)
            if clave > mejor_clave:
                mejor, mejor_clave = vecino, clave
        if mejor is None:
            break
        pos = mejor
    return pos


def paso_aleatorio(
    origen: Pos,
    direccion_previa: tuple[int, int],
    inercia: float,
    rng: Random,
    es_libre: EsLibre,
) -> tuple[Pos, tuple[int, int]]:
    """Un paso al azar que tiende a repetir la direccion anterior.

    Con probabilidad `inercia` sigue en `direccion_previa` (si esa casilla esta
    libre); si no, elige al azar entre las vecinas libres. Devuelve
    (nueva_pos, nueva_direccion); si no hay ninguna libre, (origen, (0, 0)).
    """
    libres = []
    for direccion in DIRECCIONES:
        destino = (origen[0] + direccion[0], origen[1] + direccion[1])
        if es_libre(destino):
            libres.append((direccion, destino))
    if not libres:
        return origen, (0, 0)

    sigue_recto = rng.random() < inercia  # siempre se consume un numero al azar
    previa = tuple(direccion_previa)
    if sigue_recto and previa != (0, 0):
        for direccion, destino in libres:
            if direccion == previa:
                return destino, direccion
    direccion, destino = rng.choice(libres)
    return destino, direccion
