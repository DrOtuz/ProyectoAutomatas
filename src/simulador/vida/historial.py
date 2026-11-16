"""Historial: la evolucion de cada especie tick a tick, para las graficas.

`HistorialEspecie` guarda la poblacion y los promedios de S, V, R y energia de
UNA especie. `GestorHistorial` crea uno por especie y se alimenta con
`Poblacion.snapshot()` al final de cada tick; los historiales de especies
extintas se conservan para poder graficarlas.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

METRICAS = ("poblacion", "tamano", "velocidad", "vision", "energia")


class HistorialEspecie:
    def __init__(self, nombre: str, max_puntos: int = 2000) -> None:
        if max_puntos < 4:
            raise ValueError("max_puntos debe ser al menos 4")
        self.nombre = nombre
        self.max_puntos = max_puntos
        self._ticks: list[int] = []
        self._valores: dict[str, list[Optional[float]]] = {m: [] for m in METRICAS}

    def __len__(self) -> int:
        return len(self._ticks)

    def registrar(self, tick: int, resumen: Mapping[str, Any]) -> None:
        """Agrega un punto. `resumen` es la entrada de la especie en snapshot()."""
        if self._ticks and tick <= self._ticks[-1]:
            raise ValueError("los ticks deben registrarse en orden creciente")
        self._ticks.append(tick)
        for m in METRICAS:
            self._valores[m].append(resumen.get(m))
        if len(self._ticks) > self.max_puntos:
            self._reducir()

    def _reducir(self) -> None:
        """Descarta uno de cada dos puntos de la mitad antigua."""
        mitad = len(self._ticks) // 2
        indices = list(range(0, mitad, 2)) + list(range(mitad, len(self._ticks)))
        self._ticks = [self._ticks[i] for i in indices]
        for m in METRICAS:
            self._valores[m] = [self._valores[m][i] for i in indices]

    def serie(self, metrica: str) -> list[tuple[int, Optional[float]]]:
        if metrica not in self._valores:
            raise ValueError(f"metrica desconocida: {metrica!r} (use una de {METRICAS})")
        return list(zip(self._ticks, self._valores[metrica]))

    def ultimo(self) -> Optional[dict[str, Any]]:
        if not self._ticks:
            return None
        d: dict[str, Any] = {"tick": self._ticks[-1]}
        for m in METRICAS:
            d[m] = self._valores[m][-1]
        return d

    def a_dict(self) -> dict[str, Any]:
        return {
            "nombre": self.nombre,
            "max_puntos": self.max_puntos,
            "ticks": list(self._ticks),
            "valores": {m: list(v) for m, v in self._valores.items()},
        }

    @classmethod
    def desde_dict(cls, d: Mapping[str, Any]) -> "HistorialEspecie":
        h = cls(d["nombre"], d["max_puntos"])
        h._ticks = list(d["ticks"])
        h._valores = {m: list(d["valores"][m]) for m in METRICAS}
        return h


class GestorHistorial:
    """Un `HistorialEspecie` por especie; se conservan aunque la especie se extinga."""

    def __init__(self, max_puntos: int = 2000) -> None:
        self.max_puntos = max_puntos
        self.historiales: dict[str, HistorialEspecie] = {}

    def registrar(self, tick: int, snapshot: Mapping[str, Mapping[str, Any]]) -> None:
        for nombre, resumen in snapshot.items():
            h = self.historiales.get(nombre)
            if h is None:
                h = self.historiales[nombre] = HistorialEspecie(nombre, self.max_puntos)
            h.registrar(tick, resumen)

    def __getitem__(self, nombre: str) -> HistorialEspecie:
        return self.historiales[nombre]

    def __contains__(self, nombre: str) -> bool:
        return nombre in self.historiales

    def nombres(self) -> list[str]:
        return list(self.historiales)

    def eliminar(self, nombre: str) -> None:
        """Olvida el historial (para cuando el usuario elimina la especie)."""
        self.historiales.pop(nombre, None)

    def a_dict(self) -> dict[str, Any]:
        return {
            "max_puntos": self.max_puntos,
            "historiales": {n: h.a_dict() for n, h in self.historiales.items()},
        }

    @classmethod
    def desde_dict(cls, d: Mapping[str, Any]) -> "GestorHistorial":
        g = cls(d["max_puntos"])
        g.historiales = {n: HistorialEspecie.desde_dict(h) for n, h in d["historiales"].items()}
        return g
