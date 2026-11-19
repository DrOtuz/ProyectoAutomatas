"""Vegetacion: humedad, crecimiento de pasto y arbol y regeneracion del alimento.

Paso 5 del ciclo (despues del fuego). Consumo de azar fijo: una sola llamada
rng.random((alto, ancho)) por tick, para el cambio de tierra a pasto y de pasto a arbol.

Los nutrientes (0 a 100) escalan el crecimiento: con 50 el factor es 1.0.
"""
from __future__ import annotations

import numpy as np

from simulador.ecosistema.mapa import AGUA, ARBOL, PASTO, TIERRA


class Vegetacion:
    def __init__(self, mapa, config: dict | None = None) -> None:
        if config is None:
            from simulador.configuracion.ecosistema import VEGETACION

            config = VEGETACION
        self._mapa = mapa
        self._cfg = config
        self.nutrientes = int(config["nutrientes_iniciales"])
        self._base = self._calcularHumedadBase()
        for fila in range(mapa.alto):
            for x in range(mapa.ancho):
                mapa.casilla(x, fila).humedad = float(self._base[fila, x])

    def _calcularHumedadBase(self) -> np.ndarray:
        """1.0 en el agua y baja linealmente hasta 0 a `radio_humedad` casillas (Chebyshev)."""
        m = self._mapa
        radio = self._cfg["radio_humedad"]
        agua = np.zeros((m.alto, m.ancho), dtype=bool)
        for c in m.casillas():
            if c.tipo == AGUA:
                agua[c.coordenada[1], c.coordenada[0]] = True
        distancia = np.full((m.alto, m.ancho), radio + 1, dtype=float)
        ys, xs = np.nonzero(agua)
        for y, x in zip(ys, xs, strict=True):
            y0, y1 = max(0, y - radio), min(m.alto, y + radio + 1)
            x0, x1 = max(0, x - radio), min(m.ancho, x + radio + 1)
            yy, xx = np.mgrid[y0:y1, x0:x1]
            d = np.maximum(abs(yy - y), abs(xx - x))
            distancia[y0:y1, x0:x1] = np.minimum(distancia[y0:y1, x0:x1], d)
        return np.clip(1.0 - distancia / (radio + 1), 0.0, 1.0)

    def sembrar(self, rng) -> None:
        """Reparte pasto y arboles sobre la tierra desnuda, mas cerca del agua.

        Se usa al empezar con un mapa dibujado en el editor, que solo trae tierra y agua.
        Usa su propio generador para no tocar el del ciclo.
        """
        m = self._mapa
        sorteo = rng.random((m.alto, m.ancho, 2))
        for y, fila in enumerate(m._casillas):
            for x, c in enumerate(fila):
                if c.tipo != TIERRA:
                    continue
                humedad = self._base[y, x]
                if sorteo[y, x, 0] < 0.15 + 0.75 * humedad:
                    c.tipo = PASTO
                    if sorteo[y, x, 1] < 0.25 * humedad:
                        c.tipo = ARBOL
                    c.alimento = self._cfg["alimento_maximo"]["pasto" if c.tipo == PASTO else "arbol"]

    def paso(self, ciclo) -> None:
        m = self._mapa
        cfg = self._cfg
        sorteo = ciclo.rng.random((m.alto, m.ancho))
        estacion = ciclo.reloj.factoresEstacion()
        crecimiento = estacion["factor_crecimiento"] * ciclo.eventos.factorCrecimiento() * (self.nutrientes / 50.0)
        modificador = ciclo.eventos.modificadorHumedad()
        factor_humedad = estacion["factor_humedad"]
        inercia = cfg["inercia_humedad"]
        maximo, regen, prob = cfg["alimento_maximo"], cfg["regeneracion"], cfg["probabilidad_crecer"]

        for y, fila in enumerate(m._casillas):
            base_fila = self._base[y]
            sorteo_fila = sorteo[y]
            for x, c in enumerate(fila):
                objetivo = min(1.0, max(0.0, base_fila[x] * factor_humedad + modificador))
                c.humedad += inercia * (objetivo - c.humedad)
                tipo = c.tipo
                if tipo == PASTO or tipo == ARBOL:
                    nombre = "pasto" if tipo == PASTO else "arbol"
                    c.alimento = min(maximo[nombre], c.alimento + regen[nombre] * crecimiento)
                    if tipo == PASTO and sorteo_fila[x] < prob["pasto"] * crecimiento * (0.5 + c.humedad):
                        c.evolucionar()
                elif tipo == TIERRA and sorteo_fila[x] < prob["tierra"] * crecimiento * (0.5 + c.humedad):
                    c.evolucionar()
                    c.alimento = 0.0

    def aEstado(self) -> dict:
        return {"nutrientes": self.nutrientes}

    def cargarEstado(self, estado: dict) -> None:
        self.nutrientes = int(estado["nutrientes"])
