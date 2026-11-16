import dataclasses
import json
import math
import random
import statistics

import pytest

from simulador.vida.config import ConfigVida
from simulador.vida.estadisticas import Estadisticas
from simulador.vida.tipos import Dieta

CFG = ConfigVida()


# --- validacion e inmutabilidad -----------------------------------------------


@pytest.mark.parametrize("malo", [0, -1.0, math.nan, math.inf, -math.inf, "1", None, True])
@pytest.mark.parametrize("rasgo", ["tamano", "velocidad", "vision"])
def test_rechaza_rasgos_invalidos(rasgo, malo):
    base = {"tamano": 1.0, "velocidad": 1.0, "vision": 4.0}
    base[rasgo] = malo
    with pytest.raises(ValueError):
        Estadisticas(**base)


def test_acepta_enteros_y_los_guarda_como_float():
    e = Estadisticas(1, 2, 4)
    assert isinstance(e.tamano, float) and isinstance(e.vision, float)
    assert e == Estadisticas(1.0, 2.0, 4.0)


def test_es_inmutable():
    e = Estadisticas(1.0, 1.0, 4.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.tamano = 2.0  # type: ignore[misc]


# --- herencia -------------------------------------------------------------------


def test_con_sigma_cero_el_hijo_es_la_media_geometrica_exacta():
    cfg = CFG.con(SIGMA=0.0)
    madre, padre = Estadisticas(1.0, 4.0, 2.0), Estadisticas(4.0, 1.0, 8.0)
    hijo = Estadisticas.cruzar(madre, padre, cfg, random.Random(1))
    assert hijo.tamano == pytest.approx(2.0)
    assert hijo.velocidad == pytest.approx(2.0)
    assert hijo.vision == pytest.approx(4.0)


def test_padres_iguales_y_sigma_cero_dan_un_hijo_igual():
    cfg = CFG.con(SIGMA=0.0)
    p = Estadisticas(1.5, 1.2, 5.0)
    hijo = Estadisticas.cruzar(p, p, cfg, random.Random(2))
    assert hijo == p


def test_el_cruce_es_simetrico_sin_mutacion():
    cfg = CFG.con(SIGMA=0.0)
    a, b = Estadisticas(1.0, 2.0, 3.0), Estadisticas(2.0, 5.0, 9.0)
    assert Estadisticas.cruzar(a, b, cfg, random.Random(3)) == Estadisticas.cruzar(
        b, a, cfg, random.Random(3)
    )


def test_la_mutacion_tiene_media_cero_y_desviacion_sigma_en_escala_log():
    rng = random.Random(42)
    madre, padre = Estadisticas(1.0, 1.0, 4.0), Estadisticas(1.0, 1.0, 4.0)
    eps = []
    for _ in range(10_000):
        hijo = Estadisticas.cruzar(madre, padre, CFG, rng)
        eps.append(math.log(hijo.tamano / madre.tamano))
    assert abs(statistics.fmean(eps)) < 0.003
    assert statistics.pstdev(eps) == pytest.approx(CFG.SIGMA, abs=0.002)


def test_la_desviacion_sigue_a_sigma_de_la_configuracion():
    rng = random.Random(7)
    cfg = CFG.con(SIGMA=0.08)
    p = Estadisticas(2.0, 1.0, 4.0)
    eps = [math.log(Estadisticas.cruzar(p, p, cfg, rng).velocidad) for _ in range(10_000)]
    assert statistics.pstdev(eps) == pytest.approx(0.08, abs=0.003)


def test_la_mutacion_es_proporcional_al_valor_del_rasgo():
    rng = random.Random(8)
    chico, grande = Estadisticas(0.5, 0.5, 0.5), Estadisticas(5.0, 5.0, 5.0)
    rel_chico = [Estadisticas.cruzar(chico, chico, CFG, rng).tamano / 0.5 for _ in range(5000)]
    rel_grande = [Estadisticas.cruzar(grande, grande, CFG, rng).tamano / 5.0 for _ in range(5000)]
    assert statistics.pstdev(rel_chico) == pytest.approx(statistics.pstdev(rel_grande), abs=0.005)


def test_los_tres_rasgos_mutan_de_forma_independiente():
    rng = random.Random(9)
    p = Estadisticas(1.0, 1.0, 1.0)
    hijos = [Estadisticas.cruzar(p, p, CFG, rng) for _ in range(5000)]
    s = [math.log(h.tamano) for h in hijos]
    v = [math.log(h.velocidad) for h in hijos]
    assert abs(statistics.correlation(s, v)) < 0.05


def test_un_rasgo_nunca_es_cero_ni_negativo_aunque_sigma_sea_grande():
    rng = random.Random(10)
    cfg = CFG.con(SIGMA=2.0)
    p = Estadisticas(1.0, 1.0, 1.0)
    for _ in range(5000):
        h = Estadisticas.cruzar(p, p, cfg, rng)
        assert h.tamano > 0 and h.velocidad > 0 and h.vision > 0
        assert all(math.isfinite(x) for x in h.a_dict().values())


def test_misma_semilla_mismas_estadisticas():
    a, b = Estadisticas(1.0, 1.0, 4.0), Estadisticas(2.0, 1.5, 5.0)
    uno = Estadisticas.cruzar(a, b, CFG, random.Random(11))
    dos = Estadisticas.cruzar(a, b, CFG, random.Random(11))
    otro = Estadisticas.cruzar(a, b, CFG, random.Random(12))
    assert uno == dos and uno != otro


def test_la_secuencia_del_azar_no_depende_de_sigma():
    # con sigma 0 y sigma > 0 el generador avanza igual (repetibilidad)
    a = Estadisticas(1.0, 1.0, 4.0)
    r1, r2 = random.Random(5), random.Random(5)
    Estadisticas.cruzar(a, a, CFG.con(SIGMA=0.0), r1)
    Estadisticas.cruzar(a, a, CFG.con(SIGMA=0.5), r2)
    assert r1.random() == r2.random()


def test_promediar_generaciones_encoge_la_variacion():
    # promediar logaritmos encoge la variacion; la mutacion la mantiene
    rng = random.Random(13)
    cfg = CFG.con(SIGMA=0.05)
    poblacion = [Estadisticas.desde_plantilla(Dieta.HERBIVORO, cfg.con(VARIACION_INICIAL=0.5), rng)
                 for _ in range(200)]
    var_inicial = statistics.pvariance([math.log(e.tamano) for e in poblacion])
    for _ in range(30):
        poblacion = [
            Estadisticas.cruzar(rng.choice(poblacion), rng.choice(poblacion), cfg, rng)
            for _ in range(200)
        ]
    var_final = statistics.pvariance([math.log(e.tamano) for e in poblacion])
    assert var_final < var_inicial


# --- plantillas -------------------------------------------------------------------


@pytest.mark.parametrize("dieta", list(Dieta))
def test_desde_plantilla_queda_dentro_del_10_por_ciento(dieta):
    rng = random.Random(20)
    s, v, r = CFG.PLANTILLAS[dieta]
    vistos = set()
    for _ in range(1000):
        e = Estadisticas.desde_plantilla(dieta, CFG, rng)
        assert s * 0.9 <= e.tamano <= s * 1.1
        assert v * 0.9 <= e.velocidad <= v * 1.1
        assert r * 0.9 <= e.vision <= r * 1.1
        vistos.add(e)
    assert len(vistos) > 900  # cada criatura sale con variacion individual


def test_desde_plantilla_sin_variacion_es_exacta():
    cfg = CFG.con(VARIACION_INICIAL=0.0)
    e = Estadisticas.desde_plantilla(Dieta.CARNIVORO, cfg, random.Random(1))
    assert (e.tamano, e.velocidad, e.vision) == (2.5, 1.6, 6.0)


def test_desde_plantilla_usa_la_plantilla_de_la_configuracion():
    cfg = CFG.con(PLANTILLAS={**CFG.PLANTILLAS, Dieta.HERBIVORO: (3.0, 2.0, 7.0)},
                  VARIACION_INICIAL=0.0)
    e = Estadisticas.desde_plantilla(Dieta.HERBIVORO, cfg, random.Random(1))
    assert (e.tamano, e.velocidad, e.vision) == (3.0, 2.0, 7.0)


# --- derivados --------------------------------------------------------------------


@pytest.mark.parametrize(
    "vision, esperado", [(4.0, 4), (0.2, 1), (0.0001, 1), (4.6, 5), (5.4, 5), (6.0, 6)]
)
def test_radio_entero(vision, esperado):
    assert Estadisticas(1.0, 1.0, vision).radio_entero() == esperado


def test_masa_en_unidades_u():
    assert Estadisticas(1.0, 1.0, 4.0).masa_u(CFG) == 100
    assert Estadisticas(2.5, 1.0, 4.0).masa_u(CFG) == 250
    assert Estadisticas(2.5, 1.0, 4.0).masa_u(CFG.con(UNIDADES_POR_TAMANO=10.0)) == 25


# --- guardado ---------------------------------------------------------------------


def test_a_dict_desde_dict_son_inversos_y_serializan_como_json():
    e = Estadisticas(1.234567, 0.987654, 4.321)
    assert Estadisticas.desde_dict(e.a_dict()) == e
    assert Estadisticas.desde_dict(json.loads(json.dumps(e.a_dict()))) == e
    assert set(e.a_dict()) == {"tamano", "velocidad", "vision"}


def test_desde_dict_con_datos_incompletos_o_invalidos_falla():
    with pytest.raises(KeyError):
        Estadisticas.desde_dict({"tamano": 1.0, "velocidad": 1.0})
    with pytest.raises(ValueError):
        Estadisticas.desde_dict({"tamano": 0.0, "velocidad": 1.0, "vision": 4.0})


def test_variar_multiplica_cada_rasgo_dentro_del_margen():
    rng = random.Random(30)
    base = Estadisticas(2.0, 1.0, 5.0)
    vistos = set()
    for _ in range(500):
        e = base.variar(0.2, rng)
        assert 1.6 <= e.tamano <= 2.4 and 0.8 <= e.velocidad <= 1.2 and 4.0 <= e.vision <= 6.0
        vistos.add(e)
    assert len(vistos) > 400
    assert base.variar(0.0, rng) == base
