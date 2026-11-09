"""Pruebas de la resolucion de rutas y carpeta de datos del almacenamiento."""

import pytest

from simulador.app.almacenamiento.rutas import (
    NOMBRE_ARCHIVO_BIBLIOTECA,
    VARIABLE_CARPETA_DATOS,
    obtenerCarpetaDatos,
    obtenerRutaBiblioteca,
)


@pytest.mark.requisito("RF-48")
def test_obtener_carpeta_datos_con_variable_de_entorno(tmp_path, monkeypatch):
    carpeta_personalizada = tmp_path / "datos_personalizados"
    monkeypatch.setenv(VARIABLE_CARPETA_DATOS, str(carpeta_personalizada))

    resultado = obtenerCarpetaDatos()

    assert resultado == carpeta_personalizada
    assert resultado.exists()
    assert resultado.is_dir()


@pytest.mark.requisito("RF-48")
def test_obtener_carpeta_datos_sin_variable_usa_localappdata(tmp_path, monkeypatch):
    monkeypatch.delenv(VARIABLE_CARPETA_DATOS, raising=False)
    local_app_data = tmp_path / "LocalAppData"
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))

    resultado = obtenerCarpetaDatos()

    esperado = local_app_data / "Simulador"
    assert resultado == esperado
    assert resultado.exists()
    assert resultado.is_dir()


@pytest.mark.requisito("RF-48")
def test_obtener_carpeta_datos_variable_vacia_usa_defecto(tmp_path, monkeypatch):
    monkeypatch.setenv(VARIABLE_CARPETA_DATOS, "   ")
    local_app_data = tmp_path / "LocalAppData"
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))

    resultado = obtenerCarpetaDatos()

    esperado = local_app_data / "Simulador"
    assert resultado == esperado
    assert resultado.exists()


@pytest.mark.requisito("RF-48")
def test_obtener_ruta_biblioteca(tmp_path, monkeypatch):
    carpeta = tmp_path / "simulador_datos"
    monkeypatch.setenv(VARIABLE_CARPETA_DATOS, str(carpeta))

    ruta_db = obtenerRutaBiblioteca()

    assert ruta_db == carpeta / NOMBRE_ARCHIVO_BIBLIOTECA
    assert ruta_db.parent.exists()
