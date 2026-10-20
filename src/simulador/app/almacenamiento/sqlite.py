"""AlmacenamientoSqlite: guarda la biblioteca de simulaciones en un archivo SQLite."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from simulador.contratos.almacenamiento import Almacenamiento, ResumenSimulacion, validarNombre
from simulador.contratos.errores import ErrorSimulador, NombreInvalido, SimulacionNoEncontrada

VERSION_ESQUEMA = 1

_CREAR_TABLA_V1 = """
CREATE TABLE simulaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    nombre_clave TEXT NOT NULL UNIQUE,
    tick INTEGER NOT NULL,
    velocidad INTEGER NOT NULL,
    fecha_guardado TEXT NOT NULL,
    estado BLOB NOT NULL
)
"""

_COLUMNAS_RESUMEN = "id, nombre, tick, fecha_guardado, velocidad"


class ErrorEsquema(ErrorSimulador):
    """El archivo de guardado es de una version que este programa no sabe abrir."""


class AlmacenamientoSqlite(Almacenamiento):
    """Biblioteca de simulaciones guardada en un archivo SQLite con version de esquema."""

    def __init__(self, ruta: str | Path) -> None:
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        self._conexion = sqlite3.connect(str(ruta), isolation_level=None)
        try:
            self._prepararEsquema()
        except ErrorSimulador:
            self._conexion.close()
            raise

    def cerrar(self) -> None:
        """Cierra el archivo. Hay que llamarlo antes de borrar o mover el archivo (Windows)."""
        self._conexion.close()

    def crear(self, nombre: str, estado: bytes, tick: int, velocidad: int) -> ResumenSimulacion:
        validarNombre(nombre)
        ahora = datetime.now()
        try:
            with self._transaccion() as conexion:
                cursor = conexion.execute(
                    "INSERT INTO simulaciones "
                    "(nombre, nombre_clave, tick, velocidad, fecha_guardado, estado) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (nombre, nombre.casefold(), tick, velocidad, ahora.isoformat(), bytes(estado)),
                )
        except sqlite3.IntegrityError as error:
            raise NombreInvalido("Ya existe una simulacion con ese nombre.") from error
        return ResumenSimulacion(
            simulacion_id=int(cursor.lastrowid),
            nombre=nombre,
            tick=tick,
            fecha_guardado=ahora,
            velocidad=velocidad,
        )

    def guardar(
        self, simulacion_id: int, estado: bytes, tick: int, velocidad: int
    ) -> ResumenSimulacion:
        with self._transaccion() as conexion:
            cursor = conexion.execute(
                "UPDATE simulaciones "
                "SET tick = ?, velocidad = ?, fecha_guardado = ?, estado = ? WHERE id = ?",
                (tick, velocidad, datetime.now().isoformat(), bytes(estado), simulacion_id),
            )
            if cursor.rowcount == 0:
                raise SimulacionNoEncontrada(f"No existe la simulacion {simulacion_id}.")
            self._puntoDeCorte()
        return self._obtenerResumen(simulacion_id)

    def cargar(self, simulacion_id: int) -> bytes:
        fila = self._conexion.execute(
            "SELECT estado FROM simulaciones WHERE id = ?", (simulacion_id,)
        ).fetchone()
        if fila is None:
            raise SimulacionNoEncontrada(f"No existe la simulacion {simulacion_id}.")
        return bytes(fila[0])

    def listar(self) -> list[ResumenSimulacion]:
        filas = self._conexion.execute(
            f"SELECT {_COLUMNAS_RESUMEN} FROM simulaciones ORDER BY id"
        ).fetchall()
        return [self._aResumen(fila) for fila in filas]

    def renombrar(self, simulacion_id: int, nombre: str) -> ResumenSimulacion:
        self._obtenerResumen(simulacion_id)
        validarNombre(nombre)
        try:
            with self._transaccion() as conexion:
                conexion.execute(
                    "UPDATE simulaciones SET nombre = ?, nombre_clave = ? WHERE id = ?",
                    (nombre, nombre.casefold(), simulacion_id),
                )
        except sqlite3.IntegrityError as error:
            raise NombreInvalido("Ya existe una simulacion con ese nombre.") from error
        return self._obtenerResumen(simulacion_id)

    def eliminar(self, simulacion_id: int) -> None:
        with self._transaccion() as conexion:
            cursor = conexion.execute("DELETE FROM simulaciones WHERE id = ?", (simulacion_id,))
            if cursor.rowcount == 0:
                raise SimulacionNoEncontrada(f"No existe la simulacion {simulacion_id}.")

    def _puntoDeCorte(self) -> None:
        """No hace nada. Las pruebas lo sustituyen para simular un corte a mitad de guardar."""

    def _prepararEsquema(self) -> None:
        version = self._conexion.execute("PRAGMA user_version").fetchone()[0]
        if version > VERSION_ESQUEMA:
            raise ErrorEsquema(
                f"El archivo fue creado por una version mas nueva del programa (esquema "
                f"{version}); este programa conoce hasta el esquema {VERSION_ESQUEMA}."
            )
        if version == 0:
            with self._transaccion() as conexion:
                conexion.execute(_CREAR_TABLA_V1)
                conexion.execute(f"PRAGMA user_version = {VERSION_ESQUEMA}")

    @contextmanager
    def _transaccion(self) -> Iterator[sqlite3.Connection]:
        """Agrupa escrituras: se aplican todas o ninguna."""
        self._conexion.execute("BEGIN IMMEDIATE")
        try:
            yield self._conexion
        except BaseException:
            self._conexion.execute("ROLLBACK")
            raise
        else:
            self._conexion.execute("COMMIT")

    def _obtenerResumen(self, simulacion_id: int) -> ResumenSimulacion:
        fila = self._conexion.execute(
            f"SELECT {_COLUMNAS_RESUMEN} FROM simulaciones WHERE id = ?", (simulacion_id,)
        ).fetchone()
        if fila is None:
            raise SimulacionNoEncontrada(f"No existe la simulacion {simulacion_id}.")
        return self._aResumen(fila)

    @staticmethod
    def _aResumen(fila: tuple[Any, ...]) -> ResumenSimulacion:
        return ResumenSimulacion(
            simulacion_id=fila[0],
            nombre=fila[1],
            tick=fila[2],
            fecha_guardado=datetime.fromisoformat(fila[3]),
            velocidad=fila[4],
        )