"""Simulacion de Vida sin interfaz: para probar y calibrar las constantes.

    python -m simulador.vida.simulacion_vida [ticks] [semilla]

Usa el MapaFalso (no el motor del Subgrupo A), asi que sirve aunque A no haya
entregado nada. Funciones:

    crear_escenario(cfg, semilla)    mapa mediano + tres especies (herbivoro, omnivoro, carnivoro)
    correr(ticks, cfg, semilla)      ejecuta e imprime una tabla cada `cada` ticks
    exportar_csv(historial, ruta)    guarda las series para una hoja de calculo
    barrido(configs, semillas, ticks) cuantas veces sobrevive cada dieta
"""
from __future__ import annotations

import csv
import sys
from collections.abc import Callable, Mapping, Sequence
from random import Random
from typing import Any

from .adaptadores.mapa_falso import MapaFalso
from .config import ConfigVida
from .historial import METRICAS, GestorHistorial
from .poblacion import Poblacion
from .tipos import Dieta

# nombre de la especie -> dieta (los nombres son los del escenario de prueba)
ESPECIES_ESCENARIO: dict[str, Dieta] = {
    "conejo": Dieta.HERBIVORO,
    "zorro": Dieta.OMNIVORO,
    "lobo": Dieta.CARNIVORO,
}
INICIALES = {"conejo": 120, "zorro": 40, "lobo": 20}


class Simulacion:
    """Un mapa, una poblacion y su historial, avanzando juntos."""

    def __init__(self, pob: Poblacion, mapa: MapaFalso) -> None:
        self.pob = pob
        self.mapa = mapa

    @property
    def historial(self) -> GestorHistorial:
        """Las series que Poblacion va llenando en cada tick."""
        return self.pob.historial

    def avanzar(self, temperatura: float | None = None) -> None:
        t = self.pob.cfg.TEMPERATURA_POR_DEFECTO if temperatura is None else temperatura
        self.mapa.regenerar()
        self.pob.actualizar(self.mapa, t)

    def vivas_por_dieta(self) -> dict[str, bool]:
        snap = self.pob.snapshot()
        return {
            dieta.value: any(
                snap[n]["poblacion"] > 0 for n, d in ESPECIES_ESCENARIO.items()
                if d == dieta and n in snap
            )
            for dieta in Dieta
        }


def crear_mapa(semilla: int, ancho: int = 50, alto: int = 50) -> MapaFalso:
    """Terreno repetible: sobre todo pasto, con arboles, agua y suelo vacio."""
    rng = Random(semilla * 7919 + 13)
    mapa = MapaFalso(ancho, alto)
    for y in range(alto):
        for x in range(ancho):
            r = rng.random()
            if r < 0.62:
                mapa.poner_pasto(x, y)
            elif r < 0.80:
                mapa.poner_arbol(x, y)
            elif r < 0.85:
                mapa.poner_agua(x, y)
    return mapa


def crear_escenario(
    cfg: ConfigVida | None = None, semilla: int = 1,
    ancho: int = 50, alto: int = 50, iniciales: Mapping[str, int] | None = None,
) -> Simulacion:
    cfg = cfg or ConfigVida()
    iniciales = iniciales or INICIALES
    mapa = crear_mapa(semilla, ancho, alto)
    pob = Poblacion(cfg, Random(semilla))
    for nombre, dieta in ESPECIES_ESCENARIO.items():
        pob.crear_especie(nombre, dieta, iniciales[nombre], mapa)
    return Simulacion(pob, mapa)


def correr(
    ticks: int, cfg: ConfigVida | None = None, semilla: int = 1, cada: int = 50,
    salida: Callable[[str], None] | None = print, sim: Simulacion | None = None,
) -> Simulacion:
    sim = sim or crear_escenario(cfg, semilla)
    nombres = list(ESPECIES_ESCENARIO)
    if salida:
        salida("tick   " + "  ".join(f"{n:>7}" for n in nombres) + "   total")
    for _ in range(ticks):
        sim.avanzar()
        if salida and sim.pob.tick % cada == 0:
            snap = sim.pob.snapshot()
            fila = "  ".join(f"{snap[n]['poblacion']:>7}" for n in nombres if n in snap)
            salida(f"{sim.pob.tick:>5}  {fila}   {sim.pob.total():>5}")
    return sim


def exportar_csv(historial: GestorHistorial, ruta: str) -> None:
    """Una fila por tick y una columna por especie y metrica (vacio si no hay dato)."""
    nombres = historial.nombres()
    ticks = sorted({t for n in nombres for t, _ in historial[n].serie("poblacion")})
    tablas = {
        (n, m): dict(historial[n].serie(m)) for n in nombres for m in METRICAS
    }
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tick"] + [f"{n}_{m}" for n in nombres for m in METRICAS])
        for t in ticks:
            fila: list[Any] = [t]
            for n in nombres:
                for m in METRICAS:
                    v = tablas[(n, m)].get(t)
                    fila.append("" if v is None else round(v, 6) if isinstance(v, float) else v)
            w.writerow(fila)


def barrido(
    configs: Mapping[str, ConfigVida], semillas: Sequence[int], ticks: int,
    salida: Callable[[str], None] | None = print,
) -> dict[str, dict[str, Any]]:
    """Corre cada configuracion con cada semilla y cuenta en cuantas sobrevive cada dieta.

    Tambien cuenta las corridas que llegaron a saturar el limite de criaturas.
    """
    resultado: dict[str, dict[str, Any]] = {}
    for nombre, cfg in configs.items():
        vivas = {d.value: 0 for d in Dieta}
        saturadas = 0
        todas = 0
        for semilla in semillas:
            sim = crear_escenario(cfg, semilla)
            tope = 0
            for _ in range(ticks):
                sim.avanzar()
                tope = max(tope, sim.pob.total())
            for dieta, ok in sim.vivas_por_dieta().items():
                vivas[dieta] += ok
            saturadas += tope >= cfg.MAX_CRIATURAS
            todas += all(sim.vivas_por_dieta().values())
        resultado[nombre] = {
            "semillas": len(semillas), "vivas": vivas, "coexisten": todas, "saturadas": saturadas
        }
        if salida:
            salida(f"{nombre}: coexisten {todas}/{len(semillas)}  vivas={vivas}  saturadas={saturadas}")
    return resultado


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    correr(n, semilla=s)
