"""Configuracion con los valores del documento original (v0.1 del plan).

Muchas pruebas verifican cuentas a mano (por ejemplo "un pasto de 30 u da 15 %")
y por eso necesitan estos valores fijos, aunque los defaults de ConfigVida se
recalibren. Las pruebas de simulacion larga tambien los usan para que su
duracion no dependa de la calibracion.
"""
from simulador.vida.config import ConfigVida
from simulador.vida.tipos import Dieta

H, OM, C = Dieta.HERBIVORO, Dieta.OMNIVORO, Dieta.CARNIVORO

CFG_DOC = ConfigVida().con(
    C=0.05,
    K=0.15,
    SIGMA=0.05,
    ETA_PLANTA={H: 0.50, C: 0.0, OM: 0.35},
    ETA_CARNE={H: 0.0, C: 0.80, OM: 0.60},
    PLANTILLAS={H: (1.0, 1.0, 4.0), OM: (1.5, 1.2, 5.0), C: (2.5, 1.6, 6.0)},
)
