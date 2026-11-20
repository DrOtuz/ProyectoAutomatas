"""Pruebas de los avisos del contrato."""

import dataclasses

import pytest

from simulador.contratos.avisos import (
    CupoAlcanzado,
    EspecieExtinguida,
    EventoNaturalIniciado,
    EventoNaturalTerminado,
    OrigenEvento,
)
from simulador.contratos.comandos import TipoEvento


@pytest.mark.requisito("RF-41")
def test_los_avisos_son_inmutables():
    aviso = CupoAlcanzado(tick=10, cupo=1000)
    with pytest.raises(dataclasses.FrozenInstanceError):
        aviso.tick = 11


@pytest.mark.requisito("RF-51")
def test_un_evento_terminado_no_esta_cancelado_por_defecto():
    aviso = EventoNaturalTerminado(tipo=TipoEvento.lluvia, tick=50)
    assert aviso.cancelado is False


@pytest.mark.requisito("RF-28")
def test_un_evento_iniciado_guarda_su_origen():
    aviso = EventoNaturalIniciado(tipo=TipoEvento.incendio, origen=OrigenEvento.manual, tick=5)
    assert aviso.origen is OrigenEvento.manual


@pytest.mark.requisito("RF-44")
def test_una_especie_extinguida_guarda_su_nombre():
    aviso = EspecieExtinguida(especie_id=2, nombre="Conejos", tick=300)
    assert aviso.nombre == "Conejos"