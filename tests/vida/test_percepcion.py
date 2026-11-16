import random

import pytest

from simulador.vida.percepcion import (
    casillas_en_radio,
    distancia,
    paso_alejando,
    paso_aleatorio,
    paso_hacia,
    vecinos,
)


def libre_en(ancho, alto, bloqueadas=()):
    bloqueadas = set(bloqueadas)
    return lambda p: 0 <= p[0] < ancho and 0 <= p[1] < alto and p not in bloqueadas


def test_distancia_es_chebyshev():
    assert distancia((0, 0), (3, 1)) == 3
    assert distancia((2, 2), (2, 2)) == 0
    assert distancia((5, 5), (2, 9)) == 4
    assert distancia((1, 1), (2, 2)) == 1  # la diagonal cuesta 1


def test_vecinos_son_8_y_distintos():
    v = vecinos((5, 5))
    assert len(v) == 8 and len(set(v)) == 8
    assert (5, 5) not in v
    assert all(distancia((5, 5), p) == 1 for p in v)


def test_casillas_en_radio_en_el_centro():
    c = casillas_en_radio((5, 5), 2, 20, 20)
    assert len(c) == 25
    assert all(distancia((5, 5), p) <= 2 for p in c)
    assert (5, 5) in c


def test_casillas_en_radio_se_recorta_en_los_bordes():
    esquina = casillas_en_radio((0, 0), 2, 10, 10)
    assert len(esquina) == 9  # 3 x 3
    assert min(p[0] for p in esquina) == 0 and min(p[1] for p in esquina) == 0
    otra = casillas_en_radio((9, 9), 3, 10, 10)
    assert len(otra) == 16  # 4 x 4
    assert max(p[0] for p in otra) == 9


def test_casillas_en_radio_sin_centro_y_radio_cero():
    assert (5, 5) not in casillas_en_radio((5, 5), 1, 10, 10, incluir_centro=False)
    assert casillas_en_radio((5, 5), 0, 10, 10) == [(5, 5)]
    with pytest.raises(ValueError):
        casillas_en_radio((5, 5), -1, 10, 10)


def test_paso_hacia_avanza_los_pasos_pedidos():
    libre = libre_en(20, 20)
    assert paso_hacia((0, 0), (10, 0), 1, libre) == (1, 0)
    assert paso_hacia((0, 0), (10, 0), 3, libre) == (3, 0)
    assert paso_hacia((0, 0), (5, 5), 2, libre) == (2, 2)  # en diagonal


def test_paso_hacia_no_se_pasa_del_destino():
    libre = libre_en(20, 20)
    assert paso_hacia((0, 0), (2, 0), 5, libre) == (2, 0)
    assert paso_hacia((4, 4), (4, 4), 3, libre) == (4, 4)
    assert paso_hacia((4, 4), (4, 4), 0, libre) == (4, 4)


def test_paso_hacia_no_pisa_el_destino_si_esta_ocupado():
    destino = (3, 0)
    libre = libre_en(20, 20, bloqueadas=[destino])
    assert paso_hacia((0, 0), destino, 10, libre) == (2, 0)  # queda al lado


def test_paso_hacia_rodea_un_obstaculo_o_se_detiene():
    # la casilla (1, 0) esta bloqueada; puede ir en diagonal
    libre = libre_en(20, 20, bloqueadas=[(1, 0)])
    pos = paso_hacia((0, 0), (5, 0), 1, libre)
    assert pos in {(1, 1), (1, -1)} and libre(pos)
    # encerrada: no se mueve
    encerrada = libre_en(3, 3, bloqueadas=vecinos((1, 1)))
    assert paso_hacia((1, 1), (2, 2), 4, encerrada) == (1, 1)


def test_paso_alejando_aumenta_la_distancia():
    libre = libre_en(30, 30)
    antes = (10, 10)
    amenaza = (8, 10)
    despues = paso_alejando(antes, [amenaza], 1, libre)
    assert distancia(despues, amenaza) > distancia(antes, amenaza)
    despues2 = paso_alejando(antes, [amenaza], 3, libre)
    assert distancia(despues2, amenaza) == distancia(antes, amenaza) + 3


def test_paso_alejando_sin_amenazas_no_se_mueve():
    assert paso_alejando((4, 4), [], 3, libre_en(10, 10)) == (4, 4)


def test_paso_alejando_acorralada_se_queda_o_se_desliza_sin_acercarse():
    libre = libre_en(10, 10)
    # esquina (0,0) con la amenaza en (2,2): no hay forma de alejarse
    pos = paso_alejando((0, 0), [(2, 2)], 3, libre)
    assert distancia(pos, (2, 2)) >= distancia((0, 0), (2, 2))
    assert libre(pos)


def test_paso_alejando_considera_la_amenaza_mas_cercana():
    libre = libre_en(30, 30)
    cerca, lejos = (9, 10), (0, 10)
    pos = paso_alejando((10, 10), [cerca, lejos], 1, libre)
    assert distancia(pos, cerca) == 2


def test_paso_aleatorio_siempre_da_un_paso_valido():
    rng = random.Random(1)
    libre = libre_en(5, 5)
    pos, direccion = (2, 2), (0, 0)
    for _ in range(200):
        nueva, direccion = paso_aleatorio(pos, direccion, 0.7, rng, libre)
        assert libre(nueva) and distancia(pos, nueva) == 1
        assert (nueva[0] - pos[0], nueva[1] - pos[1]) == direccion
        pos = nueva


def test_paso_aleatorio_con_inercia_total_sigue_recto():
    rng = random.Random(3)
    libre = libre_en(50, 50)
    pos, direccion = (5, 25), (1, 0)
    for _ in range(10):
        pos, direccion = paso_aleatorio(pos, direccion, 1.0, rng, libre)
    assert pos == (15, 25) and direccion == (1, 0)


def test_paso_aleatorio_con_inercia_cero_cambia_de_direccion_a_veces():
    rng = random.Random(4)
    libre = libre_en(50, 50)
    direcciones = set()
    pos, direccion = (25, 25), (1, 0)
    for _ in range(100):
        pos, direccion = paso_aleatorio(pos, direccion, 0.0, rng, libre)
        direcciones.add(direccion)
    assert len(direcciones) > 3


def test_paso_aleatorio_atascada_o_bloqueada():
    rng = random.Random(5)
    encerrada = libre_en(3, 3, bloqueadas=vecinos((1, 1)))
    assert paso_aleatorio((1, 1), (1, 0), 0.7, rng, encerrada) == ((1, 1), (0, 0))
    # si la direccion previa esta bloqueada, elige otra libre
    libre = libre_en(10, 10, bloqueadas=[(6, 5)])
    pos, d = paso_aleatorio((5, 5), (1, 0), 1.0, rng, libre)
    assert d != (1, 0) and libre(pos)


def test_paso_aleatorio_es_repetible_con_la_misma_semilla():
    libre = libre_en(20, 20)

    def recorrido(semilla):
        rng, pos, d, trazo = random.Random(semilla), (10, 10), (0, 0), []
        for _ in range(50):
            pos, d = paso_aleatorio(pos, d, 0.7, rng, libre)
            trazo.append(pos)
        return trazo

    assert recorrido(9) == recorrido(9)
    assert recorrido(9) != recorrido(10)
