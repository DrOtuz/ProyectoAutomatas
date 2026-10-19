"""Pruebas de los comandos del contrato."""

import dataclasses

import pytest

from simulador.contratos.comandos import (
    CrearEspecie,
    ExtinguirEspecie,
    FijarNutrientes,
    ProvocarEvento,
    TipoEvento,
)


@pytest.mark.requisito("RF-19")
def test_los_comandos_son_inmutables():
    comando = FijarNutrientes(nivel=50)
    with pytest.raises(dataclasses.FrozenInstanceError):
        comando.nivel = 10


@pytest.mark.requisito("RF-19")
def test_dos_comandos_con_los_mismos_datos_son_iguales():
    assert ExtinguirEspecie(especie_id=1) == ExtinguirEspecie(especie_id=1)


@pytest.mark.requisito("RF-28")
def test_provocar_evento_no_trae_foco_por_defecto():
    comando = ProvocarEvento(tipo=TipoEvento.sequia)
    assert comando.foco_x is None
    assert comando.foco_y is None
    assert comando.radio == 0


@pytest.mark.requisito("RF-37")
def test_crear_especie_sin_genes_usa_los_genes_base():
    comando = CrearEspecie(nombre="Conejos", cantidad=10)
    assert comando.genes is None