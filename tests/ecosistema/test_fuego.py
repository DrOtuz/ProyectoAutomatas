import copy

import numpy as np
import pytest

from simulador.ecosistema.ciclo import CicloTick
from simulador.ecosistema.eventos import ErrorSimulador, GestorEventos
from simulador.ecosistema.fuego import AutomataFuego
from simulador.ecosistema.mapa import AGUA, ARBOL, LLAMAS, PASTO, QUEMADA, TIERRA, Mapa
from tests.ecosistema.test_eventos import CONFIG as CONFIG_EVENTOS
from tests.ecosistema.test_reloj import CONFIG as CONFIG_RELOJ

# Reloj sin oscilacion y con inflamabilidad 1.0: la probabilidad queda igual a la base
RELOJ = dict(
    CONFIG_RELOJ,
    amplitud_dia=0.0,
    por_estacion={
        e: dict(v, factor_inflamabilidad=1.0, temperatura_base=20.0)
        for e, v in CONFIG_RELOJ["por_estacion"].items()
    },
)
FUEGO = {
    "duracion_llamas": {"pasto": 3, "arbol": 8},
    "ticks_para_regenerar": 150,
    "probabilidad_propagacion": {"pasto": 1.0, "arbol": 1.0},
    "peso_humedad": 1.0,
    "temperatura_referencia": 20.0,
    "sensibilidad_temperatura": 0.0,
    "vecindad": 8,
    "radio_manual_maximo": 3,
}
# Eventos naturales apagados: lambdas en cero, solo ocurre lo que el test provoca
EVENTOS = dict(
    CONFIG_EVENTOS,
    **{
        "lambda": {e: {"sequia": 0.0, "lluvia": 0.0, "foco": 0.0} for e in CONFIG_RELOJ["estaciones"]},
    },
)


def montar(mapa, fuego_cfg=None, eventos_cfg=None, semilla=1):
    from simulador.ecosistema.reloj import Reloj

    rng = np.random.default_rng(semilla)
    ciclo = CicloTick(rng, Reloj(RELOJ), GestorEventos(rng, eventos_cfg or EVENTOS))
    fuego = AutomataFuego(mapa, fuego_cfg or FUEGO)
    ciclo.registrarPaso(4, fuego.paso)
    return ciclo, fuego


def mapaDe(tipo, ancho, alto):
    return Mapa(ancho, alto, tipo)


def tipos(mapa, y=0):
    return [mapa.casilla(x, y).tipo for x in range(mapa.ancho)]


def test_las_llamas_duran_3_ticks_en_pasto():
    m = mapaDe(PASTO, 1, 1)
    ciclo, fuego = montar(m)
    fuego.provocarIncendio(0, 0, 0)
    vistos = []
    for _ in range(5):
        ciclo.ejecutarTick()
        vistos.append(m.casilla(0, 0).tipo)
    assert vistos == [LLAMAS, LLAMAS, LLAMAS, QUEMADA, QUEMADA]


def test_las_llamas_duran_8_ticks_en_arbol():
    m = mapaDe(ARBOL, 1, 1)
    ciclo, fuego = montar(m)
    fuego.provocarIncendio(0, 0, 0)
    vistos = []
    for _ in range(10):
        ciclo.ejecutarTick()
        vistos.append(m.casilla(0, 0).tipo)
    assert vistos == [LLAMAS] * 8 + [QUEMADA] * 2


def test_se_propaga_una_casilla_por_tick_con_probabilidad_uno():
    m = mapaDe(PASTO, 12, 1)
    ciclo, fuego = montar(m, dict(FUEGO, duracion_llamas={"pasto": 50, "arbol": 50}))
    fuego.provocarIncendio(0, 0, 0)
    for n in range(1, 6):
        ciclo.ejecutarTick()
        assert sum(t == LLAMAS for t in tipos(m)) == n


def test_el_agua_frena_el_fuego():
    m = mapaDe(PASTO, 7, 3)
    for y in range(3):
        m.casilla(3, y).tipo = AGUA
    ciclo, fuego = montar(m)
    fuego.provocarIncendio(0, 1, 0)
    for _ in range(30):
        ciclo.ejecutarTick()
    assert all(m.casilla(x, y).tipo == PASTO for x in range(4, 7) for y in range(3))
    assert all(m.casilla(3, y).tipo == AGUA for y in range(3))


def test_la_humedad_maxima_impide_la_propagacion():
    m = mapaDe(PASTO, 5, 1)
    for x in range(1, 5):
        m.casilla(x, 0).humedad = 1.0
    ciclo, fuego = montar(m)
    fuego.provocarIncendio(0, 0, 0)
    for _ in range(10):
        ciclo.ejecutarTick()
    assert tipos(m)[1:] == [PASTO] * 4


def test_la_tierra_y_la_quemada_no_se_prenden():
    m = mapaDe(TIERRA, 3, 1)
    m.casilla(0, 0).tipo = PASTO
    m.casilla(2, 0).tipo = QUEMADA
    ciclo, fuego = montar(m)
    fuego.provocarIncendio(0, 0, 0)
    for _ in range(6):
        ciclo.ejecutarTick()
    assert m.casilla(1, 0).tipo == TIERRA
    assert m.casilla(2, 0).tipo == QUEMADA


def test_la_lluvia_apaga_las_llamas():
    m = mapaDe(ARBOL, 5, 5)
    cfg = dict(EVENTOS, probabilidad_apagar_llama=1.0, factor_lluvia_fuego=0.0)
    ciclo, fuego = montar(m, eventos_cfg=cfg)
    fuego.provocarIncendio(2, 2, 1)
    ciclo.ejecutarTick()
    assert len(fuego.casillasEnLlamas()) == 9
    ciclo.eventos.provocarEvento("lluvia")
    ciclo.ejecutarTick()
    assert fuego.casillasEnLlamas() == []
    assert fuego.incendio is None and fuego.incendio_terminado is True


def test_la_lluvia_reduce_la_propagacion():
    m = mapaDe(PASTO, 5, 1)
    cfg = dict(EVENTOS, factor_lluvia_fuego=0.0)
    ciclo, fuego = montar(m, eventos_cfg=cfg)
    ciclo.eventos.provocarEvento("lluvia")
    fuego.provocarIncendio(0, 0, 0)
    for _ in range(2):
        ciclo.ejecutarTick()
    assert tipos(m)[1:] == [PASTO] * 4


def test_cancelar_convierte_las_llamas_en_quemada_al_tick_siguiente():
    m = mapaDe(ARBOL, 5, 5)
    ciclo, fuego = montar(m)
    fuego.provocarIncendio(2, 2, 1)
    ciclo.ejecutarTick()
    fuego.cancelarIncendio()
    assert len(fuego.casillasEnLlamas()) == 9
    ciclo.ejecutarTick()
    assert fuego.casillasEnLlamas() == []
    assert sum(c.tipo == QUEMADA for c in m.casillas()) == 9
    assert fuego.incendio is None and fuego.incendio_terminado is True


def test_provocar_aplica_a_las_casillas_inflamables_del_radio():
    m = mapaDe(PASTO, 9, 9)
    m.casilla(4, 4).tipo = AGUA
    ciclo, fuego = montar(m)
    fuego.provocarIncendio(4, 4, 2)
    ciclo.ejecutarTick()
    assert len(fuego.casillasEnLlamas()) == 24
    assert fuego.incendio.origen == "manual"
    assert fuego.incendio.tick_inicio == 1


def test_ordenes_invalidas_se_rechazan():
    m = mapaDe(TIERRA, 5, 5)
    ciclo, fuego = montar(m)
    with pytest.raises(ErrorSimulador):
        fuego.provocarIncendio(2, 2, 1)  # sin casillas inflamables
    m.casilla(2, 2).tipo = PASTO
    with pytest.raises(ErrorSimulador):
        fuego.provocarIncendio(2, 2, 4)  # radio mayor al maximo
    with pytest.raises(ErrorSimulador):
        fuego.provocarIncendio(9, 9, 0)  # fuera del mapa
    with pytest.raises(ErrorSimulador):
        fuego.cancelarIncendio()  # no hay incendio
    fuego.provocarIncendio(2, 2, 0)
    with pytest.raises(ErrorSimulador):
        fuego.provocarIncendio(2, 2, 0)  # ya hay uno pendiente
    ciclo.ejecutarTick()
    with pytest.raises(ErrorSimulador):
        fuego.provocarIncendio(2, 2, 0)  # ya hay uno activo


def test_foco_natural_prende_una_casilla_inflamable_al_azar():
    def correr(semilla):
        m = mapaDe(PASTO, 10, 10)
        ciclo, fuego = montar(m, semilla=semilla)
        ciclo.registrarPaso(3, lambda c: setattr(c, "foco_natural", True))
        ciclo.ejecutarTick()
        return fuego.casillasEnLlamas(), fuego.incendio.origen

    llamas, origen = correr(5)
    assert len(llamas) == 1 and origen == "natural"
    assert correr(5) == (llamas, origen)
    assert any(correr(s)[0] != llamas for s in range(6, 20))


def test_foco_natural_sin_casillas_inflamables_no_hace_nada():
    m = mapaDe(TIERRA, 4, 4)
    ciclo, fuego = montar(m)
    ciclo.registrarPaso(3, lambda c: setattr(c, "foco_natural", True))
    ciclo.ejecutarTick()
    assert fuego.incendio is None


def test_quemada_regenera_a_tierra_a_los_150_ticks():
    m = mapaDe(PASTO, 1, 1)
    ciclo, fuego = montar(m)
    fuego.provocarIncendio(0, 0, 0)
    for _ in range(4):
        ciclo.ejecutarTick()
    assert m.casilla(0, 0).tipo == QUEMADA
    tick_quemada = m.casilla(0, 0).tick_quemada
    while ciclo.reloj.tick < tick_quemada + 149:
        ciclo.ejecutarTick()
    assert m.casilla(0, 0).tipo == QUEMADA
    ciclo.ejecutarTick()
    assert m.casilla(0, 0).tipo == TIERRA
    assert (0, 0) in fuego.casillas_tocadas


def test_las_casillas_tocadas_incluyen_encendidas_y_quemadas_del_tick():
    m = mapaDe(PASTO, 6, 1)
    ciclo, fuego = montar(m)
    fuego.provocarIncendio(0, 0, 0)
    ciclo.ejecutarTick()
    assert fuego.casillas_tocadas == {(0, 0)}
    ciclo.ejecutarTick()
    assert fuego.casillas_tocadas == {(1, 0)}
    ciclo.ejecutarTick()
    ciclo.ejecutarTick()
    assert (0, 0) in fuego.casillas_tocadas and (3, 0) in fuego.casillas_tocadas


def test_las_casillas_recien_prendidas_no_se_propagan_ese_tick():
    m = mapaDe(PASTO, 5, 5)
    ciclo, fuego = montar(m)
    fuego.provocarIncendio(2, 2, 0)
    ciclo.ejecutarTick()
    assert len(fuego.casillasEnLlamas()) == 1
    ciclo.ejecutarTick()
    assert len(fuego.casillasEnLlamas()) == 9


def test_vecindad_de_4_no_usa_diagonales():
    m = mapaDe(PASTO, 5, 5)
    ciclo, fuego = montar(m, dict(FUEGO, vecindad=4))
    fuego.provocarIncendio(2, 2, 0)
    ciclo.ejecutarTick()
    ciclo.ejecutarTick()
    assert len(fuego.casillasEnLlamas()) == 5


def test_el_incendio_dura_mientras_haya_llamas():
    m = mapaDe(PASTO, 1, 1)
    ciclo, fuego = montar(m)
    fuego.provocarIncendio(0, 0, 0)
    for _ in range(3):
        ciclo.ejecutarTick()
        assert fuego.hayIncendio() and fuego.incendio_terminado is False
    ciclo.ejecutarTick()
    assert not fuego.hayIncendio() and fuego.incendio_terminado is True
    ciclo.ejecutarTick()
    assert fuego.incendio_terminado is False


def test_siempre_se_consumen_los_mismos_sorteos_por_tick():
    m = mapaDe(PASTO, 8, 6)
    ciclo, fuego = montar(m, semilla=7)
    referencia = np.random.default_rng(7)
    for tick in range(40):
        if tick == 10:
            fuego.provocarIncendio(4, 3, 1)
        ciclo.ejecutarTick()
        referencia.random(5)
        referencia.random((6, 8))
        referencia.random((6, 8))
        referencia.random()
    assert ciclo.rng.random() == referencia.random()


def test_misma_semilla_misma_historia_de_fuego():
    def correr():
        m = mapaDe(PASTO, 30, 30)
        cfg = dict(FUEGO, probabilidad_propagacion={"pasto": 0.3, "arbol": 0.2})
        ciclo, fuego = montar(m, cfg, semilla=11)
        ciclo.registrarPaso(3, lambda c: setattr(c, "foco_natural", c.reloj.tick % 40 == 1))
        historia = []
        for _ in range(600):
            ciclo.ejecutarTick()
            historia.append(tuple(fuego.casillasEnLlamas()))
        return historia

    assert correr() == correr()


def test_estado_se_guarda_y_se_carga_igual():
    m = mapaDe(ARBOL, 20, 20)
    cfg = dict(FUEGO, probabilidad_propagacion={"pasto": 0.3, "arbol": 0.25})
    ciclo, fuego = montar(m, cfg, semilla=3)
    fuego.provocarIncendio(10, 10, 1)
    for _ in range(12):
        ciclo.ejecutarTick()
    fuego.cancelarIncendio()

    mapa2 = copy.deepcopy(m)
    ciclo2, fuego2 = montar(mapa2, cfg)
    ciclo2.rng.bit_generator.state = copy.deepcopy(ciclo.rng.bit_generator.state)
    ciclo2.reloj.cargarEstado(ciclo.reloj.aEstado())
    ciclo2.eventos.cargarEstado(ciclo.eventos.aEstado())
    fuego2.cargarEstado(fuego.aEstado())
    assert fuego2.aEstado() == fuego.aEstado()
    assert fuego2.casillasEnLlamas() == fuego.casillasEnLlamas()

    for _ in range(20):
        ciclo.ejecutarTick()
        ciclo2.ejecutarTick()
        assert fuego2.casillasEnLlamas() == fuego.casillasEnLlamas()
        assert fuego2.aEstado() == fuego.aEstado()
    assert [c.tipo for c in m.casillas()] == [c.tipo for c in mapa2.casillas()]


def test_un_incendio_en_un_mapa_grande_cabe_en_el_presupuesto_de_tiempo():
    import time

    m = mapaDe(ARBOL, 100, 100)
    ciclo, fuego = montar(m, dict(FUEGO, probabilidad_propagacion={"pasto": 0.3, "arbol": 0.3}))
    fuego.provocarIncendio(50, 50, 3)
    inicio = time.perf_counter()
    for _ in range(60):
        ciclo.ejecutarTick()
    assert time.perf_counter() - inicio < 5.0
