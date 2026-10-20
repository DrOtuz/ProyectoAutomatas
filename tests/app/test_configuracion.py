import dataclasses
import tomllib

import pytest

from simulador.configuracion.app import ConfiguracionApp
from simulador.configuracion.base import ErrorConfiguracion
from simulador.configuracion.cargador import (
    RUTA_POR_DEFECTO,
    Configuracion,
    cargarConfiguracion,
)
from simulador.configuracion.ecosistema import ConfiguracionEcosistema
from simulador.configuracion.vida import ConfiguracionVida


@pytest.mark.requisito("RNF-06")
def test_el_archivo_por_defecto_coincide_con_los_valores_por_defecto():
    esperado = Configuracion(ConfiguracionApp(), ConfiguracionEcosistema(), ConfiguracionVida())
    assert cargarConfiguracion() == esperado


@pytest.mark.requisito("RNF-06")
def test_el_archivo_declara_todas_las_claves_de_app():
    with RUTA_POR_DEFECTO.open("rb") as archivo:
        datos = tomllib.load(archivo)
    claves = {campo.name for campo in dataclasses.fields(ConfiguracionApp)}
    assert set(datos["app"]) == claves


@pytest.mark.requisito("RNF-06")
def test_archivo_inexistente_da_error_claro(tmp_path):
    with pytest.raises(ErrorConfiguracion, match="No se encontro"):
        cargarConfiguracion(tmp_path / "no_existe.toml")


@pytest.mark.requisito("RNF-06")
def test_archivo_mal_formado_da_error_claro(tmp_path):
    ruta = tmp_path / "mala.toml"
    ruta.write_text("[app\n", encoding="utf-8")
    with pytest.raises(ErrorConfiguracion, match="no es valido"):
        cargarConfiguracion(ruta)


@pytest.mark.requisito("RNF-06")
def test_valor_fuera_de_rango_en_el_archivo_se_rechaza(tmp_path):
    ruta = tmp_path / "rango.toml"
    ruta.write_text("[app]\nzoom_maximo = 0\n", encoding="utf-8")
    with pytest.raises(ErrorConfiguracion, match="zoom_maximo"):
        cargarConfiguracion(ruta)


@pytest.mark.requisito("RNF-06")
def test_clave_desconocida_en_el_archivo_se_rechaza(tmp_path):
    ruta = tmp_path / "clave.toml"
    ruta.write_text("[app]\nzoom_maxim = 4\n", encoding="utf-8")
    with pytest.raises(ErrorConfiguracion, match="zoom_maxim"):
        cargarConfiguracion(ruta)


@pytest.mark.requisito("RNF-06")
def test_seccion_desconocida_en_el_archivo_se_rechaza(tmp_path):
    ruta = tmp_path / "seccion.toml"
    ruta.write_text("[otra]\nx = 1\n", encoding="utf-8")
    with pytest.raises(ErrorConfiguracion, match="otra"):
        cargarConfiguracion(ruta)


@pytest.mark.requisito("RNF-06")
def test_un_archivo_parcial_completa_con_los_valores_por_defecto(tmp_path):
    ruta = tmp_path / "parcial.toml"
    ruta.write_text("[app]\nzoom_maximo = 4\n", encoding="utf-8")
    configuracion = cargarConfiguracion(ruta)
    assert configuracion.app.zoom_maximo == 4
    assert configuracion.app.autoguardado_cada_ticks == 1000


@pytest.mark.requisito("RF-15")
def test_la_velocidad_inicial_debe_estar_entre_la_minima_y_la_maxima():
    with pytest.raises(ErrorConfiguracion, match="velocidad_inicial"):
        ConfiguracionApp(velocidad_inicial=100)


@pytest.mark.requisito("RNF-06")
def test_la_figura_debe_ser_una_de_las_permitidas():
    with pytest.raises(ErrorConfiguracion, match="figura_criatura"):
        ConfiguracionApp(figura_criatura="estrella")