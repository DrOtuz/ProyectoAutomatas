"""Pruebas del GestorEventos. CONFIG es el diccionario EVENTOS que usan tambien las del fuego."""
import numpy as np
import pytest

from simulador.configuracion.ecosistema import EVENTOS
from simulador.contratos.errores import ErrorSimulador as ErrorContrato
from simulador.ecosistema.ciclo import CicloTick
from simulador.ecosistema.eventos import ErrorSimulador, GestorEventos
from simulador.ecosistema.reloj import Reloj
from tests.ecosistema.test_reloj import CONFIG as CONFIG_RELOJ

CONFIG = EVENTOS
APAGADOS = dict(
    CONFIG, **{"lambda": {e: {"sequia": 0.0, "lluvia": 0.0, "foco": 0.0} for e in CONFIG_RELOJ["estaciones"]}}
)


def ciclo(cfg=CONFIG, semilla=1):
    rng = np.random.default_rng(semilla)
    return CicloTick(rng, Reloj(CONFIG_RELOJ), GestorEventos(rng, cfg))


def test_el_error_es_el_del_contrato():
    assert ErrorSimulador is ErrorContrato


def test_provocar_activa_el_evento_en_el_tick_siguiente_y_termina():
    c = ciclo(APAGADOS)
    c.eventos.provocarEvento("sequia")
    assert c.eventos.activos == {}
    c.ejecutarTick()
    assert "sequia" in c.eventos.activos and c.eventos.iniciados == [("sequia", "manual")]
    assert c.eventos.deltaTemperatura() == CONFIG["delta_temperatura_sequia"]
    for _ in range(CONFIG_RELOJ["ticks_por_estacion"]):
        c.ejecutarTick()
    assert c.eventos.activos == {}


def test_no_se_puede_provocar_dos_veces_ni_cancelar_lo_inactivo():
    c = ciclo(APAGADOS)
    c.eventos.provocarEvento("lluvia")
    with pytest.raises(ErrorSimulador):
        c.eventos.provocarEvento("lluvia")
    with pytest.raises(ErrorSimulador):
        c.eventos.cancelarEvento("sequia")
    with pytest.raises(ErrorSimulador):
        c.eventos.provocarEvento("granizo")


def test_cancelar_termina_el_evento_marcandolo_cancelado():
    c = ciclo(APAGADOS)
    c.eventos.provocarEvento("lluvia")
    c.ejecutarTick()
    c.eventos.cancelarEvento("lluvia")
    c.ejecutarTick()
    assert c.eventos.activos == {} and c.eventos.terminados == [("lluvia", True)]


def test_la_lluvia_cambia_los_factores():
    c = ciclo(APAGADOS)
    assert c.eventos.factorLluviaFuego() == 1.0 and c.eventos.probabilidadApagarLlama() == 0.0
    c.eventos.provocarEvento("lluvia")
    c.ejecutarTick()
    assert c.eventos.factorLluviaFuego() == CONFIG["factor_lluvia_fuego"]
    assert c.eventos.probabilidadApagarLlama() == CONFIG["probabilidad_apagar_llama"]
    assert c.eventos.factorCrecimiento() == CONFIG["factor_crecimiento"]["lluvia"]


def test_los_eventos_naturales_ocurren_con_el_tiempo_y_son_reproducibles():
    def correr():
        c = ciclo(semilla=5)
        historia = []
        for _ in range(8000):
            c.ejecutarTick()
            historia.append((tuple(sorted(c.eventos.activos.items())), c.eventos.foco))
        return historia

    h = correr()
    assert h == correr()
    assert any(("sequia" in dict(a)) for a, _ in h) and any(("lluvia" in dict(a)) for a, _ in h)
    assert any(f for _, f in h)


def test_siempre_consume_cinco_sorteos_por_tick():
    c = ciclo(semilla=9)
    ref = np.random.default_rng(9)
    for _ in range(30):
        c.ejecutarTick()
        ref.random(5)
    assert c.rng.random() == ref.random()


def test_estado_ida_y_vuelta():
    c = ciclo(semilla=2)
    c.eventos.provocarEvento("sequia")
    c.ejecutarTick()
    c2 = ciclo(semilla=2)
    c2.eventos.cargarEstado(c.eventos.aEstado())
    assert c2.eventos.aEstado() == c.eventos.aEstado()
