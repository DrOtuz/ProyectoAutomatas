from simulador.ecosistema.mapa import ARBOL, LLAMAS, PASTO, QUEMADA, TIERRA, Casilla, Mapa


def test_encender_pierde_el_alimento_y_recuerda_la_vegetacion():
    c = Casilla(ARBOL, (0, 0), alimento=3)
    c.encender(10)
    assert c.tipo == LLAMAS
    assert c.alimento == 0
    assert c.vegetacion_previa == ARBOL
    assert c.tick_inicio_llamas == 10


def test_solo_pasto_y_arbol_se_encienden():
    import pytest

    for tipo in (TIERRA, QUEMADA):
        with pytest.raises(ValueError):
            Casilla(tipo, (0, 0)).encender(1)


def test_quemada_vuelve_a_tierra_a_los_150_ticks():
    c = Casilla(PASTO, (0, 0))
    c.encender(5)
    c.quemar(20)
    assert c.regenerar(169, 150) is False
    assert c.tipo == QUEMADA
    assert c.regenerar(170, 150) is True
    assert c.tipo == TIERRA


def test_evolucionar_y_involucionar_suben_un_solo_nivel():
    c = Casilla(TIERRA, (0, 0))
    c.evolucionar()
    assert c.tipo == PASTO
    c.evolucionar()
    assert c.tipo == ARBOL
    c.involucionar()
    assert c.tipo == PASTO
    c.involucionar()
    assert c.tipo == TIERRA


def test_casillas_en_radio_respeta_los_bordes_y_chebyshev():
    m = Mapa(5, 5)
    assert len(m.casillasEnRadio(2, 2, 1)) == 9
    assert len(m.casillasEnRadio(0, 0, 1)) == 4
    assert m.casillasEnRadio(0, 0, 0) == [(0, 0)]


def test_en_limites():
    m = Mapa(4, 3)
    assert m.enLimites(3, 2) and not m.enLimites(4, 0) and not m.enLimites(0, -1)
