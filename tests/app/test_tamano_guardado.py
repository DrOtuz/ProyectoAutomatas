"""RNF-09: el guardado ocupa menos de 20 MB con 1000 criaturas y 5000 muestras por especie.

El motor real todavia no define el formato de su estado (contratos.md: "Formato de guardado"),
y Almacenamiento lo trata como bytes opacos. Por eso la prueba arma un estado simulado con la
forma y el volumen del peor caso y mide el archivo .db que deja AlmacenamientoSqlite en disco.
"""

import io
from pathlib import Path

import numpy as np
import pytest

from simulador.app.almacenamiento.sqlite import AlmacenamientoSqlite

LIMITE_BYTES = 20 * 1024 * 1024

CRIATURAS = 1000
ESPECIES = 12
MUESTRAS_POR_ESPECIE = 5000


COLUMNAS_CRIATURA = 16

COLUMNAS_MUESTRA = 3 + 3 * 7


def _construirEstadoSimulado() -> bytes:
    """Arma un estado grande y poco compresible, como un guardado con el historial lleno."""
    azar = np.random.default_rng(2026)
    terreno = azar.integers(0, 6, size=(100, 100), dtype=np.uint8)
    criaturas = azar.random((CRIATURAS, COLUMNAS_CRIATURA))
    historial = azar.random((ESPECIES, MUESTRAS_POR_ESPECIE, COLUMNAS_MUESTRA))
    contenido = io.BytesIO()
    np.savez(contenido, terreno=terreno, criaturas=criaturas, historial=historial)
    return contenido.getvalue()


@pytest.mark.requisito("RNF-09")
def test_el_guardado_con_1000_criaturas_y_5000_muestras_por_especie_pesa_menos_de_20_mb(tmp_path):
    ruta = tmp_path / "biblioteca.db"
    estado = _construirEstadoSimulado()

    almacenamiento = AlmacenamientoSqlite(ruta)
    try:
        resumen = almacenamiento.crear("Isla grande", estado, tick=50_000, velocidad=20)
        guardado = almacenamiento.cargar(resumen.simulacion_id)
    finally:
        # Windows no deja borrar el archivo temporal mientras la conexion siga abierta.
        almacenamiento.cerrar()

    assert guardado == estado, "el estado guardado no coincide con el que se inserto"
    tamano = Path(ruta).stat().st_size
    assert tamano < LIMITE_BYTES, (
        f"el archivo .db pesa {tamano / 1024 / 1024:.2f} MB y el limite es "
        f"{LIMITE_BYTES / 1024 / 1024:.0f} MB"
    )
