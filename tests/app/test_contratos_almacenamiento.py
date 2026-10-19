"""Pruebas del contrato de almacenamiento."""

import pytest

from simulador.contratos.almacenamiento import Almacenamiento, validarNombre
from simulador.contratos.errores import ErrorSimulador, NombreInvalido, SimulacionNoEncontrada


@pytest.mark.requisito("RF-48")
def test_almacenamiento_es_una_interfaz_y_no_se_puede_instanciar():
    with pytest.raises(TypeError):
        Almacenamiento()


@pytest.mark.requisito("RF-50")
def test_almacenamiento_ofrece_los_seis_metodos_del_contrato():
    assert Almacenamiento.__abstractmethods__ == {
        "crear",
        "guardar",
        "cargar",
        "listar",
        "renombrar",
        "eliminar",
    }


@pytest.mark.requisito("RF-07")
@pytest.mark.parametrize("nombre", ["", " ", " Isla", "Isla ", "x" * 61])
def test_los_nombres_invalidos_se_rechazan(nombre):
    with pytest.raises(NombreInvalido):
        validarNombre(nombre)


@pytest.mark.requisito("RF-07")
@pytest.mark.parametrize("nombre", ["Isla", "a", "x" * 60, "Mi isla 2"])
def test_los_nombres_validos_se_aceptan(nombre):
    assert validarNombre(nombre) == nombre


@pytest.mark.requisito("RF-12")
@pytest.mark.parametrize("clase_error", [NombreInvalido, SimulacionNoEncontrada])
def test_los_errores_de_almacenamiento_son_errores_del_simulador(clase_error):
    with pytest.raises(ErrorSimulador):
        raise clase_error("mensaje")