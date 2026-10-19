"""MotorFalso: un motor de mentira para construir y probar la interfaz sin el motor real.

Cuenta ticks, aplica FijarNutrientes, ProvocarEvento y CancelarEvento al inicio del tick
siguiente, y lanza ComandoNoSoportado con los demas comandos. El parametro retardo (en
segundos) simula un motor lento. Sus valores son fijos y solo sirven para pruebas.
"""

import hashlib
import json
import time

import numpy as np

from simulador.contratos.avisos import (
    EventoNaturalIniciado,
    EventoNaturalTerminado,
    OrigenEvento,
)
from simulador.contratos.comandos import (
    CancelarEvento,
    FijarNutrientes,
    ProvocarEvento,
    TipoEvento,
)
from simulador.contratos.errores import ComandoInvalido, ComandoNoSoportado
from simulador.contratos.instantanea import Estacion, EstadoCasilla, InfoEvento, Instantanea
from simulador.contratos.motor import Aviso, Comando, Motor


class MotorFalso(Motor):
    """Motor de prueba que cumple el contrato Motor."""

    def __init__(self, tamano: int = 100, retardo: float = 0.0):
        self._tamano = tamano
        self.retardo = retardo
        self._tick = 0
        self._nutrientes = 50
        self._eventos: list[TipoEvento] = []
        self._pendientes: list[Comando] = []

    def avanzar(self) -> list[Aviso]:
        if self.retardo > 0:
            time.sleep(self.retardo)
        self._tick += 1
        pendientes, self._pendientes = self._pendientes, []
        avisos: list[Aviso] = []
        for comando in pendientes:
            avisos.extend(self._ejecutar(comando))
        return avisos

    def aplicar(self, comando: Comando) -> None:
        if isinstance(comando, FijarNutrientes):
            if not 0 <= comando.nivel <= 100:
                raise ComandoInvalido("Los nutrientes deben estar entre 0 y 100.")
        elif isinstance(comando, ProvocarEvento):
            if comando.tipo in self._eventos:
                raise ComandoInvalido("Ese evento ya esta activo.")
        elif not isinstance(comando, CancelarEvento):
            raise ComandoNoSoportado(f"MotorFalso no implementa {type(comando).__name__}.")
        self._pendientes.append(comando)

    def obtenerInstantanea(self) -> Instantanea:
        terreno = np.zeros((self._tamano, self._tamano), dtype=np.uint8)
        terreno[:, 0] = int(EstadoCasilla.agua)
        return Instantanea(
            tick=self._tick,
            estacion=Estacion.primavera,
            temperatura=20.0,
            nutrientes=self._nutrientes,
            terreno=terreno,
            criaturas=np.zeros((0, 3), dtype=np.int32),
            especies=(),
            eventos=tuple(InfoEvento(tipo=tipo) for tipo in self._eventos),
            cupo=1000,
        )

    def aEstado(self) -> bytes:
        datos = {
            "tamano": self._tamano,
            "tick": self._tick,
            "nutrientes": self._nutrientes,
            "eventos": [tipo.value for tipo in self._eventos],
        }
        return json.dumps(datos, sort_keys=True).encode("utf-8")

    def huellaEstado(self) -> str:
        return hashlib.sha256(self.aEstado()).hexdigest()

    @classmethod
    def desdeEstado(cls, estado: bytes) -> "MotorFalso":
        datos = json.loads(estado.decode("utf-8"))
        motor = cls(tamano=datos["tamano"])
        motor._tick = datos["tick"]
        motor._nutrientes = datos["nutrientes"]
        motor._eventos = [TipoEvento(valor) for valor in datos["eventos"]]
        return motor

    def _ejecutar(self, comando: Comando) -> list[Aviso]:
        if isinstance(comando, FijarNutrientes):
            self._nutrientes = comando.nivel
        elif isinstance(comando, ProvocarEvento):
            if comando.tipo not in self._eventos:
                self._eventos.append(comando.tipo)
                return [EventoNaturalIniciado(comando.tipo, OrigenEvento.manual, self._tick)]
        elif isinstance(comando, CancelarEvento) and comando.tipo in self._eventos:
            self._eventos.remove(comando.tipo)
            return [EventoNaturalTerminado(comando.tipo, self._tick, cancelado=True)]
        return []