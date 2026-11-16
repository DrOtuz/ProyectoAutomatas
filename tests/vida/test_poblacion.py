import copy
import json
import random
import time

import pytest
from valores_doc import CFG_DOC as CFG

from simulador.vida.adaptadores.mapa_falso import MapaFalso
from simulador.vida.automata_criatura import ContextoVida
from simulador.vida.estadisticas import Estadisticas
from simulador.vida.poblacion import (
    EXTINCION,
    MUERTE,
    NACIMIENTO,
    Poblacion,
)
from simulador.vida.tipos import CausaMuerte, Dieta, EstadoEspecie

H, OM, C = Dieta.HERBIVORO, Dieta.OMNIVORO, Dieta.CARNIVORO


# --- ayudas ------------------------------------------------------------------------------------


def nueva(cfg=CFG, semilla=1):
    return Poblacion(cfg, random.Random(semilla))


def mapa_con(ancho, alto, tipo="pasto"):
    m = MapaFalso(ancho, alto)
    poner = m.poner_arbol if tipo == "arbol" else m.poner_pasto
    for y in range(alto):
        for x in range(ancho):
            poner(x, y)
    return m


def paso(pob, mapa, temperatura=22.0):
    mapa.regenerar()
    pob.actualizar(mapa, temperatura)


def simular(pob, mapa, ticks, revisar=True):
    for _ in range(ticks):
        paso(pob, mapa)
        if revisar:
            assert pob.verificar_consistencia() == []
            assert all(c.viva for c in pob._criaturas.values())


def registro(pob):
    eventos = []
    pob.suscribir(eventos.append)
    return eventos


def escenario3(semilla=1, cfg=CFG):
    pob, mapa = nueva(cfg, semilla), mapa_con(40, 40)
    pob.crear_especie("conejo", H, 60, mapa)
    pob.crear_especie("zorro", OM, 20, mapa)
    pob.crear_especie("lobo", C, 10, mapa)
    return pob, mapa


def firma(pob):
    return (
        pob.tick,
        {n: d["poblacion"] for n, d in pob.snapshot().items()},
        sorted((c.id, c.pos, round(c.energia, 9)) for c in pob.criaturas_vivas()),
    )


# --- contrato -----------------------------------------------------------------------------------


def test_poblacion_cumple_el_protocolo_del_contexto():
    assert isinstance(nueva(), ContextoVida)


# --- crear especies -----------------------------------------------------------------------------------


def test_crear_especie_coloca_las_criaturas_en_casillas_libres_y_distintas():
    mapa = MapaFalso(20, 20)
    mapa.poner_agua(0, 0)
    mapa.poner_fuego(1, 1)
    pob = nueva()
    especie = pob.crear_especie("conejo", H, 30, mapa)
    assert especie.contar() == 30 and pob.total() == 30
    vivas = pob.criaturas_vivas()
    posiciones = [c.pos for c in vivas]
    assert len(set(posiciones)) == 30
    assert all(mapa.es_transitable(*p) and not mapa.hay_fuego(*p) for p in posiciones)
    assert len({c.id for c in vivas}) == 30
    assert all(c.energia == CFG.ENERGIA_CRIA and c.dieta == H for c in vivas)
    assert pob.verificar_consistencia() == []


def test_las_criaturas_iniciales_varian_alrededor_de_la_plantilla():
    mapa = MapaFalso(30, 30)
    pob = nueva()
    pob.crear_especie("conejo", H, 100, mapa)
    tamanos = [c.stats.tamano for c in pob.criaturas_vivas()]
    assert all(0.9 <= t <= 1.1 for t in tamanos) and len(set(tamanos)) > 90
    pob.crear_especie("raro", H, 50, mapa, plantilla=Estadisticas(3.0, 2.0, 7.0))
    raros = [c.stats for c in pob.criaturas_vivas() if c.especie == "raro"]
    assert all(2.7 <= s.tamano <= 3.3 and 1.8 <= s.velocidad <= 2.2 for s in raros)


def test_respeta_el_limite_de_criaturas():
    cfg = CFG.con(MAX_CRIATURAS=50)
    mapa = MapaFalso(30, 30)
    pob = nueva(cfg)
    assert pob.crear_especie("a", H, 200, mapa).contar() == 50
    assert not pob.hay_cupo()
    segunda = pob.crear_especie("b", C, 10, mapa)  # sin cupo: nace extinta
    assert segunda.contar() == 0 and segunda.estado == EstadoEspecie.EXTINTA
    assert pob.total() == 50


def test_un_mapa_casi_lleno_solo_admite_las_casillas_libres():
    mapa = MapaFalso(3, 3)
    mapa.poner_agua(0, 0)
    pob = nueva()
    assert pob.crear_especie("a", H, 20, mapa).contar() == 8
    assert len({c.pos for c in pob.criaturas_vivas()}) == 8


def test_con_mas_de_una_criatura_por_casilla():
    cfg = CFG.con(MAX_POR_CASILLA=2)
    pob = nueva(cfg)
    assert pob.crear_especie("a", H, 5, MapaFalso(1, 1)).contar() == 2


def test_los_nombres_no_se_repiten_salvo_el_de_una_especie_eliminada():
    mapa = MapaFalso(20, 20)
    pob = nueva()
    pob.crear_especie("a", H, 3, mapa)
    with pytest.raises(ValueError):
        pob.crear_especie("a", C, 3, mapa)
    pob.eliminar_especie("a")
    again = pob.crear_especie("a", C, 4, mapa)
    assert again.dieta == C and again.contar() == 4 and pob.total() == 4


def test_argumentos_invalidos():
    mapa = MapaFalso(10, 10)
    pob = nueva()
    with pytest.raises(TypeError):
        pob.crear_especie("a", "herbivoro", 3, mapa)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        pob.crear_especie("a", H, -1, mapa)
    with pytest.raises(ValueError):
        pob.crear_especie("", H, 1, mapa)
    with pytest.raises(KeyError):
        pob.agregar_individuos("no existe", 1, mapa)


def test_agregar_individuos_a_posiciones_dadas_solo_usa_las_libres():
    mapa = MapaFalso(10, 10)
    mapa.poner_agua(2, 2)
    pob = nueva()
    pob.crear_especie("a", H, 0, mapa)
    n = pob.agregar_individuos("a", 5, mapa, posiciones=[(1, 1), (2, 2), (1, 1), (3, 3)])
    assert n == 2  # el agua y la casilla repetida se descartan
    assert sorted(c.pos for c in pob.criaturas_vivas()) == [(1, 1), (3, 3)]


def test_una_especie_extinta_vuelve_a_la_vida_al_agregarle_individuos():
    mapa = MapaFalso(10, 10)
    pob = nueva()
    pob.crear_especie("a", H, 0, mapa)
    assert pob.especies["a"].estado == EstadoEspecie.EXTINTA
    pob.agregar_individuos("a", 3, mapa)
    assert pob.especies["a"].estado == EstadoEspecie.ACTIVA and pob.total() == 3


# --- indice por casilla -------------------------------------------------------------------------------------


def test_mover_actualiza_el_indice():
    mapa = MapaFalso(10, 10)
    pob = nueva()
    pob.crear_especie("a", H, 0, mapa)
    c = pob.agregar_criatura("a", (2, 2))
    c.iniciar_tick()
    pob.mover(c, (3, 2))
    assert c.pos == (3, 2)
    assert pob.criaturas_en((2, 2)) == [] and pob.criaturas_en((3, 2)) == [c]
    pob.mover(c, (3, 2))  # misma casilla: no cambia nada
    assert pob.criaturas_en((3, 2)) == [c]
    assert pob.verificar_consistencia() == []


@pytest.mark.parametrize("n, radio", [(100, 4), (100, 6), (30, 3), (400, 10)])
def test_criaturas_en_radio_coincide_con_la_busqueda_exhaustiva(n, radio):
    # (n=100, radio=4) usa el indice por casillas; (n=100, radio=6) recorre todas
    cfg = CFG.con(MAX_CRIATURAS=1000)
    mapa = MapaFalso(30, 30)
    pob = nueva(cfg, semilla=5)
    pob.crear_especie("a", H, n, mapa)
    for centro in [(15, 15), (0, 0), (29, 29), (3, 20)]:
        esperadas = {
            c.id for c in pob.criaturas_vivas()
            if max(abs(c.pos[0] - centro[0]), abs(c.pos[1] - centro[1])) <= radio
        }
        obtenidas = pob.criaturas_en_radio(centro, radio)
        assert {c.id for c in obtenidas} == esperadas
        assert len(obtenidas) == len(esperadas)  # sin repetidas


# --- muerte y eventos ----------------------------------------------------------------------------------------


def test_una_muerte_externa_se_cuenta_al_instante_y_se_retira_en_el_tick():
    mapa = mapa_con(10, 10)
    pob = nueva()
    eventos = registro(pob)
    pob.crear_especie("a", H, 5, mapa)
    c = pob.criaturas_vivas()[0]
    c.morir(CausaMuerte.FUEGO)
    assert pob.total() == 4 and pob.hay_cupo()
    muertes = [e for e in eventos if e.tipo == MUERTE]
    assert len(muertes) == 1 and muertes[0].causa == CausaMuerte.FUEGO
    assert muertes[0].criatura_id == c.id and muertes[0].especie == "a"
    pob.actualizar(mapa, 22.0)
    assert c.id not in pob._criaturas and c not in pob.criaturas_en(c.pos)
    assert pob.verificar_consistencia() == []


def test_se_extingue_por_hambre_y_el_evento_sale_una_sola_vez():
    mapa = MapaFalso(10, 10)  # sin comida
    pob = nueva()
    eventos = registro(pob)
    pob.crear_especie("a", H, 1, mapa, energia=0.3)
    assert pob.total() == 1 and pob.especies["a"].estado == EstadoEspecie.ACTIVA
    pob.actualizar(mapa, 22.0)
    assert pob.total() == 0 and pob.especies["a"].estado == EstadoEspecie.EXTINTA
    assert [e.causa for e in eventos if e.tipo == MUERTE] == [CausaMuerte.HAMBRE]
    pob.actualizar(mapa, 22.0)
    pob.actualizar(mapa, 22.0)
    assert [e.especie for e in eventos if e.tipo == EXTINCION] == ["a"]


def test_la_presa_comida_se_retira_y_su_especie_se_extingue():
    mapa = MapaFalso(30, 30)
    pob = nueva()
    eventos = registro(pob)
    pob.crear_especie("cabra", H, 0, mapa)
    pob.crear_especie("lobo", C, 0, mapa)
    presa = pob.agregar_criatura("cabra", (15, 15), energia=50.0, stats=Estadisticas(1, 1, 4))
    lobo = pob.agregar_criatura("lobo", (14, 15), energia=50.0, stats=Estadisticas(2.5, 2.0, 6))
    pob.actualizar(mapa, 22.0)
    assert not presa.viva and presa.causa_muerte == CausaMuerte.DEPREDACION
    assert pob.total() == 1 and pob.especies["cabra"].estado == EstadoEspecie.EXTINTA
    assert pob.criaturas_en(presa.pos) == [lobo] or lobo in pob.criaturas_en(lobo.pos)
    assert any(e.tipo == MUERTE and e.causa == CausaMuerte.DEPREDACION for e in eventos)
    assert any(e.tipo == EXTINCION and e.especie == "cabra" for e in eventos)
    assert pob.verificar_consistencia() == []


def test_eliminar_en_mata_por_fuego_y_avisa():
    mapa = MapaFalso(10, 10)
    pob = nueva(CFG.con(MAX_POR_CASILLA=2))
    eventos = registro(pob)
    pob.crear_especie("a", H, 0, mapa)
    pob.crear_especie("b", H, 0, mapa)
    pob.agregar_criatura("a", (4, 4))
    pob.agregar_criatura("b", (4, 4))
    pob.agregar_criatura("a", (7, 7))
    assert pob.eliminar_en(4, 4) == 2
    assert pob.eliminar_en(4, 4) == 0 and pob.eliminar_en(0, 0) == 0
    assert pob.total() == 1 and pob.criaturas_en((4, 4)) == []
    assert [e.causa for e in eventos if e.tipo == MUERTE] == [CausaMuerte.FUEGO] * 2
    assert pob.especies["b"].estado == EstadoEspecie.EXTINTA
    assert pob.especies["a"].estado == EstadoEspecie.ACTIVA
    assert pob.verificar_consistencia() == []


def test_eliminar_especie_retira_a_todas_sus_criaturas():
    mapa = mapa_con(20, 20)
    pob = nueva()
    eventos = registro(pob)
    pob.crear_especie("a", H, 15, mapa)
    pob.crear_especie("b", H, 5, mapa)
    assert pob.eliminar_especie("a") == 15
    assert pob.total() == 5 and pob.especies["a"].estado == EstadoEspecie.ELIMINADA
    assert pob.especies["a"].contar() == 0
    assert [e.causa for e in eventos if e.tipo == MUERTE] == [CausaMuerte.ELIMINACION] * 15
    assert all(c.especie == "b" for c in pob.criaturas_vivas())
    assert "a" not in pob.snapshot()
    assert pob.eliminar_especie("a") == 0  # ya eliminada
    assert pob.verificar_consistencia() == []
    with pytest.raises(KeyError):
        pob.eliminar_especie("no existe")
    simular(pob, mapa, 20)


def test_no_se_agregan_criaturas_a_una_especie_eliminada():
    mapa = MapaFalso(10, 10)
    pob = nueva()
    pob.crear_especie("a", H, 2, mapa)
    pob.eliminar_especie("a")
    with pytest.raises(ValueError):
        pob.agregar_criatura("a", (1, 1))
    with pytest.raises(ValueError):
        pob.agregar_individuos("a", 3, mapa)
    assert pob.total() == 0


def test_nacimientos_menos_muertes_es_la_poblacion():
    pob, mapa = nueva(semilla=3), mapa_con(40, 40)
    eventos = registro(pob)  # antes de crear, para contar tambien a las iniciales
    pob.crear_especie("conejo", H, 60, mapa)
    pob.crear_especie("zorro", OM, 20, mapa)
    pob.crear_especie("lobo", C, 10, mapa)
    for _ in range(300):
        paso(pob, mapa)
        nacimientos = sum(e.tipo == NACIMIENTO for e in eventos)
        muertes = sum(e.tipo == MUERTE for e in eventos)
        assert nacimientos - muertes == pob.total()


def test_desuscribir_deja_de_avisar():
    mapa = MapaFalso(10, 10)
    pob = nueva()
    pob.crear_especie("a", H, 0, mapa)
    eventos = []
    escucha = eventos.append
    pob.suscribir(escucha)
    pob.agregar_criatura("a", (1, 1))
    assert len(eventos) == 1 and eventos[0].tipo == NACIMIENTO
    pob.desuscribir(escucha)
    pob.agregar_criatura("a", (2, 2))
    assert len(eventos) == 1


# --- reproduccion -------------------------------------------------------------------------------------


def preparar_pareja(energia=70.0, especie_b="a", ancho=10, alto=10, cfg=CFG):
    mapa = MapaFalso(ancho, alto)
    pob = nueva(cfg)
    pob.crear_especie("a", H, 0, mapa)
    if especie_b != "a":
        pob.crear_especie(especie_b, H, 0, mapa)
    uno = pob.agregar_criatura("a", (4, 4), energia=energia, stats=Estadisticas(1, 1, 4))
    dos = pob.agregar_criatura(especie_b, (5, 4), energia=energia, stats=Estadisticas(1, 1, 4))
    return pob, mapa, uno, dos


def test_dos_criaturas_adyacentes_con_energia_tienen_una_cria():
    pob, mapa, uno, dos = preparar_pareja()
    eventos = registro(pob)
    pob.actualizar(mapa, 22.0)
    assert pob.total() == 3 and pob.especies["a"].contar() == 3
    cria = max(pob.criaturas_vivas(), key=lambda c: c.id)
    assert cria.energia == CFG.ENERGIA_CRIA and cria.edad == 0
    assert max(abs(cria.pos[0] - 4), abs(cria.pos[1] - 4)) <= CFG.RADIO_BUSQUEDA_CRIA + 1
    assert uno.energia == pytest.approx(70 - 25 - 0.5) and dos.energia == pytest.approx(70 - 25 - 0.5)
    assert [e.tipo for e in eventos] == [NACIMIENTO]
    assert pob.verificar_consistencia() == []


def test_la_cria_hereda_de_los_padres_con_mutacion():
    pob, mapa, uno, dos = preparar_pareja()
    pob.actualizar(mapa, 22.0)
    cria = max(pob.criaturas_vivas(), key=lambda c: c.id)
    for rasgo in ("tamano", "velocidad", "vision"):
        padres = (getattr(uno.stats, rasgo) * getattr(dos.stats, rasgo)) ** 0.5
        assert getattr(cria.stats, rasgo) == pytest.approx(padres, rel=0.3)  # SIGMA = 5 %


def test_reproduccion_repetida_un_padre_lleno_se_reproduce_hasta_bajar_de_50():
    pob, mapa, _uno, _dos = preparar_pareja(energia=100.0, ancho=20, alto=20)
    eventos = registro(pob)
    for _ in range(4):
        pob.actualizar(mapa, 22.0)
    assert sum(e.tipo == NACIMIENTO for e in eventos) == 2  # 100 -> 75 -> 50 -> deja de buscar
    assert pob.total() == 4


def test_no_hay_reproduccion_entre_especies_distintas():
    pob, mapa, _uno, _dos = preparar_pareja(especie_b="b")
    pob.actualizar(mapa, 22.0)
    assert pob.total() == 2


def test_sin_casilla_libre_no_hay_cria_y_no_se_cobra_nada():
    mapa = MapaFalso(2, 1)  # el mapa ya esta lleno con los dos padres
    pob = nueva()
    pob.crear_especie("a", H, 0, mapa)
    uno = pob.agregar_criatura("a", (0, 0), energia=70.0)
    dos = pob.agregar_criatura("a", (1, 0), energia=70.0)
    assert pob.reproducir(uno, dos, mapa) is False
    assert uno.energia == 70.0 and dos.energia == 70.0
    assert not uno.turno_hecho and not dos.turno_hecho and pob.total() == 2
    pob.actualizar(mapa, 22.0)
    assert pob.total() == 2


def test_sin_cupo_no_hay_cria_y_no_se_cobra_nada():
    pob, mapa, uno, dos = preparar_pareja(cfg=CFG.con(MAX_CRIATURAS=2))
    assert not pob.hay_cupo()
    assert pob.reproducir(uno, dos, mapa) is False
    assert uno.energia == 70.0 and dos.energia == 70.0
    pob.actualizar(mapa, 22.0)
    assert pob.total() == 2


def test_no_se_reproduce_quien_no_quiere_o_no_alcanza():
    pob, mapa, uno, dos = preparar_pareja(energia=60.0)  # menos de 70
    assert pob.reproducir(uno, dos, mapa) is False
    pob2, mapa2, a, b = preparar_pareja()
    b.pos = (8, 8)  # lejos
    assert pob2.reproducir(a, b, mapa2) is False
    pob3, mapa3, c, d = preparar_pareja()
    c.turno_hecho = True  # ya actuo
    assert pob3.reproducir(c, d, mapa3) is False
    assert pob3.reproducir(d, d, mapa3) is False


def test_la_cria_ocupa_su_casilla_desde_que_nace_el_tick():
    # con una sola casilla libre cerca, solo cabe una cria por tick
    cfg = CFG.con(RADIO_BUSQUEDA_CRIA=1)
    mapa = MapaFalso(3, 2)
    pob = nueva(cfg)
    pob.crear_especie("a", H, 0, mapa)
    a = pob.agregar_criatura("a", (0, 0), energia=100.0)
    b = pob.agregar_criatura("a", (1, 0), energia=100.0)
    for pos in [(2, 0), (0, 1), (2, 1)]:
        pob.agregar_criatura("a", pos, energia=30.0)
    # la unica casilla libre es (1, 1)
    assert pob.casilla_libre_cerca((1, 0), mapa) == (1, 1)
    assert pob.reproducir(a, b, mapa) is True
    assert pob.casilla_libre_cerca((1, 0), mapa) is None  # ya reservada por la cria
    pob.actualizar(mapa, 22.0)
    assert pob.total() == 6 and pob.verificar_consistencia() == []


# --- repetibilidad y guardado ---------------------------------------------------------------------------------


def test_misma_semilla_misma_historia_y_otra_semilla_otra():
    def historia(semilla):
        pob, mapa = escenario3(semilla)
        trazo = []
        for _ in range(150):
            paso(pob, mapa)
            trazo.append(firma(pob))
        return trazo

    assert historia(11) == historia(11)
    assert historia(11) != historia(12)


def test_guardar_y_cargar_a_mitad_de_camino_continua_igual():
    pob, mapa = escenario3(semilla=7)
    simular(pob, mapa, 120)
    guardado = json.loads(json.dumps(pob.a_dict()))
    copia = Poblacion.desde_dict(guardado)
    mapa_copia = copy.deepcopy(mapa)
    assert copia.a_dict() == pob.a_dict()
    assert copia.verificar_consistencia() == []
    for _ in range(80):
        paso(pob, mapa)
        paso(copia, mapa_copia)
        assert firma(copia) == firma(pob)
    assert copia.verificar_consistencia() == []


def test_cargar_conserva_especies_extintas_y_eliminadas():
    mapa = mapa_con(15, 15)
    pob = nueva()
    pob.crear_especie("viva", H, 5, mapa)
    pob.crear_especie("vacia", H, 0, mapa)
    pob.crear_especie("borrada", C, 3, mapa)
    pob.eliminar_especie("borrada")
    copia = Poblacion.desde_dict(json.loads(json.dumps(pob.a_dict())))
    assert {n: e.estado for n, e in copia.especies.items()} == {
        "viva": EstadoEspecie.ACTIVA, "vacia": EstadoEspecie.EXTINTA,
        "borrada": EstadoEspecie.ELIMINADA,
    }
    assert copia.total() == 5 and copia.especies["viva"].contar() == 5


# --- instantaneas ------------------------------------------------------------------------------------------------------


def test_snapshot_da_la_poblacion_y_los_promedios():
    mapa = MapaFalso(10, 10)
    pob = nueva()
    pob.crear_especie("a", H, 0, mapa)
    pob.agregar_criatura("a", (1, 1), energia=40.0, stats=Estadisticas(1.0, 1.0, 4.0))
    pob.agregar_criatura("a", (2, 2), energia=60.0, stats=Estadisticas(3.0, 2.0, 6.0))
    pob.crear_especie("vacia", C, 0, mapa)
    pob.crear_especie("borrada", C, 0, mapa)
    pob.eliminar_especie("borrada")
    s = pob.snapshot()
    assert set(s) == {"a", "vacia"}
    assert s["a"] == {"poblacion": 2, "tamano": 2.0, "velocidad": 1.5, "vision": 5.0, "energia": 50.0}
    assert s["vacia"] == {"poblacion": 0, "tamano": None, "velocidad": None, "vision": None, "energia": None}


# --- simulaciones largas -----------------------------------------------------------------------------------------------------


def test_una_especie_con_comida_crece_y_el_indice_se_mantiene_consistente():
    pob, mapa = nueva(), mapa_con(30, 30, "arbol")
    pob.crear_especie("conejo", H, 20, mapa)
    simular(pob, mapa, 120)
    assert pob.total() > 20


def test_nunca_se_supera_el_limite_aunque_haya_comida_de_sobra():
    cfg = CFG.con(MAX_CRIATURAS=60)
    pob, mapa = nueva(cfg), mapa_con(30, 30, "arbol")
    pob.crear_especie("conejo", H, 20, mapa)
    maximo = 0
    for _ in range(500):
        paso(pob, mapa)
        assert pob.total() <= 60
        maximo = max(maximo, pob.total())
    assert maximo == 60  # y el limite si se alcanza
    assert pob.verificar_consistencia() == []


def test_la_vejez_mata_a_las_criaturas_iniciales():
    cfg = CFG.con(VIDA_BASE=10.0, VARIACION_VIDA=0.0)
    pob, mapa = nueva(cfg), mapa_con(20, 20, "arbol")
    eventos = registro(pob)
    pob.crear_especie("a", H, 10, mapa)
    simular(pob, mapa, 15)
    assert any(e.tipo == MUERTE and e.causa == CausaMuerte.VEJEZ for e in eventos)


def test_tres_dietas_durante_1000_ticks_sin_errores():
    pob, mapa = escenario3(semilla=4)
    for t in range(1000):
        paso(pob, mapa)
        assert pob.total() <= CFG.MAX_CRIATURAS
        if t % 50 == 0:
            assert pob.verificar_consistencia() == []
    assert pob.verificar_consistencia() == []


def test_un_tick_con_cientos_de_criaturas_es_rapido():
    cfg = CFG.con(MAX_CRIATURAS=1000)
    pob, mapa = nueva(cfg), mapa_con(100, 100, "arbol")
    pob.crear_especie("a", H, 400, mapa)
    pob.crear_especie("b", OM, 200, mapa)
    pob.crear_especie("c", C, 100, mapa)
    inicio = time.perf_counter()
    for _ in range(20):
        paso(pob, mapa)
    por_tick = (time.perf_counter() - inicio) / 20
    assert por_tick < 0.5, f"{por_tick:.3f} s por tick"
