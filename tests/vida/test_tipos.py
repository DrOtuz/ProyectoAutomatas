import pytest

from simulador.vida.tipos import (
    CausaMuerte,
    Dieta,
    Estado,
    EstadoEspecie,
    Objetivo,
    TipoObjetivo,
)


def test_dietas_y_lo_que_comen():
    assert Dieta.HERBIVORO.come_plantas and not Dieta.HERBIVORO.come_carne
    assert Dieta.CARNIVORO.come_carne and not Dieta.CARNIVORO.come_plantas
    assert Dieta.OMNIVORO.come_plantas and Dieta.OMNIVORO.come_carne


def test_los_enums_se_reconstruyen_desde_su_valor():
    # lo usan a_dict / desde_dict al guardar y cargar
    for enum in (Dieta, Estado, CausaMuerte, EstadoEspecie, TipoObjetivo):
        for miembro in enum:
            assert enum(miembro.value) is miembro


def test_los_estados_del_automata():
    assert {e.name for e in Estado} == {
        "HUIR", "BUSCAR_ALIMENTO", "BUSCAR_PAREJA", "EXPLORAR", "MUERTA",
    }


def test_objetivo_es_inmutable_y_tiene_valores_por_defecto():
    o = Objetivo(TipoObjetivo.PLANTA, (3, 4))
    assert o.criatura is None and o.ganancia == 0.0 and o.distancia == 0
    with pytest.raises(AttributeError):
        o.ganancia = 5  # type: ignore[misc]
