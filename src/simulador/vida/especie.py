"""Especie: nombre, dieta y ciclo de vida (activa, extinta o eliminada).

Una especie no crea ni mueve criaturas: solo lleva la cuenta de cuales estan
vivas. Quien las crea y las retira es `Poblacion`, que tambien decide cuando
una especie se declara extinta (al final del tick, cuando ya nacieron las crias;
si no, una especie cuyos ultimos padres mueren en el mismo tick en que nacen sus
crias se daria por extinta por error).
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from .criatura import Criatura
from .estadisticas import Estadisticas
from .tipos import Dieta, EstadoEspecie


class Especie:
    def __init__(
        self,
        nombre: str,
        dieta: Dieta,
        plantilla: Estadisticas,
        color: Optional[str] = None,
    ) -> None:
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("la especie necesita un nombre")
        if not isinstance(dieta, Dieta):
            raise ValueError(f"dieta invalida: {dieta!r}")
        self.nombre = nombre
        self.dieta = dieta
        self.plantilla = plantilla  # S, V y R de referencia de sus criaturas iniciales
        self.color = color  # lo asigna la interfaz (C) si es None
        self.estado = EstadoEspecie.ACTIVA
        self._ids: set[int] = set()

    # --- criaturas vivas ---------------------------------------------------------------

    def agregar(self, criatura: Criatura) -> None:
        if self.estado == EstadoEspecie.ELIMINADA:
            raise ValueError(f"la especie {self.nombre!r} fue eliminada")
        if criatura.especie != self.nombre:
            raise ValueError(f"{criatura!r} no es de la especie {self.nombre!r}")
        self._ids.add(criatura.id)

    def quitar(self, criatura: Criatura) -> None:
        """La saca de la cuenta (no hace nada si no estaba).

        No declara la extincion: eso lo hace Poblacion al final del tick."""
        self._ids.discard(criatura.id)

    def contar(self) -> int:
        return len(self._ids)

    @property
    def ids(self) -> frozenset[int]:
        return frozenset(self._ids)

    # --- ciclo de vida -------------------------------------------------------------------

    def extinguir(self) -> None:
        """Marca la especie como EXTINTA. Solo si ya no le quedan criaturas."""
        if self._ids:
            raise ValueError(f"{self.nombre!r} aun tiene {len(self._ids)} criaturas")
        self.estado = EstadoEspecie.EXTINTA

    def reactivar(self) -> None:
        """Una especie extinta vuelve a estar ACTIVA si se le agregan criaturas."""
        if self.estado == EstadoEspecie.EXTINTA:
            self.estado = EstadoEspecie.ACTIVA

    def eliminar(self) -> None:
        """Marca la especie como ELIMINADA (decision del usuario). Poblacion
        se encarga de retirar a sus criaturas."""
        self.estado = EstadoEspecie.ELIMINADA

    # --- guardado y carga ------------------------------------------------------------------

    def a_dict(self) -> dict[str, Any]:
        return {
            "nombre": self.nombre,
            "dieta": self.dieta.value,
            "plantilla": self.plantilla.a_dict(),
            "color": self.color,
            "estado": self.estado.value,
        }

    @classmethod
    def desde_dict(cls, datos: Mapping[str, Any]) -> "Especie":
        """Reconstruye la especie (sin criaturas: Poblacion las vuelve a registrar)."""
        especie = cls(
            datos["nombre"],
            Dieta(datos["dieta"]),
            Estadisticas.desde_dict(datos["plantilla"]),
            datos.get("color"),
        )
        especie.estado = EstadoEspecie(datos["estado"])
        return especie

    def __repr__(self) -> str:
        return f"Especie({self.nombre!r}, {self.dieta.value}, {self.estado.name}, n={self.contar()})"
