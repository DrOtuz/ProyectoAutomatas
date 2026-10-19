"""AlmacenamientoMemoria: guarda las simulaciones en memoria, para pruebas y desarrollo."""

from dataclasses import replace
from datetime import datetime

from simulador.contratos.almacenamiento import Almacenamiento, ResumenSimulacion, validarNombre
from simulador.contratos.errores import NombreInvalido, SimulacionNoEncontrada


class AlmacenamientoMemoria(Almacenamiento):
    """Biblioteca de simulaciones que vive solo mientras el programa esta abierto."""

    def __init__(self):
        self._resumenes: dict[int, ResumenSimulacion] = {}
        self._estados: dict[int, bytes] = {}
        self._siguiente_id = 1

    def crear(self, nombre: str, estado: bytes, tick: int, velocidad: int) -> ResumenSimulacion:
        validarNombre(nombre)
        self._comprobarNombreLibre(nombre)
        resumen = ResumenSimulacion(
            simulacion_id=self._siguiente_id,
            nombre=nombre,
            tick=tick,
            fecha_guardado=datetime.now(),
            velocidad=velocidad,
        )
        self._resumenes[resumen.simulacion_id] = resumen
        self._estados[resumen.simulacion_id] = bytes(estado)
        self._siguiente_id += 1
        return resumen

    def guardar(
        self, simulacion_id: int, estado: bytes, tick: int, velocidad: int
    ) -> ResumenSimulacion:
        actual = self._obtener(simulacion_id)
        resumen = replace(actual, tick=tick, velocidad=velocidad, fecha_guardado=datetime.now())
        self._resumenes[simulacion_id] = resumen
        self._estados[simulacion_id] = bytes(estado)
        return resumen

    def cargar(self, simulacion_id: int) -> bytes:
        self._obtener(simulacion_id)
        return self._estados[simulacion_id]

    def listar(self) -> list[ResumenSimulacion]:
        return list(self._resumenes.values())

    def renombrar(self, simulacion_id: int, nombre: str) -> ResumenSimulacion:
        actual = self._obtener(simulacion_id)
        validarNombre(nombre)
        self._comprobarNombreLibre(nombre, excepto_id=simulacion_id)
        resumen = replace(actual, nombre=nombre)
        self._resumenes[simulacion_id] = resumen
        return resumen

    def eliminar(self, simulacion_id: int) -> None:
        self._obtener(simulacion_id)
        del self._resumenes[simulacion_id]
        del self._estados[simulacion_id]

    def _obtener(self, simulacion_id: int) -> ResumenSimulacion:
        if simulacion_id not in self._resumenes:
            raise SimulacionNoEncontrada(f"No existe la simulacion {simulacion_id}.")
        return self._resumenes[simulacion_id]

    def _comprobarNombreLibre(self, nombre: str, excepto_id: int | None = None) -> None:
        for simulacion_id, resumen in self._resumenes.items():
            if simulacion_id != excepto_id and resumen.nombre.casefold() == nombre.casefold():
                raise NombreInvalido("Ya existe una simulacion con ese nombre.")