"""Definiciones de estilo y paletas de color para la interfaz grafica (RNF-11)."""

import numpy as np

from simulador.contratos.instantanea import EstadoCasilla

# Paleta oficial de 12 colores de especies (RF-55)
PALETA_ESPECIES: tuple[str, ...] = (
    "#0606F9",
    "#06F906",
    "#F9062F",
    "#06D0F9",
    "#C7A705",
    "#EC79D9",
    "#6AFBB3",
    "#773E22",
    "#223077",
    "#F906F9",
    "#6A6AFB",
    "#D0F906",
)

# Colores de los estados de terreno (RF-13)
COLORES_TERRENO_RGB: dict[EstadoCasilla, tuple[int, int, int]] = {
    EstadoCasilla.tierra: (201, 166, 107),  # #C9A66B
    EstadoCasilla.agua: (46, 134, 222),      # #2E86DE
    EstadoCasilla.pasto: (139, 195, 74),     # #8BC34A
    EstadoCasilla.arbol: (27, 94, 32),       # #1B5E20
    EstadoCasilla.llamas: (255, 109, 0),     # #FF6D00
    EstadoCasilla.quemada: (62, 62, 62),     # #3E3E3E
}


def construirTablaColoresTerreno() -> np.ndarray:
    """Construye un arreglo LUT de 256 x 3 (RGB) para mapear EstadoCasilla a pixeles."""
    lut = np.zeros((256, 3), dtype=np.uint8)
    for estado, rgb in COLORES_TERRENO_RGB.items():
        lut[int(estado)] = rgb
    return lut
