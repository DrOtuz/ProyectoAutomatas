import copy
import csv
import random

import pytest

from simulador.vida import simulacion_vida as sv
from simulador.vida.config import ConfigVida
from simulador.vida.poblacion import Poblacion
from simulador.vida.tipos import Dieta


@pytest.mark.parametrize("semilla", [1, 2, 3])
def test_2000_ticks_sin_interfaz_terminan_sin_excepcion(semilla):
    sim = sv.correr(2000, semilla=semilla, salida=None)
    assert sim.pob.tick == 2000
    assert sim.pob.verificar_consistencia() == []
    assert sim.pob.total() <= ConfigVida().MAX_CRIATURAS


def test_el_historial_se_llena_para_las_tres_especies():
    sim = sv.correr(60, semilla=1, salida=None)
    assert sim.historial.nombres() == ["conejo", "zorro", "lobo"]
    for n in sim.historial.nombres():
        assert len(sim.historial[n]) == 60
        assert sim.historial[n].serie("poblacion")[0][0] == 1


def test_misma_semilla_mismo_csv(tmp_path):
    rutas = []
    for i in range(2):
        sim = sv.correr(150, semilla=5, salida=None)
        ruta = tmp_path / f"s{i}.csv"
        sv.exportar_csv(sim.historial, str(ruta))
        rutas.append(ruta)
    assert rutas[0].read_text() == rutas[1].read_text()
    filas = list(csv.reader(rutas[0].open()))
    assert filas[0][0] == "tick" and "conejo_poblacion" in filas[0]
    assert len(filas) == 151  # encabezado + 150 ticks


def test_otra_semilla_otro_csv(tmp_path):
    a, b = (sv.correr(150, semilla=s, salida=None) for s in (5, 6))
    sv.exportar_csv(a.historial, str(tmp_path / "a.csv"))
    sv.exportar_csv(b.historial, str(tmp_path / "b.csv"))
    assert (tmp_path / "a.csv").read_text() != (tmp_path / "b.csv").read_text()


def test_guardar_a_mitad_y_seguir_da_lo_mismo_que_no_guardar():
    sim = sv.correr(120, semilla=3, salida=None)
    guardado = sim.pob.a_dict()
    mapa2 = copy.deepcopy(sim.mapa)
    sv.correr(80, sim=sim, salida=None)  # sigue sin guardar

    pob2 = Poblacion.desde_dict(copy.deepcopy(guardado), sim.pob.cfg)
    for _ in range(80):
        mapa2.regenerar()
        pob2.actualizar(mapa2, sim.pob.cfg.TEMPERATURA_POR_DEFECTO)

    def firma(p):
        return sorted((c.id, c.pos, round(c.energia, 9)) for c in p.criaturas_vivas())

    assert pob2.tick == sim.pob.tick
    assert firma(pob2) == firma(sim.pob)


def test_barrido_resume_las_dietas_vivas():
    res = sv.barrido({"base": ConfigVida()}, [1, 2], 30, salida=None)
    r = res["base"]
    assert r["semillas"] == 2
    assert set(r["vivas"]) == {d.value for d in Dieta}
    assert 0 <= r["coexisten"] <= 2 and r["saturadas"] in (0, 1, 2)
