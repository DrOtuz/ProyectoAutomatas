"""Pruebas de la interfaz Motor del contrato."""

import pytest

from simulador.contratos.motor import Motor


@pytest.mark.requisito("RF-19")
def test_motor_es_una_interfaz_y_no_se_puede_instanciar():
    with pytest.raises(TypeError):
        Motor()


@pytest.mark.requisito("RF-49")
def test_motor_ofrece_los_seis_metodos_del_contrato():
    assert Motor.__abstractmethods__ == {
        "avanzar",
        "aplicar",
        "obtenerInstantanea",
        "aEstado",
        "huellaEstado",
        "desdeEstado",
    }