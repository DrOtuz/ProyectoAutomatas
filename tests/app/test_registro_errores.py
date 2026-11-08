"""Pruebas del registro de errores inesperados y mensajes al usuario (RNF-12)."""

import pytest

from simulador.app.registro_errores import (
    NOMBRE_ARCHIVO_LOG,
    formatearMensajeUsuario,
    obtenerCarpetaDatos,
    obtenerRutaRegistroErrores,
    registrarError,
)


@pytest.mark.requisito("RNF-12")
def test_registrar_error_crea_archivo_con_traceback_y_contexto(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMULADOR_CARPETA_DATOS", str(tmp_path))

    try:
        raise ValueError("Fallo en simulacion de prueba")
    except ValueError as error:
        ruta = registrarError(error, contexto="Paso de prueba")

    assert ruta == tmp_path / NOMBRE_ARCHIVO_LOG
    assert ruta.exists()

    contenido = ruta.read_text(encoding="utf-8")
    assert "FECHA:" in contenido
    assert "CONTEXTO: Paso de prueba" in contenido
    assert "TIPO: ValueError" in contenido
    assert "MENSAJE: Fallo en simulacion de prueba" in contenido
    assert "DETALLE:" in contenido
    assert "raise ValueError" in contenido


@pytest.mark.requisito("RNF-12")
def test_registrar_error_anexa_multiples_entradas(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMULADOR_CARPETA_DATOS", str(tmp_path))

    registrarError("Primer fallo detectado")
    registrarError("Segundo fallo detectado")

    contenido = (tmp_path / NOMBRE_ARCHIVO_LOG).read_text(encoding="utf-8")
    assert "Primer fallo detectado" in contenido
    assert "Segundo fallo detectado" in contenido
    assert contenido.count("FECHA:") == 2


@pytest.mark.requisito("RNF-12")
def test_formatear_mensaje_usuario_incluye_ruta_y_seguridad_de_guardado(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMULADOR_CARPETA_DATOS", str(tmp_path))

    mensaje = formatearMensajeUsuario("Error critico")

    assert "Error critico" in mensaje
    assert "Su ultima simulacion guardada permanece segura" in mensaje
    assert str(tmp_path / NOMBRE_ARCHIVO_LOG) in mensaje


@pytest.mark.requisito("RNF-12")
def test_obtener_ruta_registro_errores_usa_carpeta_datos(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMULADOR_CARPETA_DATOS", str(tmp_path))

    assert obtenerRutaRegistroErrores() == tmp_path / NOMBRE_ARCHIVO_LOG
    assert obtenerCarpetaDatos() == tmp_path
