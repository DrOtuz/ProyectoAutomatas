"""Pruebas del MotorFalso."""

import time

import pytest

from simulador.contratos.avisos import EventoNaturalIniciado, EventoNaturalTerminado
from simulador.contratos.comandos import (
    CancelarEvento,
    EliminarEspecie,
    FijarNutrientes,
    ProvocarEvento,
    TipoEvento,
)
from simulador.contratos.errores import ComandoInvalido, ComandoNoSoportado
from simulador.contratos.motor import Motor
from simulador.contratos.motor_falso import MotorFalso


@pytest.mark.requisito("RF-19")
def test_el_motor_falso_cumple_el_contrato_motor():
    assert isinstance(MotorFalso(), Motor)


@pytest.mark.requisito("RF-14")
def test_cada_avance_suma_un_tick():
    motor = MotorFalso()
    motor.avanzar()
    motor.avanzar()
    assert motor.obtenerInstantanea().tick == 2


@pytest.mark.requisito("RF-19")
def test_un_comando_tiene_efecto_en_el_tick_siguiente():
    motor = MotorFalso()
    motor.aplicar(FijarNutrientes(nivel=80))
    assert motor.obtenerInstantanea().nutrientes != 80
    motor.avanzar()
    assert motor.obtenerInstantanea().nutrientes == 80


@pytest.mark.requisito("RF-16")
def test_nutrientes_fuera_de_rango_se_rechazan_sin_cambiar_nada():
    motor = MotorFalso()
    antes = motor.obtenerInstantanea().nutrientes
    with pytest.raises(ComandoInvalido):
        motor.aplicar(FijarNutrientes(nivel=150))
    motor.avanzar()
    assert motor.obtenerInstantanea().nutrientes == antes


@pytest.mark.requisito("RF-19")
def test_un_comando_que_el_motor_no_implementa_lanza_comando_no_soportado():
    motor = MotorFalso()
    with pytest.raises(ComandoNoSoportado):
        motor.aplicar(EliminarEspecie(especie_id=1))


@pytest.mark.requisito("RF-28")
def test_provocar_un_evento_lo_activa_y_avisa():
    motor = MotorFalso()
    motor.aplicar(ProvocarEvento(tipo=TipoEvento.sequia))
    avisos = motor.avanzar()
    assert isinstance(avisos[0], EventoNaturalIniciado)
    assert avisos[0].tick == 1
    assert [evento.tipo for evento in motor.obtenerInstantanea().eventos] == [TipoEvento.sequia]


@pytest.mark.requisito("RF-31")
def test_no_se_puede_provocar_dos_veces_el_mismo_evento():
    motor = MotorFalso()
    motor.aplicar(ProvocarEvento(tipo=TipoEvento.lluvia))
    motor.avanzar()
    with pytest.raises(ComandoInvalido):
        motor.aplicar(ProvocarEvento(tipo=TipoEvento.lluvia))


@pytest.mark.requisito("RF-51")
def test_cancelar_un_evento_lo_termina_y_avisa():
    motor = MotorFalso()
    motor.aplicar(ProvocarEvento(tipo=TipoEvento.sequia))
    motor.avanzar()
    motor.aplicar(CancelarEvento(tipo=TipoEvento.sequia))
    avisos = motor.avanzar()
    assert isinstance(avisos[0], EventoNaturalTerminado)
    assert avisos[0].cancelado is True
    assert motor.obtenerInstantanea().eventos == ()


@pytest.mark.requisito("RF-49")
def test_guardar_y_cargar_da_la_misma_huella():
    motor = MotorFalso()
    motor.aplicar(FijarNutrientes(nivel=70))
    motor.aplicar(ProvocarEvento(tipo=TipoEvento.incendio))
    motor.avanzar()
    copia = MotorFalso.desdeEstado(motor.aEstado())
    assert copia.huellaEstado() == motor.huellaEstado()


@pytest.mark.requisito("RNF-05")
def test_mismos_comandos_dan_la_misma_huella():
    motores = [MotorFalso(), MotorFalso()]
    for motor in motores:
        motor.aplicar(FijarNutrientes(nivel=30))
        motor.avanzar()
        motor.avanzar()
    assert motores[0].huellaEstado() == motores[1].huellaEstado()


@pytest.mark.requisito("RNF-03")
def test_el_retardo_hace_mas_lento_cada_avance():
    motor = MotorFalso(retardo=0.05)
    inicio = time.perf_counter()
    motor.avanzar()
    assert time.perf_counter() - inicio >= 0.04