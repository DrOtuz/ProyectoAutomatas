import pytest

from simulador.vida.adaptadores.mapa_falso import MapaFalso
from simulador.vida.puertos import TIPO_COMIDA, TIPO_FUEGO, MapaPuerto


def test_cumple_el_puerto():
    assert isinstance(MapaFalso(20, 20), MapaPuerto)


def test_limites_y_transitabilidad():
    m = MapaFalso(20, 20)
    assert m.en_limites(0, 0) and m.en_limites(19, 19)
    assert not m.en_limites(-1, 0) and not m.en_limites(20, 5)
    m.poner_agua(5, 5)
    assert not m.es_transitable(5, 5)
    assert m.es_transitable(5, 6)
    assert not m.es_transitable(30, 30)


def test_se_puede_crear_un_mapa_de_20x20_y_consultar_comida_y_fuego():
    m = MapaFalso(20, 20)
    m.poner_pasto(3, 3)
    m.poner_arbol(4, 3)
    m.poner_fuego(10, 10)
    assert m.biomasa_en(3, 3) == 30
    assert m.biomasa_en(4, 3) == 60
    assert m.biomasa_en(0, 0) == 0
    assert m.hay_fuego(10, 10) and not m.hay_fuego(3, 3)


def test_consumir_biomasa_devuelve_lo_que_habia_y_vacia_la_casilla():
    m = MapaFalso(10, 10)
    m.poner_pasto(2, 2)
    assert m.consumir_biomasa(2, 2) == 30
    assert m.biomasa_en(2, 2) == 0
    assert m.consumir_biomasa(2, 2) == 0
    assert m.consumir_biomasa(7, 7) == 0


def test_regeneracion_del_pasto_y_del_arbol():
    m = MapaFalso(10, 10)
    m.poner_pasto(1, 1)
    m.poner_arbol(2, 2)
    m.consumir_biomasa(1, 1)
    m.consumir_biomasa(2, 2)
    m.regenerar()
    assert m.biomasa_en(1, 1) == 1  # pasto: 1 u por tick
    assert m.biomasa_en(2, 2) == 2  # arbol: 2 u por tick
    for _ in range(100):
        m.regenerar()
    assert m.biomasa_en(1, 1) == 30  # no pasa del maximo
    assert m.biomasa_en(2, 2) == 60


def test_comida_sin_regeneracion_no_crece():
    m = MapaFalso(10, 10)
    m.poner_comida(1, 1, 12.0)
    m.consumir_biomasa(1, 1)
    m.regenerar()
    assert m.biomasa_en(1, 1) == 0


def test_la_comida_no_crece_donde_hay_fuego():
    m = MapaFalso(10, 10)
    m.poner_pasto(1, 1)
    m.consumir_biomasa(1, 1)
    m.poner_fuego(1, 1)
    m.regenerar()
    assert m.biomasa_en(1, 1) == 0


def test_buscar_en_radio_comida_respeta_el_radio_y_los_bordes():
    m = MapaFalso(20, 20)
    m.poner_pasto(5, 5)
    m.poner_pasto(7, 5)
    m.poner_pasto(9, 5)
    assert m.buscar_en_radio(5, 5, 2, TIPO_COMIDA) == [(5, 5), (7, 5)]
    assert m.buscar_en_radio(5, 5, 4, TIPO_COMIDA) == [(5, 5), (7, 5), (9, 5)]
    assert m.buscar_en_radio(5, 5, 1, TIPO_COMIDA) == [(5, 5)]
    m.poner_pasto(0, 0)
    assert m.buscar_en_radio(0, 0, 3, TIPO_COMIDA) == [(0, 0)]  # esquina, sin salirse
    m.consumir_biomasa(5, 5)
    assert (5, 5) not in m.buscar_en_radio(5, 5, 2, TIPO_COMIDA)


def test_buscar_en_radio_fuego_y_tipo_desconocido():
    m = MapaFalso(20, 20)
    m.poner_fuego(10, 10)
    m.poner_fuego(18, 18)
    assert m.buscar_en_radio(9, 9, 2, TIPO_FUEGO) == [(10, 10)]
    assert m.buscar_en_radio(0, 0, 3, TIPO_FUEGO) == []
    with pytest.raises(ValueError):
        m.buscar_en_radio(0, 0, 3, "agua")


def test_el_agua_quita_la_comida_y_no_admite_fuego_ni_comida():
    m = MapaFalso(10, 10)
    m.poner_pasto(3, 3)
    m.poner_agua(3, 3)
    assert m.biomasa_en(3, 3) == 0
    with pytest.raises(ValueError):
        m.poner_pasto(3, 3)
    with pytest.raises(ValueError):
        m.poner_fuego(3, 3)


def test_poner_fuera_del_mapa_falla():
    m = MapaFalso(5, 5)
    for accion in (m.poner_pasto, m.poner_arbol, m.poner_agua, m.poner_fuego):
        with pytest.raises(ValueError):
            accion(5, 0)


def test_propagar_fuego_avanza_como_frente_y_se_apaga_detras():
    m = MapaFalso.desde_texto(["pppppp"])
    m.poner_fuego(0, 0)
    assert m.propagar_fuego() == [(1, 0)]
    assert m.biomasa_en(0, 0) == 0
    assert m.propagar_fuego() == [(2, 0)]
    assert not m.hay_fuego(0, 0) and not m.hay_fuego(1, 0)
    for _ in range(10):
        m.propagar_fuego()
    assert m.casillas_en_fuego() == []  # se acabo la comida


def test_el_fuego_no_cruza_agua_ni_tierra_sin_comida():
    m = MapaFalso.desde_texto(["p~p", "p.p"])
    m.poner_fuego(0, 0)
    m.propagar_fuego()
    assert m.casillas_en_fuego() == [(0, 1)]
    m.propagar_fuego()
    assert m.casillas_en_fuego() == []  # (1,1) es tierra sin comida; no pasa


def test_desde_texto_y_a_texto_son_inversos():
    dibujo = [
        "p.A~*",
        "pp..~",
        "A..pp",
    ]
    m = MapaFalso.desde_texto(dibujo)
    assert (m.ancho, m.alto) == (5, 3)
    assert m.biomasa_en(0, 0) == 30 and m.biomasa_en(2, 0) == 60
    assert not m.es_transitable(3, 0) and m.hay_fuego(4, 0)
    assert m.a_texto().split("\n") == dibujo


def test_desde_texto_rechaza_dibujos_invalidos():
    with pytest.raises(ValueError):
        MapaFalso.desde_texto([])
    with pytest.raises(ValueError):
        MapaFalso.desde_texto(["pp", "p"])
    with pytest.raises(ValueError):
        MapaFalso.desde_texto(["p?"])
    with pytest.raises(ValueError):
        MapaFalso(0, 5)


def test_mapa_grande_100x100():
    m = MapaFalso(100, 100)
    m.poner_pasto(99, 99)
    assert m.buscar_en_radio(95, 95, 4, TIPO_COMIDA) == [(99, 99)]
