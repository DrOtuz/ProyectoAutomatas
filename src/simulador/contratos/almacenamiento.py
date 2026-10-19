"""Almacenamiento: la interfaz con la que la aplicacion guarda y recupera simulaciones.

La implementan AlmacenamientoMemoria (para pruebas) y AlmacenamientoSqlite.
El estado del motor se guarda como bytes opacos: el almacenamiento no los interpreta.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from simulador.contratos.errores import NombreInvalido

# Temporal: pasa a configuracion/app.py cuando exista la configuracion (tarea A-9).
LARGO_MAXIMO_NOMBRE = 60


def validarNombre(nombre: str) -> str:
    """Comprueba las reglas del nombre: de 1 a 60 caracteres y sin espacios en los extremos.

    Devuelve el mismo nombre o lanza NombreInvalido. Que no se repita (sin distinguir
    mayusculas) lo comprueba cada implementacion de Almacenamiento.
    """
    if len(nombre) == 0 or len(nombre) > LARGO_MAXIMO_NOMBRE or nombre != nombre.strip():
        raise NombreInvalido(
            f"El nombre debe tener de 1 a {LARGO_MAXIMO_NOMBRE} caracteres "
            "y no puede empezar ni terminar con espacios."
        )
    return nombre


@dataclass(frozen=True)
class ResumenSimulacion:
    """Datos de una simulacion guardada, sin su estado."""

    simulacion_id: int
    nombre: str
    tick: int
    fecha_guardado: datetime
    velocidad: int


class Almacenamiento(ABC):
    """Operaciones de la biblioteca de simulaciones guardadas."""

    @abstractmethod
    def crear(self, nombre: str, estado: bytes, tick: int, velocidad: int) -> ResumenSimulacion:
        """Guarda una simulacion nueva. Lanza NombreInvalido si el nombre no vale o ya existe."""

    @abstractmethod
    def guardar(
        self, simulacion_id: int, estado: bytes, tick: int, velocidad: int
    ) -> ResumenSimulacion:
        """Reemplaza el estado guardado. Un corte a mitad deja valida la version anterior."""

    @abstractmethod
    def cargar(self, simulacion_id: int) -> bytes:
        """Devuelve el estado guardado. Lanza SimulacionNoEncontrada si no existe."""

    @abstractmethod
    def listar(self) -> list[ResumenSimulacion]:
        """Devuelve las simulaciones guardadas, sin su estado."""

    @abstractmethod
    def renombrar(self, simulacion_id: int, nombre: str) -> ResumenSimulacion:
        """Cambia el nombre. Lanza NombreInvalido o SimulacionNoEncontrada."""

    @abstractmethod
    def eliminar(self, simulacion_id: int) -> None:
        """Borra la simulacion. Lanza SimulacionNoEncontrada si no existe."""