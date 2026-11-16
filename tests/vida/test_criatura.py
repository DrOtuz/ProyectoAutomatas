import json
import random

import pytest
from valores_doc import CFG_DOC as CFG

from simulador.vida.criatura import Criatura, factor_temperatura
from simulador.vida.estadisticas import Estadisticas
from simulador.vida.tipos import (
    INTENCION_ALIMENTO,
    INTENCION_PAREJA,
    CausaMuerte,
    Dieta,
    Estado,
)

_ids = iter(range(1, 10_000))


def crear(dieta=Dieta.HERBIVORO, s=1.0, v=1.0, r=4.0, pos=(5, 5), energia=70.0,
          vida_max=100_000, especie=None, cfg=CFG):
    return Criatura(
        id=next(_ids),
        especie=especie or dieta.value,
        dieta=dieta,
        stats=Estadisticas(s, v, r),
        pos=pos,
        cfg=cfg,
        vida_max=vida_max,
        energia=energia,
    )


def herbivoro(**kw):
    return crear(Dieta.HERBIVORO, 1.0, 1.0, 4.0, **kw)


def omnivoro(**kw):
    return crear(Dieta.OMNIVORO, 1.5, 1.2, 5.0, **kw)


def carnivoro(**kw):
    return crear(Dieta.CARNIVORO, 2.5, 1.6, 6.0, **kw)


# --- construccion --------------------------------------------------------------------


def test_nace_con_la_energia_de_cria_por_defecto_y_en_buen_estado():
    c = Criatura(1, "x", Dieta.HERBIVORO, Estadisticas(1, 1, 4), (0, 0), CFG, 1000)
    assert c.energia == 30
    assert c.viva and c.causa_muerte is None
    assert c.estado == Estado.EXPLORAR
    assert c.intencion == INTENCION_ALIMENTO
    assert c.edad == 0 and c.se_movio is False


@pytest.mark.parametrize("energia", [0, -5, 100.1])
def test_rechaza_energia_inicial_invalida(energia):
    with pytest.raises(ValueError):
        herbivoro(energia=energia)


def test_rechaza_vida_maxima_invalida():
    with pytest.raises(ValueError):
        herbivoro(vida_max=0)


# --- metabolismo (tabla del documento) -----------------------------------------------


def test_factor_temperatura_coincide_con_el_documento():
    assert factor_temperatura(22, CFG) == 1.0
    assert factor_temperatura(-10, CFG) == pytest.approx(2.5, abs=0.05)
    assert factor_temperatura(0, CFG) == pytest.approx(1.7, abs=0.05)
    assert factor_temperatura(40, CFG) == pytest.approx(1.5, abs=0.02)


def test_factor_temperatura_es_una_u_simetrica_alrededor_del_optimo():
    assert factor_temperatura(12, CFG) == pytest.approx(factor_temperatura(32, CFG))
    assert factor_temperatura(22, CFG) < factor_temperatura(25, CFG) < factor_temperatura(30, CFG)


def test_gasto_del_herbivoro_de_referencia():
    c = herbivoro()
    assert c.gasto(22) == pytest.approx(0.50)  # quieto: 0.30 + 0.05*4
    c.se_movio = True
    assert c.gasto(22) == pytest.approx(0.65)  # moviendose: + 0.15
    assert c.gasto(40) == pytest.approx(0.97, abs=0.01)


@pytest.mark.parametrize(
    "criatura, quieta, moviendose",
    [
        (herbivoro(), 0.50, 0.65),
        (omnivoro(), 0.50, 0.69),
        (carnivoro(), 0.48, 0.78),
    ],
)
def test_gastos_de_las_tres_dietas_coinciden_con_el_documento(criatura, quieta, moviendose):
    assert criatura.gasto(22) == pytest.approx(quieta, abs=0.005)
    criatura.se_movio = True
    assert criatura.gasto(22) == pytest.approx(moviendose, abs=0.005)


def test_efecto_de_duplicar_un_rasgo_segun_el_documento():
    def gasto_moviendose(**kw):
        c = crear(**kw)
        c.se_movio = True
        return c.gasto(22)

    base = gasto_moviendose()
    assert gasto_moviendose(v=2.0) == pytest.approx(1.10)  # +69 %
    assert gasto_moviendose(v=2.0) / base == pytest.approx(1.69, abs=0.01)
    assert gasto_moviendose(r=8.0) == pytest.approx(0.85)  # +31 %
    assert gasto_moviendose(s=2.0) == pytest.approx(0.55, abs=0.01)  # -16 %
    assert gasto_moviendose(s=2.0) < base


def test_un_animal_grande_gasta_menos_como_porcentaje_de_sus_reservas():
    chico, grande = crear(s=1.0), crear(s=4.0)
    assert grande.gasto(22) < chico.gasto(22)
    # en absoluto gasta mas: S * gasto%
    assert grande.gasto(22) * 4.0 > chico.gasto(22) * 1.0


def test_70_de_energia_aguantan_unos_108_ticks_moviendose_sin_comer():
    c = herbivoro(energia=70.0)
    ticks = 0
    while c.viva:
        c.se_movio = True
        c.cobrar_metabolismo(22)
        ticks += 1
    assert ticks == 108
    assert c.causa_muerte == CausaMuerte.HAMBRE and c.energia == 0


def test_cobrar_metabolismo_resta_el_gasto_y_lo_devuelve():
    c = herbivoro(energia=50.0)
    g = c.cobrar_metabolismo(22)
    assert g == pytest.approx(0.50)
    assert c.energia == pytest.approx(49.5)
    c.se_movio = True
    assert c.cobrar_metabolismo(22) == pytest.approx(0.65)


def test_una_criatura_muerta_no_paga_ni_envejece():
    c = herbivoro(energia=50.0)
    c.morir(CausaMuerte.FUEGO)
    assert c.cobrar_metabolismo(22) == 0.0 and c.energia == 50.0
    c.envejecer()
    assert c.edad == 0


# --- pasos por tick -------------------------------------------------------------------


def pasos_de(velocidad, n):
    c = crear(v=velocidad)
    resultado = []
    for _ in range(n):
        c.iniciar_tick()
        resultado.append(c.pasos_tick)
    return resultado


def test_velocidad_decimal_se_acumula():
    assert pasos_de(1.6, 5) == [1, 2, 1, 2, 2]
    assert sum(pasos_de(1.6, 10)) == 16
    assert pasos_de(1.0, 4) == [1, 1, 1, 1]
    assert pasos_de(2.0, 3) == [2, 2, 2]
    assert pasos_de(0.5, 4) == [0, 1, 0, 1]


def test_el_total_de_pasos_es_el_esperado_a_largo_plazo():
    for v in (0.3, 1.2, 1.6, 2.7, 3.33):
        assert sum(pasos_de(v, 1000)) == pytest.approx(v * 1000, abs=1)


def test_iniciar_tick_reinicia_las_marcas():
    c = herbivoro()
    c.se_movio = True
    c.turno_hecho = True
    c.iniciar_tick()
    assert c.se_movio is False and c.turno_hecho is False


# --- movimiento -----------------------------------------------------------------------


def test_mover_a_actualiza_posicion_direccion_y_marca_movimiento():
    c = herbivoro(pos=(5, 5))
    c.mover_a((6, 4))
    assert c.pos == (6, 4) and c.direccion == (1, -1) and c.se_movio
    c.mover_a((6, 7))  # varios pasos en un tick: la direccion es el signo
    assert c.pos == (6, 7) and c.direccion == (0, 1)


def test_mover_a_la_misma_casilla_no_cuenta_como_movimiento():
    c = herbivoro(pos=(5, 5))
    c.mover_a((5, 5))
    assert c.se_movio is False and c.direccion == (0, 0)


# --- alimentacion ---------------------------------------------------------------------


def test_un_pasto_de_30u_da_15_y_un_arbol_de_60u_da_30_al_herbivoro():
    c = herbivoro(energia=30.0)
    assert c.comer_planta(30.0) == pytest.approx(15.0)
    assert c.energia == pytest.approx(45.0)
    assert c.comer_planta(60.0) == pytest.approx(30.0)
    assert c.energia == pytest.approx(75.0)


def test_ganancias_tipicas_del_documento():
    omni, carn, presa = omnivoro(energia=30.0), carnivoro(energia=30.0), herbivoro()
    assert omni.ganancia_planta(30.0) == pytest.approx(7.0)  # 0.35 * 30 / 1.5
    assert omni.ganancia_presa(presa) == pytest.approx(40.0)  # 100*0.60*1 / 1.5
    assert carn.ganancia_presa(presa) == pytest.approx(32.0)  # 100*0.80*1 / 2.5


def test_las_funciones_de_ganancia_no_modifican_nada():
    c, presa = carnivoro(energia=30.0), herbivoro()
    c.ganancia_presa(presa)
    c.ganancia_planta(10.0)
    assert c.energia == 30.0 and presa.viva


def test_la_energia_nunca_pasa_de_100_y_lo_que_sobra_se_pierde():
    c = herbivoro(energia=95.0)
    assert c.comer_planta(30.0) == pytest.approx(5.0)  # solo gano 5
    assert c.energia == 100.0
    assert c.comer_planta(30.0) == 0.0 and c.energia == 100.0


def test_ganar_mas_de_lo_que_cabe_con_una_presa_tambien_se_topa():
    c = omnivoro(energia=80.0)
    c.comer_presa(herbivoro())  # daria 40
    assert c.energia == 100.0


def test_comer_una_presa_la_mata_por_depredacion():
    carn, presa = carnivoro(energia=30.0), herbivoro()
    ganado = carn.comer_presa(presa)
    assert ganado == pytest.approx(32.0) and carn.energia == pytest.approx(62.0)
    assert not presa.viva and presa.causa_muerte == CausaMuerte.DEPREDACION
    assert presa.estado == Estado.MUERTA


def test_un_depredador_gana_mas_de_una_presa_grande():
    carn = crear(Dieta.CARNIVORO, s=4.0, v=1.0, r=4.0, energia=10.0)
    chica = crear(Dieta.HERBIVORO, s=1.0, especie="a")
    grande = crear(Dieta.HERBIVORO, s=3.0, especie="b")
    assert carn.ganancia_presa(grande) == pytest.approx(3 * carn.ganancia_presa(chica))


def test_no_puede_comer_lo_que_su_dieta_no_permite():
    with pytest.raises(ValueError):
        carnivoro().comer_planta(30.0)
    with pytest.raises(ValueError):
        herbivoro().comer_presa(herbivoro(especie="otra"))
    with pytest.raises(ValueError):
        herbivoro().comer_planta(-1.0)


def test_eficiencias_por_dieta():
    assert herbivoro().eficiencia_planta() == 0.50 and herbivoro().eficiencia_carne() == 0.0
    assert carnivoro().eficiencia_carne() == 0.80 and carnivoro().eficiencia_planta() == 0.0
    assert omnivoro().eficiencia_planta() == 0.35 and omnivoro().eficiencia_carne() == 0.60


# --- depredacion: quien es presa y quien amenaza ----------------------------------------


def test_presa_elegible_exige_otra_especie_y_ratio_de_tamano():
    carn = crear(Dieta.CARNIVORO, s=2.5, especie="lobo")
    assert carn.puede_cazar(crear(Dieta.HERBIVORO, s=2.0, especie="cabra"))  # 2.5 >= 2.4
    assert not carn.puede_cazar(crear(Dieta.HERBIVORO, s=2.2, especie="cabra"))  # 2.5 < 2.64
    assert not carn.puede_cazar(crear(Dieta.CARNIVORO, s=1.0, especie="lobo"))  # misma especie
    assert carn.puede_cazar(crear(Dieta.CARNIVORO, s=1.0, especie="zorro"))  # otra especie


def test_el_ratio_en_el_limite_exacto_cuenta():
    dep = crear(Dieta.CARNIVORO, s=1.2, especie="a")
    assert dep.puede_cazar(crear(Dieta.HERBIVORO, s=1.0, especie="b"))


def test_un_herbivoro_grande_no_es_amenaza():
    grande = crear(Dieta.HERBIVORO, s=5.0, especie="bufalo")
    chico = crear(Dieta.HERBIVORO, s=1.0, especie="conejo")
    assert not grande.es_amenaza_para(chico)
    assert not grande.puede_cazar(chico)


def test_amenaza_es_el_mismo_criterio_visto_desde_la_presa():
    carn, presa = carnivoro(especie="lobo"), herbivoro(especie="cabra")
    assert carn.es_amenaza_para(presa)
    assert not presa.es_amenaza_para(carn)
    omni = omnivoro(especie="oso")
    assert omni.es_amenaza_para(presa)  # 1.5 >= 1.2


def test_no_se_caza_a_los_muertos_ni_cazan_los_muertos():
    carn, presa = carnivoro(especie="lobo"), herbivoro(especie="cabra")
    presa.morir(CausaMuerte.HAMBRE)
    assert not carn.puede_cazar(presa)
    carn2, presa2 = carnivoro(especie="lobo"), herbivoro(especie="cabra")
    carn2.morir(CausaMuerte.HAMBRE)
    assert not carn2.puede_cazar(presa2)


# --- intencion e histeresis ------------------------------------------------------------


def test_umbrales_de_reproduccion_y_salida():
    c = herbivoro(energia=69.9)
    assert not c.en_umbral_reproduccion()
    c.energia = 70.0
    assert c.en_umbral_reproduccion()
    c.energia = 50.0
    assert not c.en_umbral_salida()
    c.energia = 49.9
    assert c.en_umbral_salida()


def test_histeresis_de_la_intencion():
    c = herbivoro(energia=69.0)
    assert c.actualizar_intencion() == INTENCION_ALIMENTO
    c.energia = 70.0
    assert c.actualizar_intencion() == INTENCION_PAREJA
    for e in (65.0, 55.0, 50.0):  # entre 50 y 70 sigue buscando pareja
        c.energia = e
        assert c.actualizar_intencion() == INTENCION_PAREJA
    c.energia = 49.9
    assert c.actualizar_intencion() == INTENCION_ALIMENTO
    for e in (55.0, 69.9):  # y no vuelve a pareja hasta llegar a 70
        c.energia = e
        assert c.actualizar_intencion() == INTENCION_ALIMENTO
    c.energia = 70.0
    assert c.actualizar_intencion() == INTENCION_PAREJA


def test_quiere_pareja_es_una_consulta_pura_con_la_misma_histeresis():
    c = herbivoro(energia=69.0)
    assert not c.quiere_pareja()
    c.energia = 70.0
    assert c.quiere_pareja() and c.intencion == INTENCION_ALIMENTO  # no la cambia
    c.intencion = INTENCION_PAREJA
    c.energia = 55.0
    assert c.quiere_pareja()
    c.energia = 49.0
    assert not c.quiere_pareja()


def test_los_umbrales_siguen_a_e_max():
    cfg = CFG.con(E_MAX=200.0)
    c = herbivoro(energia=139.0, cfg=cfg)
    assert not c.en_umbral_reproduccion()
    c.energia = 140.0
    assert c.en_umbral_reproduccion()


# --- reproduccion ---------------------------------------------------------------------


def test_pagar_reproduccion_resta_25():
    c = herbivoro(energia=70.0)
    c.pagar_reproduccion()
    assert c.energia == 45.0


def test_un_padre_lleno_puede_reproducirse_varias_veces_hasta_bajar_de_50():
    c = herbivoro(energia=100.0)
    c.actualizar_intencion()
    veces = 0
    while c.intencion == INTENCION_PAREJA and c.puede_pagar_reproduccion():
        c.pagar_reproduccion()
        c.actualizar_intencion()
        veces += 1
    assert veces == 3  # 100 -> 75 -> 50 -> 25
    assert c.energia == 25.0 and c.intencion == INTENCION_ALIMENTO


def test_no_se_paga_una_reproduccion_que_deja_a_la_criatura_sin_energia():
    c = herbivoro(energia=25.0)
    assert not c.puede_pagar_reproduccion()
    with pytest.raises(ValueError):
        c.pagar_reproduccion()
    assert c.energia == 25.0  # nada cobrado


def test_un_padre_con_70_queda_en_45_y_sale_de_pareja():
    c = herbivoro(energia=70.0)
    c.actualizar_intencion()
    c.pagar_reproduccion()
    assert c.actualizar_intencion() == INTENCION_ALIMENTO


# --- vejez ----------------------------------------------------------------------------


def test_con_vejez_muere_al_llegar_a_vida_max():
    c = herbivoro(vida_max=5, energia=100.0)
    for _ in range(4):
        c.envejecer()
    assert c.viva and c.edad == 4
    c.envejecer()
    assert not c.viva and c.causa_muerte == CausaMuerte.VEJEZ


def test_sin_vejez_la_edad_no_mata():
    cfg = CFG.con(VEJEZ_ACTIVA=False)
    c = herbivoro(vida_max=5, cfg=cfg)
    for _ in range(50):
        c.envejecer()
    assert c.viva and c.edad == 50


@pytest.mark.parametrize("s, esperado", [(1.0, 1500), (16.0, 3000), (0.0625, 750)])
def test_vida_max_dentro_de_mas_menos_15_por_ciento(s, esperado):
    rng = random.Random(1)
    stats = Estadisticas(s, 1.0, 4.0)
    vidas = [Criatura.calcular_vida_max(stats, CFG, rng) for _ in range(2000)]
    assert min(vidas) >= esperado * 0.85 - 1 and max(vidas) <= esperado * 1.15 + 1
    assert sum(vidas) / len(vidas) == pytest.approx(esperado, rel=0.02)
    assert len(set(vidas)) > 100  # varia entre individuos


def test_un_animal_grande_vive_mas():
    rng = random.Random(2)
    chico = Criatura.calcular_vida_max(Estadisticas(1.0, 1, 4), CFG.con(VARIACION_VIDA=0.0), rng)
    grande = Criatura.calcular_vida_max(Estadisticas(16.0, 1, 4), CFG.con(VARIACION_VIDA=0.0), rng)
    assert grande == 2 * chico


def test_calcular_vida_max_siempre_consume_azar_aunque_la_vejez_este_apagada():
    stats = Estadisticas(1.0, 1.0, 4.0)
    r1, r2 = random.Random(5), random.Random(5)
    Criatura.calcular_vida_max(stats, CFG.con(VEJEZ_ACTIVA=False), r1)
    Criatura.calcular_vida_max(stats, CFG, r2)
    assert r1.random() == r2.random()


def test_nueva_sortea_la_vida_y_nace_con_energia_de_cria():
    rng = random.Random(3)
    c = Criatura.nueva(7, "x", Dieta.HERBIVORO, Estadisticas(1, 1, 4), (1, 1), CFG, rng)
    assert c.energia == 30 and 1275 <= c.vida_max <= 1725
    c2 = Criatura.nueva(8, "x", Dieta.HERBIVORO, Estadisticas(1, 1, 4), (1, 1), CFG,
                        random.Random(3))
    assert c2.vida_max == c.vida_max  # misma semilla, misma vida


# --- muerte ---------------------------------------------------------------------------


def test_morir_marca_el_estado_y_conserva_la_primera_causa():
    c = herbivoro()
    c.morir(CausaMuerte.FUEGO)
    c.morir(CausaMuerte.HAMBRE)
    assert not c.viva and c.estado == Estado.MUERTA
    assert c.causa_muerte == CausaMuerte.FUEGO


def test_sin_energia_muere_de_hambre():
    c = herbivoro(energia=0.3)
    c.cobrar_metabolismo(22)
    assert not c.viva and c.causa_muerte == CausaMuerte.HAMBRE and c.energia == 0.0


def test_el_frio_extremo_mata_mas_rapido():
    def ticks_hasta_morir(temp):
        c, n = herbivoro(energia=50.0), 0
        while c.viva:
            c.cobrar_metabolismo(temp)
            n += 1
        return n

    assert ticks_hasta_morir(-10) < ticks_hasta_morir(40) < ticks_hasta_morir(22)


# --- guardado -------------------------------------------------------------------------


def test_a_dict_desde_dict_son_inversos_y_serializan_como_json():
    c = carnivoro(pos=(7, 9), energia=61.5)
    c.estado = Estado.BUSCAR_PAREJA
    c.intencion = INTENCION_PAREJA
    c.iniciar_tick()
    c.mover_a((8, 9))
    c.edad = 321
    copia = Criatura.desde_dict(json.loads(json.dumps(c.a_dict())), CFG)
    assert copia.a_dict() == c.a_dict()
    assert copia.pos == (8, 9) and isinstance(copia.pos, tuple)
    assert isinstance(copia.direccion, tuple)


def test_se_guarda_y_carga_una_criatura_muerta_sin_energia():
    c = herbivoro(energia=0.3)
    c.cobrar_metabolismo(22)
    copia = Criatura.desde_dict(json.loads(json.dumps(c.a_dict())), CFG)
    assert not copia.viva and copia.energia == 0.0
    assert copia.causa_muerte == CausaMuerte.HAMBRE and copia.estado == Estado.MUERTA


def test_al_morir_avisa_una_sola_vez_y_ya_con_la_causa_puesta():
    avisos = []
    c = herbivoro()
    c.al_morir = lambda x: avisos.append((x.id, x.viva, x.causa_muerte))
    c.morir(CausaMuerte.FUEGO)
    c.morir(CausaMuerte.HAMBRE)  # ya muerta: no vuelve a avisar
    assert avisos == [(c.id, False, CausaMuerte.FUEGO)]


def test_al_morir_tambien_avisa_si_muere_de_hambre_o_de_vejez_o_comida():
    avisos = []
    hambriento = herbivoro(energia=0.3)
    viejo = herbivoro(vida_max=1)
    presa = herbivoro()
    for c in (hambriento, viejo, presa):
        c.al_morir = lambda x: avisos.append(x.causa_muerte)
    hambriento.cobrar_metabolismo(22)
    viejo.envejecer()
    carnivoro(especie="lobo").comer_presa(presa)
    assert avisos == [CausaMuerte.HAMBRE, CausaMuerte.VEJEZ, CausaMuerte.DEPREDACION]
