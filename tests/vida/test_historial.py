import json

import pytest

from simulador.vida.historial import METRICAS, GestorHistorial, HistorialEspecie


def resumen(n, s=1.0, v=2.0, r=3.0, e=50.0):
    return dict(poblacion=n, tamano=s, velocidad=v, vision=r, energia=e)


def test_serie_devuelve_las_cinco_metricas_en_orden_de_tick():
    h = HistorialEspecie("a")
    h.registrar(1, resumen(10, s=1.0))
    h.registrar(2, resumen(12, s=1.5))
    assert [m for m in METRICAS] == ["poblacion", "tamano", "velocidad", "vision", "energia"]
    assert h.serie("poblacion") == [(1, 10), (2, 12)]
    assert h.serie("tamano") == [(1, 1.0), (2, 1.5)]
    for m in METRICAS:
        assert len(h.serie(m)) == 2


def test_metrica_desconocida_y_ticks_desordenados_fallan():
    h = HistorialEspecie("a")
    h.registrar(5, resumen(1))
    with pytest.raises(ValueError):
        h.serie("peso")
    with pytest.raises(ValueError):
        h.registrar(5, resumen(1))


def test_ultimo():
    h = HistorialEspecie("a")
    assert h.ultimo() is None
    h.registrar(3, resumen(7))
    assert h.ultimo()["tick"] == 3 and h.ultimo()["poblacion"] == 7


def test_no_supera_max_puntos_y_conserva_lo_reciente():
    h = HistorialEspecie("a", max_puntos=100)
    for t in range(1, 1001):
        h.registrar(t, resumen(t))
        assert len(h) <= 100
    ticks = [t for t, _ in h.serie("poblacion")]
    assert ticks == sorted(ticks) and len(set(ticks)) == len(ticks)
    assert ticks[-1] == 1000
    assert ticks[-10:] == list(range(991, 1001))  # lo mas reciente queda completo
    assert ticks[0] <= 10  # y lo antiguo sigue representado


def test_especie_extinta_guarda_none():
    h = HistorialEspecie("a")
    h.registrar(1, dict(poblacion=0, tamano=None, velocidad=None, vision=None, energia=None))
    assert h.serie("tamano") == [(1, None)]


def test_gestor_crea_uno_por_especie_y_conserva_extintas():
    g = GestorHistorial()
    g.registrar(1, {"a": resumen(3), "b": resumen(2)})
    g.registrar(2, {"a": resumen(4)})  # b ya no aparece (p. ej. eliminada)
    assert g.nombres() == ["a", "b"]
    assert len(g["a"]) == 2 and len(g["b"]) == 1
    g.eliminar("b")
    assert "b" not in g


def test_guardar_y_cargar():
    g = GestorHistorial(max_puntos=50)
    for t in range(1, 120):
        g.registrar(t, {"a": resumen(t)})
    g2 = GestorHistorial.desde_dict(json.loads(json.dumps(g.a_dict())))
    assert g2.a_dict() == g.a_dict()
    g2.registrar(500, {"a": resumen(1)})
    assert g2["a"].ultimo()["tick"] == 500
