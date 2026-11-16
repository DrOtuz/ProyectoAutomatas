import pytest

from simulador.vida.config import ConfigVida
from simulador.vida.criatura import Criatura
from simulador.vida.especie import Especie
from simulador.vida.estadisticas import Estadisticas
from simulador.vida.tipos import Dieta, EstadoEspecie

from valores_doc import CFG_DOC as CFG


def especie(nombre="conejo", dieta=Dieta.HERBIVORO):
    return Especie(nombre, dieta, Estadisticas(1.0, 1.0, 4.0))


def criatura(id, nombre="conejo"):
    return Criatura(id, nombre, Dieta.HERBIVORO, Estadisticas(1, 1, 4), (0, 0), CFG, 1000)


def test_una_especie_nueva_esta_activa_y_vacia():
    e = especie()
    assert e.estado == EstadoEspecie.ACTIVA and e.contar() == 0
    assert e.color is None and e.dieta == Dieta.HERBIVORO


@pytest.mark.parametrize("nombre", ["", "   ", None, 5])
def test_exige_un_nombre(nombre):
    with pytest.raises(ValueError):
        Especie(nombre, Dieta.HERBIVORO, Estadisticas(1, 1, 4))


def test_exige_una_dieta_valida():
    with pytest.raises(ValueError):
        Especie("x", "herbivoro", Estadisticas(1, 1, 4))


def test_agregar_y_quitar_llevan_la_cuenta():
    e = especie()
    a, b = criatura(1), criatura(2)
    e.agregar(a)
    e.agregar(b)
    e.agregar(a)  # repetir no duplica
    assert e.contar() == 2 and e.ids == {1, 2}
    e.quitar(a)
    e.quitar(a)  # quitar de nuevo no falla
    assert e.contar() == 1 and e.ids == {2}


def test_quitar_a_la_ultima_no_declara_la_extincion():
    e = especie()
    a = criatura(1)
    e.agregar(a)
    e.quitar(a)
    assert e.contar() == 0 and e.estado == EstadoEspecie.ACTIVA  # lo decide Poblacion


def test_no_acepta_criaturas_de_otra_especie():
    with pytest.raises(ValueError):
        especie("conejo").agregar(criatura(1, "lobo"))


def test_extinguir_solo_si_no_quedan_criaturas():
    e = especie()
    a = criatura(1)
    e.agregar(a)
    with pytest.raises(ValueError):
        e.extinguir()
    e.quitar(a)
    e.extinguir()
    assert e.estado == EstadoEspecie.EXTINTA


def test_una_especie_extinta_se_reactiva_pero_una_activa_no_cambia():
    e = especie()
    e.reactivar()
    assert e.estado == EstadoEspecie.ACTIVA
    e.extinguir()
    e.reactivar()
    assert e.estado == EstadoEspecie.ACTIVA


def test_eliminar_marca_la_especie_y_ya_no_acepta_criaturas():
    e = especie()
    e.eliminar()
    assert e.estado == EstadoEspecie.ELIMINADA
    with pytest.raises(ValueError):
        e.agregar(criatura(1))
    e.reactivar()  # una eliminada no vuelve
    assert e.estado == EstadoEspecie.ELIMINADA


def test_a_dict_desde_dict_son_inversos():
    e = Especie("lobo", Dieta.CARNIVORO, Estadisticas(2.5, 1.6, 6.0), color="#aa3300")
    e.eliminar()
    copia = Especie.desde_dict(e.a_dict())
    assert copia.a_dict() == e.a_dict()
    assert copia.estado == EstadoEspecie.ELIMINADA and copia.contar() == 0
    assert copia.color == "#aa3300" and copia.dieta == Dieta.CARNIVORO
