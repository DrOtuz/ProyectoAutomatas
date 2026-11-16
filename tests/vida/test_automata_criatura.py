import random

import pytest

from simulador.vida.adaptadores.contexto_falso import ContextoFalso
from simulador.vida.adaptadores.mapa_falso import MapaFalso
from simulador.vida.automata_criatura import AutomataCriatura, ContextoVida
from simulador.vida.config import ConfigVida
from simulador.vida.criatura import Criatura
from simulador.vida.estadisticas import Estadisticas
from simulador.vida.percepcion import distancia
from simulador.vida.tipos import (
    INTENCION_ALIMENTO,
    INTENCION_PAREJA,
    CausaMuerte,
    Dieta,
    Estado,
    TipoObjetivo,
)

from valores_doc import CFG_DOC as CFG
_ids = iter(range(1, 100_000))


# --- ayudas ----------------------------------------------------------------------------


def escenario(ancho=20, alto=20, cfg=CFG, reproduccion_ok=True, semilla=1, mapa=None):
    mapa = mapa or MapaFalso(ancho, alto)
    ctx = ContextoFalso(mapa.ancho, mapa.alto, reproduccion_ok)
    auto = AutomataCriatura(cfg, random.Random(semilla))
    return mapa, ctx, auto


def poner(ctx, dieta, s, v, r, pos, energia=50.0, especie=None, vida_max=100_000, cfg=CFG):
    c = Criatura(
        id=next(_ids),
        especie=especie or dieta.value,
        dieta=dieta,
        stats=Estadisticas(s, v, r),
        pos=pos,
        cfg=cfg,
        vida_max=vida_max,
        energia=energia,
    )
    return ctx.agregar(c)


def herbivoro(ctx, pos, energia=50.0, especie=None, v=1.0, r=4.0, s=1.0, **kw):
    return poner(ctx, Dieta.HERBIVORO, s, v, r, pos, energia, especie, **kw)


def omnivoro(ctx, pos, energia=50.0, especie=None, **kw):
    return poner(ctx, Dieta.OMNIVORO, 1.5, 1.2, 5.0, pos, energia, especie, **kw)


def carnivoro(ctx, pos, energia=50.0, especie=None, v=1.6, r=6.0, s=2.5, **kw):
    return poner(ctx, Dieta.CARNIVORO, s, v, r, pos, energia, especie, **kw)


def jugar(auto, c, mapa, ctx, temperatura=22.0):
    c.iniciar_tick()
    auto.turno(c, mapa, ctx, temperatura)


def tick(auto, criaturas, mapa, ctx, temperatura=22.0):
    """Un tick completo: todas reinician sus marcas y luego juegan en orden."""
    for c in criaturas:
        if c.viva:
            c.iniciar_tick()
    for c in criaturas:
        auto.turno(c, mapa, ctx, temperatura)


def decidir(auto, c, mapa, ctx):
    return auto.elegir_estado(c, auto.percibir(c, mapa, ctx))


# --- contrato ----------------------------------------------------------------------------


def test_el_contexto_falso_cumple_el_protocolo():
    assert isinstance(ContextoFalso(5, 5), ContextoVida)


# --- comer: como capturar una pieza ---------------------------------------------------------


def test_el_herbivoro_come_el_pasto_vecino_en_el_mismo_tick():
    mapa, ctx, auto = escenario()
    mapa.poner_pasto(6, 5)
    h = herbivoro(ctx, (5, 5), energia=30.0)
    jugar(auto, h, mapa, ctx)
    assert h.pos == (6, 5) and h.estado == Estado.BUSCAR_ALIMENTO
    assert mapa.biomasa_en(6, 5) == 0
    assert h.energia == pytest.approx(30 + 15 - 0.65)  # comio 15 y pago por moverse


def test_un_pasto_lejano_se_alcanza_avanzando_y_se_come_al_llegar():
    mapa, ctx, auto = escenario()
    mapa.poner_pasto(8, 5)
    h = herbivoro(ctx, (5, 5), energia=30.0)
    jugar(auto, h, mapa, ctx)
    assert h.pos == (6, 5) and h.energia == pytest.approx(30 - 0.65)
    jugar(auto, h, mapa, ctx)
    assert h.pos == (7, 5) and mapa.biomasa_en(8, 5) == 30
    jugar(auto, h, mapa, ctx)  # d=1 <= 1 paso: entra y come
    assert h.pos == (8, 5) and mapa.biomasa_en(8, 5) == 0
    assert h.energia == pytest.approx(30 - 3 * 0.65 + 15)


def test_con_mas_velocidad_alcanza_comida_mas_lejana_en_un_tick():
    mapa, ctx, auto = escenario()
    mapa.poner_pasto(8, 5)
    h = herbivoro(ctx, (5, 5), energia=30.0, v=3.0)
    jugar(auto, h, mapa, ctx)
    assert h.pos == (8, 5) and mapa.biomasa_en(8, 5) == 0


def test_sobre_el_pasto_come_sin_moverse_y_paga_el_gasto_quieto():
    mapa, ctx, auto = escenario()
    mapa.poner_pasto(5, 5)
    h = herbivoro(ctx, (5, 5), energia=30.0)
    jugar(auto, h, mapa, ctx)
    assert h.pos == (5, 5) and not h.se_movio
    assert h.energia == pytest.approx(30 + 15 - 0.50)


def test_elige_la_comida_que_maximiza_ganancia_sobre_distancia_mas_uno():
    mapa, ctx, auto = escenario()
    h = herbivoro(ctx, (5, 5))
    mapa.poner_pasto(6, 5)  # 15 / 2 = 7.5
    mapa.poner_arbol(7, 5)  # 30 / 3 = 10  -> gana el arbol
    _, objetivo = decidir(auto, h, mapa, ctx)
    assert objetivo.pos == (7, 5) and objetivo.tipo == TipoObjetivo.PLANTA

    mapa2, ctx2, auto2 = escenario()
    h2 = herbivoro(ctx2, (5, 5))
    mapa2.poner_pasto(6, 5)  # 7.5
    mapa2.poner_arbol(9, 5)  # 30 / 5 = 6  -> gana el pasto
    _, objetivo2 = decidir(auto2, h2, mapa2, ctx2)
    assert objetivo2.pos == (6, 5)


def test_puntuar_comida_con_los_ejemplos_del_documento():
    mapa, ctx, auto = escenario()
    mapa.poner_pasto(6, 5)
    mapa.poner_arbol(8, 5)
    h = herbivoro(ctx, (5, 5))
    p = auto.percibir(h, mapa, ctx)
    por_pos = {o.pos: o for o in p.plantas}
    assert auto.puntuar_comida(h, por_pos[(6, 5)]) == pytest.approx(7.5)
    assert por_pos[(6, 5)].ganancia == pytest.approx(15.0)
    assert por_pos[(8, 5)].ganancia == pytest.approx(30.0)
    assert auto.puntuar_comida(h, por_pos[(8, 5)]) == pytest.approx(7.5)


def test_el_omnivoro_prefiere_la_presa_cuando_rinde_mas():
    mapa, ctx, auto = escenario()
    mapa.poner_pasto(6, 5)  # 7 / 2 = 3.5
    o = omnivoro(ctx, (5, 5))
    herbivoro(ctx, (7, 5), especie="conejo")  # 40 / 3 = 13.3
    _, objetivo = decidir(auto, o, mapa, ctx)
    assert objetivo.tipo == TipoObjetivo.PRESA and objetivo.pos == (7, 5)


def test_la_vision_limita_lo_que_ve():
    mapa, ctx, auto = escenario()
    mapa.poner_pasto(10, 5)  # distancia 5; R = 4
    h = herbivoro(ctx, (5, 5))
    estado, objetivo = decidir(auto, h, mapa, ctx)
    assert estado == Estado.EXPLORAR and objetivo is None
    mapa.poner_pasto(9, 5)  # distancia 4: justo en el borde
    estado, objetivo = decidir(auto, h, mapa, ctx)
    assert estado == Estado.BUSCAR_ALIMENTO and objetivo.pos == (9, 5)


def test_un_carnivoro_ignora_las_plantas():
    mapa, ctx, auto = escenario()
    mapa.poner_pasto(6, 5)
    c = carnivoro(ctx, (5, 5))
    assert auto.percibir(c, mapa, ctx).plantas == []
    assert decidir(auto, c, mapa, ctx)[0] == Estado.EXPLORAR


def test_una_casilla_de_comida_ocupada_por_otra_criatura_no_es_objetivo():
    mapa, ctx, auto = escenario()
    mapa.poner_pasto(6, 5)
    a = herbivoro(ctx, (5, 5))
    b = herbivoro(ctx, (6, 5))
    assert auto.percibir(a, mapa, ctx).plantas == []
    assert [o.pos for o in auto.percibir(b, mapa, ctx).plantas] == [(6, 5)]


def test_no_hay_comida_en_casillas_con_fuego():
    mapa, ctx, auto = escenario()
    mapa.poner_pasto(6, 5)
    mapa.poner_fuego(6, 5)
    h = herbivoro(ctx, (5, 5))
    assert auto.percibir(h, mapa, ctx).plantas == []


# --- huir ---------------------------------------------------------------------------------------


def test_un_herbivoro_huye_de_un_carnivoro_grande():
    mapa, ctx, auto = escenario()
    h = herbivoro(ctx, (10, 10))
    c = carnivoro(ctx, (8, 10))
    assert decidir(auto, h, mapa, ctx)[0] == Estado.HUIR
    antes = distancia(h.pos, c.pos)
    jugar(auto, h, mapa, ctx)
    assert h.estado == Estado.HUIR and distancia(h.pos, c.pos) > antes


def test_huir_tiene_prioridad_sobre_la_comida_cercana():
    mapa, ctx, auto = escenario()
    mapa.poner_pasto(11, 10)
    h = herbivoro(ctx, (10, 10), energia=30.0)
    carnivoro(ctx, (8, 10))
    assert decidir(auto, h, mapa, ctx)[0] == Estado.HUIR


def test_un_herbivoro_grande_no_asusta():
    mapa, ctx, auto = escenario()
    h = herbivoro(ctx, (10, 10))
    herbivoro(ctx, (8, 10), especie="bufalo", s=5.0)
    assert not auto.percibir(h, mapa, ctx).hay_amenaza


def test_quien_cumple_el_ratio_de_depredacion_es_amenaza_y_quien_no_cumple_no():
    mapa, ctx, auto = escenario()
    h = herbivoro(ctx, (10, 10))
    o = omnivoro(ctx, (9, 10))  # 1.5 >= 1.2 * 1.0
    assert auto.percibir(h, mapa, ctx).hay_amenaza
    o.morir(CausaMuerte.HAMBRE)
    assert not auto.percibir(h, mapa, ctx).hay_amenaza  # los muertos no asustan
    mapa2, ctx2, auto2 = escenario()
    h2 = herbivoro(ctx2, (10, 10))
    carnivoro(ctx2, (9, 10), s=1.1, especie="zorro")  # 1.1 < 1.2
    assert not auto2.percibir(h2, mapa2, ctx2).hay_amenaza


def test_una_amenaza_fuera_del_radio_de_vision_no_se_ve():
    mapa, ctx, auto = escenario()
    h = herbivoro(ctx, (10, 10))
    carnivoro(ctx, (5, 10))  # distancia 5 > R = 4
    assert decidir(auto, h, mapa, ctx)[0] == Estado.EXPLORAR


def test_huye_del_fuego_dentro_del_radio_y_lo_ignora_fuera():
    mapa, ctx, auto = escenario()
    mapa.poner_fuego(8, 10)
    h = herbivoro(ctx, (10, 10))
    assert decidir(auto, h, mapa, ctx)[0] == Estado.HUIR
    jugar(auto, h, mapa, ctx)
    assert distancia(h.pos, (8, 10)) > 2

    mapa2, ctx2, auto2 = escenario()
    mapa2.poner_fuego(4, 10)  # distancia 6
    h2 = herbivoro(ctx2, (10, 10))
    assert decidir(auto2, h2, mapa2, ctx2)[0] == Estado.EXPLORAR


def test_al_huir_no_entra_a_casillas_con_fuego_ni_agua():
    mapa, ctx, auto = escenario(ancho=5, alto=3)
    for y in range(3):
        mapa.poner_agua(4, y)  # pared de agua al este
    mapa.poner_fuego(0, 1)
    h = herbivoro(ctx, (2, 1))
    for _ in range(6):
        jugar(auto, h, mapa, ctx)
        assert mapa.es_transitable(*h.pos) and not mapa.hay_fuego(*h.pos)


# --- pareja e histeresis --------------------------------------------------------------------------


def test_dos_criaturas_con_energia_se_acercan_y_se_reproducen():
    mapa, ctx, auto = escenario()
    a = herbivoro(ctx, (5, 5), energia=70.0)
    b = herbivoro(ctx, (8, 5), energia=70.0)
    tick(auto, [a, b], mapa, ctx)  # a: 5->6 ; b: ve a a distancia 2 -> 8->7
    assert a.estado == Estado.BUSCAR_PAREJA and b.estado == Estado.BUSCAR_PAREJA
    assert (a.pos, b.pos) == ((6, 5), (7, 5))
    tick(auto, [a, b], mapa, ctx)
    assert ctx.reproducciones == [(a, b)]
    assert a.pos == (6, 5) and not a.se_movio  # reproducirse ocupa el tick


def test_la_pareja_de_una_reproduccion_no_actua_pero_si_paga_y_envejece():
    mapa, ctx, auto = escenario()
    a = herbivoro(ctx, (5, 5), energia=70.0)
    b = herbivoro(ctx, (6, 5), energia=70.0)
    tick(auto, [a, b], mapa, ctx)
    assert ctx.reproducciones == [(a, b)]
    assert b.turno_hecho and b.pos == (6, 5)
    assert b.energia == pytest.approx(70 - 0.50) and b.edad == 1
    assert len(ctx.reproducciones) == 1  # b no inicio otra


def test_dos_criaturas_que_se_buscan_se_encuentran_aunque_ninguna_estuviera_en_pareja():
    # regresion: exigir que la otra ya estuviera en BUSCAR_PAREJA bloqueaba el encuentro
    mapa, ctx, auto = escenario()
    a = herbivoro(ctx, (5, 5), energia=70.0)
    b = herbivoro(ctx, (9, 5), energia=70.0)
    assert a.estado == Estado.EXPLORAR and b.estado == Estado.EXPLORAR
    for _ in range(10):
        tick(auto, [a, b], mapa, ctx)
        if ctx.reproducciones:
            break
    assert ctx.reproducciones


def test_no_busca_a_quien_no_quiere_pareja_y_explora_conservando_la_intencion():
    mapa, ctx, auto = escenario()
    a = herbivoro(ctx, (5, 5), energia=70.0)
    herbivoro(ctx, (7, 5), energia=40.0)  # tiene hambre: no quiere pareja
    estado, objetivo = decidir(auto, a, mapa, ctx)
    assert estado == Estado.EXPLORAR and objetivo is None
    assert a.intencion == INTENCION_PAREJA


def test_otra_especie_no_es_pareja():
    mapa, ctx, auto = escenario()
    a = herbivoro(ctx, (5, 5), energia=70.0, especie="conejo")
    herbivoro(ctx, (6, 5), energia=70.0, especie="liebre")
    assert auto.percibir(a, mapa, ctx).parejas == []


def test_con_energia_para_pareja_ignora_la_comida():
    mapa, ctx, auto = escenario()
    mapa.poner_pasto(6, 6)
    a = herbivoro(ctx, (5, 5), energia=75.0)
    herbivoro(ctx, (8, 5), energia=75.0)
    estado, objetivo = decidir(auto, a, mapa, ctx)
    assert estado == Estado.BUSCAR_PAREJA and objetivo.tipo == TipoObjetivo.PAREJA


def test_histeresis_entre_50_y_70_sigue_buscando_pareja_y_bajo_50_vuelve_a_comer():
    mapa, ctx, auto = escenario()
    mapa.poner_pasto(5, 6)
    a = herbivoro(ctx, (5, 5), energia=70.0)
    herbivoro(ctx, (8, 5), energia=60.0, especie=None).intencion = INTENCION_PAREJA
    assert decidir(auto, a, mapa, ctx)[0] == Estado.BUSCAR_PAREJA
    a.energia = 55.0  # bajo 70 pero >= 50: sigue
    assert decidir(auto, a, mapa, ctx)[0] == Estado.BUSCAR_PAREJA
    a.energia = 49.9  # bajo 50: vuelve a buscar comida
    estado, objetivo = decidir(auto, a, mapa, ctx)
    assert estado == Estado.BUSCAR_ALIMENTO and objetivo.tipo == TipoObjetivo.PLANTA
    assert a.intencion == INTENCION_ALIMENTO
    a.energia = 69.0  # y no vuelve a pareja hasta llegar a 70
    assert decidir(auto, a, mapa, ctx)[0] == Estado.BUSCAR_ALIMENTO


def test_si_la_reproduccion_falla_se_queda_donde_esta():
    mapa, ctx, auto = escenario(reproduccion_ok=False)
    a = herbivoro(ctx, (5, 5), energia=70.0)
    b = herbivoro(ctx, (6, 5), energia=70.0)
    jugar(auto, a, mapa, ctx)
    assert ctx.reproducciones == [(a, b)]
    assert a.pos == (5, 5) and not b.turno_hecho


def test_elegir_pareja_prefiere_la_mas_cercana_y_desempata_por_id():
    mapa, ctx, auto = escenario()
    a = herbivoro(ctx, (10, 10), energia=70.0)
    lejos = herbivoro(ctx, (13, 10), energia=70.0)
    cerca2 = herbivoro(ctx, (10, 8), energia=70.0)
    cerca1 = herbivoro(ctx, (8, 10), energia=70.0)
    p = auto.percibir(a, mapa, ctx)
    elegida = auto.elegir_pareja(a, p).criatura
    assert elegida is min((cerca1, cerca2), key=lambda o: o.id)
    assert lejos not in (elegida,)


# --- caza ------------------------------------------------------------------------------------------


def test_el_carnivoro_captura_en_el_mismo_tick_si_le_alcanza_el_paso():
    mapa, ctx, auto = escenario()
    c = carnivoro(ctx, (5, 5), energia=30.0, v=2.0)
    presa = herbivoro(ctx, (7, 5))
    jugar(auto, c, mapa, ctx)
    assert not presa.viva and presa.causa_muerte == CausaMuerte.DEPREDACION
    assert c.pos == (7, 5) and c in ctx.criaturas_en((7, 5))
    gasto_corriendo = (0.30 + 0.05 * 6 + 0.15 * 2.0**2) * 2.5**-0.25  # V = 2, R = 6, S = 2.5
    assert c.energia == pytest.approx(30 + 32 - gasto_corriendo)  # comio 32, pago por correr


def test_con_velocidad_decimal_captura_cuando_acumula_los_pasos():
    mapa, ctx, auto = escenario()
    c = carnivoro(ctx, (5, 5), v=1.6)
    presa = herbivoro(ctx, (7, 5))  # distancia 2
    jugar(auto, c, mapa, ctx)  # 1 paso: se acerca
    assert presa.viva and distancia(c.pos, presa.pos) == 1
    jugar(auto, c, mapa, ctx)  # 2 pasos: captura
    assert not presa.viva


def test_un_depredador_mas_rapido_casi_siempre_atrapa():
    mapa, ctx, auto = escenario(ancho=60, alto=60)
    c = carnivoro(ctx, (30, 30), v=2.0)
    presa = herbivoro(ctx, (34, 30), v=1.0)
    for _ in range(10):
        tick(auto, [c, presa], mapa, ctx)
        if not presa.viva:
            break
    assert not presa.viva and presa.causa_muerte == CausaMuerte.DEPREDACION


def test_una_presa_mas_rapida_que_ve_al_depredador_escapa():
    mapa, ctx, auto = escenario(ancho=100, alto=100)
    c = carnivoro(ctx, (46, 50), v=1.0)
    presa = herbivoro(ctx, (50, 50), v=2.0)
    for _ in range(20):
        tick(auto, [c, presa], mapa, ctx)
        assert presa.viva


def test_el_depredador_pierde_a_la_presa_fuera_de_su_radio_de_vision():
    mapa, ctx, auto = escenario()
    c = carnivoro(ctx, (5, 5), r=2.0)
    herbivoro(ctx, (8, 5))  # distancia 3 > R = 2
    assert decidir(auto, c, mapa, ctx)[0] == Estado.EXPLORAR
    c2 = carnivoro(ctx, (15, 15), r=3.0)
    herbivoro(ctx, (18, 15))
    assert decidir(auto, c2, mapa, ctx)[0] == Estado.BUSCAR_ALIMENTO


def test_no_caza_a_los_de_su_especie_ni_a_los_demasiado_grandes():
    mapa, ctx, auto = escenario()
    c = carnivoro(ctx, (5, 5), especie="lobo")
    carnivoro(ctx, (6, 5), especie="lobo", s=1.0)  # misma especie
    herbivoro(ctx, (5, 6), especie="alce", s=2.4)  # 2.5 < 1.2 * 2.4
    assert auto.percibir(c, mapa, ctx).presas == []


def test_un_obstaculo_en_el_camino_impide_la_captura():
    mapa, ctx, auto = escenario()
    for y in (4, 5, 6):
        mapa.poner_agua(6, y)
    c = carnivoro(ctx, (5, 5), v=3.0)
    presa = herbivoro(ctx, (8, 5))
    jugar(auto, c, mapa, ctx)
    assert presa.viva and c.pos == (5, 5)


def test_una_presa_comida_antes_de_su_turno_no_actua_ni_paga():
    mapa, ctx, auto = escenario()
    presa = herbivoro(ctx, (6, 5), energia=50.0)
    presa.morir(CausaMuerte.DEPREDACION)
    presa.iniciar_tick()
    auto.turno(presa, mapa, ctx, 22.0)
    assert presa.energia == 50.0 and presa.edad == 0 and presa.pos == (6, 5)


# --- explorar -----------------------------------------------------------------------------------------


def test_explorar_se_mueve_hasta_pasos_tick_casillas():
    mapa, ctx, auto = escenario(ancho=100, alto=100)
    h = herbivoro(ctx, (50, 50), v=2.0)
    jugar(auto, h, mapa, ctx)
    assert h.estado == Estado.EXPLORAR and distancia(h.pos, (50, 50)) == 2


def test_explorar_con_inercia_total_sigue_en_linea_recta():
    cfg = CFG.con(INERCIA_EXPLORAR=1.0)
    mapa, ctx, auto = escenario(ancho=100, alto=100, cfg=cfg)
    h = herbivoro(ctx, (10, 50), v=2.0, cfg=cfg)
    h.direccion = (1, 0)
    for _ in range(2):
        jugar(auto, h, mapa, ctx)
    assert h.pos == (14, 50) and h.direccion == (1, 0)


def test_explorar_es_repetible_con_la_misma_semilla():
    def recorrido(semilla):
        mapa, ctx, auto = escenario(ancho=50, alto=50, semilla=semilla)
        h = herbivoro(ctx, (25, 25))
        trazo = []
        for _ in range(40):
            jugar(auto, h, mapa, ctx)
            trazo.append(h.pos)
        return trazo

    assert recorrido(7) == recorrido(7)
    assert recorrido(7) != recorrido(8)


def test_encerrada_no_se_mueve_ni_falla_y_paga_el_gasto_quieto():
    mapa = MapaFalso(3, 3)
    for x in range(3):
        for y in range(3):
            if (x, y) != (1, 1):
                mapa.poner_agua(x, y)
    mapa, ctx, auto = escenario(mapa=mapa)
    h = herbivoro(ctx, (1, 1), energia=50.0)
    jugar(auto, h, mapa, ctx)
    assert h.pos == (1, 1) and h.direccion == (0, 0)
    assert h.energia == pytest.approx(49.5)


def test_respeta_el_maximo_de_criaturas_por_casilla():
    mapa = MapaFalso(3, 1)
    mapa, ctx, auto = escenario(mapa=mapa)
    a = herbivoro(ctx, (0, 0))
    herbivoro(ctx, (1, 0))
    herbivoro(ctx, (2, 0))
    jugar(auto, a, mapa, ctx)
    assert a.pos == (0, 0)  # el unico vecino esta ocupado


# --- metabolismo y vejez dentro del turno ---------------------------------------------------------------


def test_el_metabolismo_se_cobra_al_final_con_el_costo_de_haberse_movido():
    mapa, ctx, auto = escenario(ancho=100, alto=100)
    h = herbivoro(ctx, (50, 50), energia=50.0)
    jugar(auto, h, mapa, ctx)  # explora: se mueve
    assert h.se_movio and h.energia == pytest.approx(50 - 0.65)


def test_cada_turno_envejece_un_tick_y_muere_de_vejez():
    mapa, ctx, auto = escenario()
    h = herbivoro(ctx, (5, 5), energia=90.0, vida_max=2)
    jugar(auto, h, mapa, ctx)
    assert h.viva and h.edad == 1
    jugar(auto, h, mapa, ctx)
    assert not h.viva and h.causa_muerte == CausaMuerte.VEJEZ


def test_sin_energia_muere_de_hambre_al_final_del_turno():
    mapa, ctx, auto = escenario()
    h = herbivoro(ctx, (5, 5), energia=0.3)
    jugar(auto, h, mapa, ctx)
    assert not h.viva and h.causa_muerte == CausaMuerte.HAMBRE


def test_comer_a_tiempo_salva_de_morir_de_hambre_en_el_mismo_turno():
    mapa, ctx, auto = escenario()
    mapa.poner_pasto(6, 5)
    h = herbivoro(ctx, (5, 5), energia=0.3)
    jugar(auto, h, mapa, ctx)
    assert h.viva and h.energia == pytest.approx(0.3 + 15 - 0.65)


def test_la_temperatura_afecta_al_costo_del_turno():
    def energia_tras_un_turno(temperatura):
        mapa, ctx, auto = escenario()
        h = herbivoro(ctx, (5, 5), energia=50.0)
        jugar(auto, h, mapa, ctx, temperatura)
        return h.energia

    assert energia_tras_un_turno(40.0) < energia_tras_un_turno(22.0)
    assert energia_tras_un_turno(-10.0) < energia_tras_un_turno(40.0)
