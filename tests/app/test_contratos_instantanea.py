"""Pruebas de la instantanea del contrato."""

import numpy as np
import pytest

from simulador.contratos.instantanea import Estacion, InfoEspecie, Instantanea


def crearInstantanea(n_criaturas=2):
    especie = InfoEspecie(
        especie_id=1, nombre="Conejos", color=0, poblacion=n_criaturas, extinguida=False
    )
    return Instantanea(
        tick=0,
        estacion=Estacion.primavera,
        temperatura=20.0,
        nutrientes=50,
        terreno=np.zeros((100, 100), dtype=np.uint8),
        criaturas=np.zeros((n_criaturas, 3), dtype=np.int32),
        especies=(especie,),
        eventos=(),
        cupo=1000,
    )


@pytest.mark.requisito("RF-13")
def test_el_terreno_es_de_solo_lectura():
    instantanea = crearInstantanea()
    with pytest.raises(ValueError):
        instantanea.terreno[0, 0] = 1


@pytest.mark.requisito("RF-13")
def test_las_criaturas_son_de_solo_lectura():
    instantanea = crearInstantanea()
    with pytest.raises(ValueError):
        instantanea.criaturas[0, 0] = 1


@pytest.mark.requisito("RF-17")
def test_el_total_de_criaturas_es_el_numero_de_filas():
    assert crearInstantanea(n_criaturas=3).total_criaturas == 3


@pytest.mark.requisito("RF-17")
def test_la_instantanea_guarda_estacion_y_cupo():
    instantanea = crearInstantanea()
    assert instantanea.estacion is Estacion.primavera
    assert instantanea.cupo == 1000