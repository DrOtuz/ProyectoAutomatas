"""RegistroSeries: series de cada especie, tick a tick, para las graficas de la interfaz.

El Ejecutor llama a `registrar` en su hilo con la instantanea de cada tick; la ventana lee con
`serie` desde el hilo principal. Asi no se pierde ningun tick aunque la ventana refresque menos
veces por segundo que el motor avanza, y no hace falta tocar el motor desde la interfaz.
"""

from __future__ import annotations

import threading

from simulador.contratos.instantanea import Instantanea

METRICAS = ("poblacion", "tamano", "velocidad", "vision", "energia")


class RegistroSeries:
    def __init__(self, max_puntos: int = 4000) -> None:
        self._max = max_puntos
        self._cerrojo = threading.Lock()
        self._ticks: dict[int, list[int]] = {}
        self._valores: dict[int, dict[str, list[float | None]]] = {}
        self.version = 0  # sube con cada punto nuevo: la ventana redibuja solo si cambio

    def sembrar(self, series: dict[int, dict[str, list[tuple[int, float | None]]]]) -> None:
        """Carga el historial que ya traia la simulacion (por ejemplo, al cargar un guardado)."""
        with self._cerrojo:
            for especie_id, por_metrica in series.items():
                ticks = [t for t, _ in por_metrica["poblacion"]]
                self._ticks[especie_id] = ticks
                self._valores[especie_id] = {m: [v for _, v in por_metrica[m]] for m in METRICAS}
            self.version += 1

    def registrar(self, instantanea: Instantanea) -> None:
        with self._cerrojo:
            for e in instantanea.especies:
                ticks = self._ticks.setdefault(e.especie_id, [])
                if ticks and ticks[-1] >= instantanea.tick:
                    continue  # ya registrado
                valores = self._valores.setdefault(e.especie_id, {m: [] for m in METRICAS})
                ticks.append(instantanea.tick)
                valores["poblacion"].append(e.poblacion)
                valores["tamano"].append(e.tamano)
                valores["velocidad"].append(e.velocidad)
                valores["vision"].append(e.vision)
                valores["energia"].append(e.energia)
                if len(ticks) > self._max:  # se queda con uno de cada dos de lo viejo
                    mitad = len(ticks) // 2
                    ticks[:mitad] = ticks[:mitad:2]
                    for lista in valores.values():
                        lista[:mitad] = lista[:mitad:2]
            self.version += 1

    def serie(self, especie_id: int) -> tuple[list[int], dict[str, list[float | None]]]:
        """Copia de los ticks y de cada metrica de la especie (listas vacias si no hay)."""
        with self._cerrojo:
            ticks = list(self._ticks.get(especie_id, []))
            valores = {m: list(v) for m, v in self._valores.get(especie_id, {}).items()}
        return ticks, {m: valores.get(m, []) for m in METRICAS}
