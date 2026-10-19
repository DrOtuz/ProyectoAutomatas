"""Motor: la interfaz que la aplicacion usa para mover la simulacion.

La implementan Ecosistema y Vida (clase Simulacion) y tambien MotorFalso, que sirve
para construir y probar la interfaz sin el motor real.

Reglas de uso:
- Se llama siempre desde un solo hilo (el del Ejecutor).
- aplicar valida y encola; el efecto ocurre al inicio del tick siguiente, tambien en pausa.
"""

from abc import ABC, abstractmethod

from simulador.contratos.avisos import (
    CupoAlcanzado,
    EspecieExtinguida,
    EventoNaturalIniciado,
    EventoNaturalTerminado,
)
from simulador.contratos.comandos import (
    AgregarCriaturas,
    CancelarEvento,
    CrearEspecie,
    EliminarCriaturas,
    EliminarEspecie,
    ExtinguirEspecie,
    FijarNutrientes,
    ProvocarEvento,
)
from simulador.contratos.instantanea import Instantanea

Aviso = EventoNaturalIniciado | EventoNaturalTerminado | CupoAlcanzado | EspecieExtinguida

Comando = (
    FijarNutrientes
    | ProvocarEvento
    | CancelarEvento
    | CrearEspecie
    | AgregarCriaturas
    | EliminarCriaturas
    | ExtinguirEspecie
    | EliminarEspecie
)


class Motor(ABC):
    """Operaciones que la aplicacion puede pedirle a la simulacion."""

    @abstractmethod
    def avanzar(self) -> list[Aviso]:
        """Avanza un tick y devuelve los avisos que ocurrieron en ese tick."""

    @abstractmethod
    def aplicar(self, comando: Comando) -> None:
        """Valida el comando y lo encola.

        Lanza ComandoInvalido si algun valor no es correcto (no cambia nada) y
        ComandoNoSoportado si el motor aun no implementa ese comando.
        """

    @abstractmethod
    def obtenerInstantanea(self) -> Instantanea:
        """Devuelve el estado visible actual, de solo lectura."""

    @abstractmethod
    def aEstado(self) -> bytes:
        """Serializa el estado completo del motor en bytes autodescritos."""

    @abstractmethod
    def huellaEstado(self) -> str:
        """Devuelve un resumen del estado: dos motores iguales dan la misma huella."""

    @classmethod
    @abstractmethod
    def desdeEstado(cls, estado: bytes) -> "Motor":
        """Reconstruye un motor desde los bytes de aEstado."""