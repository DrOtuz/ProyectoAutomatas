"""Pruebas del motor integrado: A (mapa, clima, fuego) + B (vida) detras del contrato Motor."""
import numpy as np
import pytest

from simulador.contratos.avisos import (
    CupoAlcanzado,
    EspecieExtinguida,
    EventoNaturalIniciado,
    EventoNaturalTerminado,
    OrigenEvento,
)
from simulador.contratos.comandos import (
    AgregarCriaturas,
    CancelarEvento,
    CrearEspecie,
    EliminarCriaturas,
    EliminarEspecie,
    ExtinguirEspecie,
    FijarNutrientes,
    ProvocarEvento,
    TipoEvento,
)
from simulador.contratos.errores import ComandoInvalido, ErrorSimulador
from simulador.contratos.instantanea import EstadoCasilla, Instantanea
from simulador.contratos.motor import Motor
from simulador.integracion import MapaVida, SimuladorEcosistema
from simulador.vida.puertos import MapaPuerto

PASTO, AGUA, ARBOL, TIERRA = (int(EstadoCasilla[n]) for n in ("pasto", "agua", "arbol", "tierra"))


def terreno(base=PASTO):
    t = np.full((100, 100), base, dtype=np.uint8)
    t[:, 0] = AGUA
    return t


def motor(semilla=1, **kw):
    return SimuladorEcosistema(terreno(**kw), semilla=semilla)


def avanzar(m, n):
    avisos = []
    for _ in range(n):
        avisos += m.avanzar()
    return avisos


def con_especies(semilla=1):
    m = motor(semilla)
    m.aplicar(CrearEspecie("Conejos", 40, "herbivoro"))
    m.aplicar(CrearEspecie("Lobos", 4, "carnivoro", genes=(2.0, 1.5, 6.0)))
    m.avanzar()
    return m


# ---------- contrato ----------


def test_cumple_el_contrato_motor_y_el_mapa_cumple_el_puerto_de_vida():
    m = motor()
    assert isinstance(m, Motor)
    assert isinstance(MapaVida(m.mapa), MapaPuerto)


def test_la_instantanea_tiene_la_forma_del_contrato():
    m = con_especies()
    i = m.obtenerInstantanea()
    assert isinstance(i, Instantanea)
    assert i.terreno.shape == (100, 100) and i.terreno.dtype == np.uint8
    assert i.criaturas.dtype == np.int32 and i.criaturas.shape[1] == 3
    assert i.total_criaturas == 44 and i.cupo == 500
    assert not i.terreno.flags.writeable and not i.criaturas.flags.writeable
    assert [(e.nombre, e.poblacion, e.extinguida) for e in i.especies] == [("Conejos", 40, False), ("Lobos", 4, False)]
    assert set(i.criaturas[:, 2]) == {1, 2}
    assert (i.terreno[:, 0] == AGUA).all()


def test_cada_avance_suma_un_tick_y_la_instantanea_lo_refleja():
    m = motor()
    assert m.obtenerInstantanea().tick == 0
    avanzar(m, 5)
    assert m.obtenerInstantanea().tick == 5


def test_las_criaturas_no_pisan_agua_ni_se_apilan():
    m = con_especies()
    avanzar(m, 25)
    c = m.obtenerInstantanea().criaturas
    assert not (m.obtenerInstantanea().terreno[c[:, 1], c[:, 0]] == AGUA).any()
    assert len({(x, y) for x, y, _ in c.tolist()}) == len(c)
    assert m.poblacion.verificar_consistencia() == []


# ---------- comandos ----------


def test_un_comando_tiene_efecto_en_el_tick_siguiente():
    m = motor()
    m.aplicar(FijarNutrientes(80))
    assert m.obtenerInstantanea().nutrientes == 50
    m.avanzar()
    assert m.obtenerInstantanea().nutrientes == 80


@pytest.mark.parametrize(
    "comando",
    [
        FijarNutrientes(101),
        FijarNutrientes(-1),
        CrearEspecie("", 5),
        CrearEspecie("x" * 31, 5),
        CrearEspecie("A", 0),
        CrearEspecie("A", 5, dieta="vegano"),
        CrearEspecie("A", 5, genes=(9.0, 1.0, 5.0)),
        CrearEspecie("A", 5, genes=(1.0, 1.0)),
        AgregarCriaturas(99, 5),
        EliminarCriaturas(99, 5),
        ExtinguirEspecie(99),
        EliminarEspecie(99),
        ProvocarEvento(TipoEvento.incendio, 5, 5, radio=9),
        ProvocarEvento(TipoEvento.incendio, 0, 5, radio=0),  # agua
        CancelarEvento(TipoEvento.sequia),
    ],
)
def test_los_comandos_invalidos_se_rechazan_sin_cambiar_nada(comando):
    m = con_especies()
    antes = m.huellaEstado()
    with pytest.raises(ComandoInvalido):
        m.aplicar(comando)
    assert m.huellaEstado() == antes


def test_el_nombre_no_se_repite_ni_siquiera_si_esta_pendiente_o_fue_eliminada():
    m = motor()
    m.aplicar(CrearEspecie("Conejos", 5))
    with pytest.raises(ComandoInvalido):
        m.aplicar(CrearEspecie("conejos", 5))
    m.avanzar()
    m.aplicar(EliminarEspecie(1))
    m.avanzar()
    with pytest.raises(ComandoInvalido):
        m.aplicar(CrearEspecie("Conejos", 5))
    assert m.obtenerInstantanea().especies == ()


def test_crear_especie_usa_la_dieta_y_los_genes_pedidos():
    m = motor()
    m.aplicar(CrearEspecie("Gigantes", 10, "omnivoro", genes=(3.0, 0.5, 10.0)))
    m.avanzar()
    e = m.poblacion.especies["Gigantes"]
    assert e.dieta.value == "omnivoro" and e.plantilla.tamano == 3.0 and e.plantilla.vision == 10.0


def test_cada_especie_recibe_un_color_distinto_de_la_paleta():
    m = motor()
    for i in range(12):
        m.aplicar(CrearEspecie(f"E{i}", 2))
    m.avanzar()
    assert sorted(e.color for e in m.obtenerInstantanea().especies) == list(range(12))


def test_agregar_eliminar_extinguir_y_eliminar_especie():
    m = con_especies()
    m.aplicar(AgregarCriaturas(1, 10))
    m.avanzar()
    assert m.poblacion.especies["Conejos"].contar() >= 50 - 5  # algunas pueden morir ese tick
    antes = m.poblacion.especies["Conejos"].contar()
    m.aplicar(EliminarCriaturas(1, 7))
    m.avanzar()
    assert m.poblacion.especies["Conejos"].contar() <= antes - 7 + 8  # nacimientos posibles

    m.aplicar(ExtinguirEspecie(2))
    avisos = m.avanzar()
    assert any(isinstance(a, EspecieExtinguida) and a.nombre == "Lobos" and a.especie_id == 2 for a in avisos)
    info = {e.nombre: e for e in m.obtenerInstantanea().especies}
    assert info["Lobos"].extinguida and info["Lobos"].poblacion == 0
    m.aplicar(AgregarCriaturas(2, 3))  # una extinguida se puede repoblar
    info = {e.nombre: e for e in m.obtenerInstantanea().especies}
    assert info["Lobos"].poblacion == 3 and not info["Lobos"].extinguida
    m.aplicar(ExtinguirEspecie(2))
    m.avanzar()

    m.aplicar(EliminarEspecie(2))
    m.avanzar()
    assert [e.nombre for e in m.obtenerInstantanea().especies] == ["Conejos"]
    assert "Lobos" not in m.poblacion.historial


def test_aviso_de_cupo_se_da_una_sola_vez():
    m = motor()
    m.aplicar(CrearEspecie("Conejos", 490))
    avisos = avanzar(m, 3)
    m.aplicar(AgregarCriaturas(1, 200))
    avisos += avanzar(m, 3)
    cupos = [a for a in avisos if isinstance(a, CupoAlcanzado)]
    assert len(cupos) == 1 and cupos[0].cupo == 500
    assert m.obtenerInstantanea().total_criaturas <= 500


# ---------- eventos y fuego ----------


def test_sequia_y_lluvia_se_provocan_y_terminan_con_avisos():
    m = motor()
    m.aplicar(ProvocarEvento(TipoEvento.sequia))
    with pytest.raises(ComandoInvalido):
        m.aplicar(ProvocarEvento(TipoEvento.sequia))
    avisos = m.avanzar()
    assert EventoNaturalIniciado(TipoEvento.sequia, OrigenEvento.manual, 1) in avisos
    assert [e.tipo for e in m.obtenerInstantanea().eventos] == [TipoEvento.sequia]
    m.aplicar(CancelarEvento(TipoEvento.sequia))
    avisos = m.avanzar()
    assert EventoNaturalTerminado(TipoEvento.sequia, 2, cancelado=True) in avisos
    assert m.obtenerInstantanea().eventos == ()


def test_un_incendio_manual_quema_el_mapa_y_mata_a_las_criaturas_en_llamas():
    m = motor()
    m.aplicar(CrearEspecie("Conejos", 300))
    m.avanzar()
    m.aplicar(ProvocarEvento(TipoEvento.incendio, 50, 50, radio=2))
    avisos = m.avanzar()
    assert any(isinstance(a, EventoNaturalIniciado) and a.tipo == TipoEvento.incendio for a in avisos)
    i = m.obtenerInstantanea()
    assert (i.terreno == int(EstadoCasilla.llamas)).sum() == 25
    assert any(e.tipo == TipoEvento.incendio and e.casillas_en_llamas == 25 for e in i.eventos)
    llamas = np.argwhere(i.terreno == int(EstadoCasilla.llamas))  # (y, x)
    ocupadas = {(x, y) for x, y, _ in i.criaturas.tolist()}
    assert not ocupadas & {(int(x), int(y)) for y, x in llamas}  # nadie sobrevive dentro del fuego
    m.aplicar(CancelarEvento(TipoEvento.incendio))
    fin = avanzar(m, 3)
    assert any(isinstance(a, EventoNaturalTerminado) and a.tipo == TipoEvento.incendio for a in fin)
    assert (m.obtenerInstantanea().terreno == int(EstadoCasilla.quemada)).any()


def test_cancelar_un_incendio_lo_marca_cancelado():
    m = motor()
    m.aplicar(ProvocarEvento(TipoEvento.incendio, 50, 50, radio=1))
    m.avanzar()
    m.aplicar(CancelarEvento(TipoEvento.incendio))
    avisos = m.avanzar()
    assert EventoNaturalTerminado(TipoEvento.incendio, 2, cancelado=True) in avisos


def test_el_pasto_comido_vuelve_a_crecer():
    m = motor()
    m.avanzar()
    c = m.mapa.casilla(10, 10)
    consumido = MapaVida(m.mapa, m.fuego).consumir_biomasa(10, 10)
    assert consumido > 0 and c.alimento == 0
    avanzar(m, 40)
    assert c.alimento > 0


# ---------- determinismo y guardado ----------


def test_misma_semilla_y_comandos_dan_la_misma_huella():
    a, b = con_especies(3), con_especies(3)
    avanzar(a, 25)
    avanzar(b, 25)
    assert a.huellaEstado() == b.huellaEstado()
    assert con_especies(4).huellaEstado() != con_especies(3).huellaEstado()


def test_guardar_y_cargar_da_la_misma_huella_y_sigue_igual():
    a = con_especies(5)
    a.aplicar(ProvocarEvento(TipoEvento.incendio, 40, 40, radio=1))
    a.aplicar(CrearEspecie("Pendiente", 3))  # queda pendiente al guardar
    avanzar(a, 5)
    a.aplicar(CrearEspecie("Otra", 3))
    datos = a.aEstado()
    assert isinstance(datos, bytes)
    b = SimuladorEcosistema.desdeEstado(datos)
    assert b.huellaEstado() == a.huellaEstado()
    assert avanzar(a, 20) == avanzar(b, 20)
    assert a.huellaEstado() == b.huellaEstado()
    assert a.poblacion.historial["Conejos"].serie("poblacion") == b.poblacion.historial["Conejos"].serie("poblacion")


def test_un_estado_danado_se_rechaza_con_un_error_del_simulador():
    with pytest.raises(ErrorSimulador):
        SimuladorEcosistema.desdeEstado(b"no es un estado")


def test_con_500_criaturas_el_estado_cabe_en_20_mb():
    m = motor()
    m.aplicar(CrearEspecie("Conejos", 500))
    avanzar(m, 3)
    assert m.obtenerInstantanea().total_criaturas > 450
    assert len(m.aEstado()) < 20 * 1024 * 1024


def test_el_historial_se_llena_y_se_consulta_por_id():
    m = con_especies()
    avanzar(m, 10)
    serie = m.serie(1, "poblacion")
    assert len(serie) == 11 and serie[-1][0] == m.tick


def test_un_mapa_dibujado_solo_con_tierra_y_agua_recibe_vegetacion_inicial():
    t = np.full((100, 100), TIERRA, dtype=np.uint8)
    t[40:60, 40:60] = AGUA
    m = SimuladorEcosistema(t, semilla=3)
    ter = m.obtenerInstantanea().terreno
    assert (ter == PASTO).sum() > 1000 and (ter == ARBOL).sum() > 0
    assert (ter[40:60, 40:60] == AGUA).all()
    assert SimuladorEcosistema(t, semilla=3).huellaEstado() == m.huellaEstado()
    m.aplicar(CrearEspecie("Conejos", 30))
    avanzar(m, 20)
    assert m.obtenerInstantanea().total_criaturas > 0


def test_un_incendio_sin_foco_elige_una_casilla_con_vegetacion():
    m = motor()
    m.aplicar(ProvocarEvento(TipoEvento.incendio))  # lo que manda el boton de la interfaz
    avisos = m.avanzar()
    assert any(isinstance(a, EventoNaturalIniciado) and a.tipo == TipoEvento.incendio for a in avisos)
    assert (m.obtenerInstantanea().terreno == int(EstadoCasilla.llamas)).sum() == 1
    m.aplicar(CancelarEvento(TipoEvento.incendio))
    assert EventoNaturalTerminado(TipoEvento.incendio, 2, cancelado=True) in m.avanzar()
    assert m.obtenerInstantanea().eventos == ()


def test_sin_vegetacion_no_hay_incendio_posible():
    m = SimuladorEcosistema(np.full((100, 100), TIERRA, dtype=np.uint8), semilla=1)
    m.mapa.casilla(5, 5).tipo = EstadoCasilla.tierra
    for c in m.mapa.casillas():
        c.tipo = EstadoCasilla.tierra
    with pytest.raises(ComandoInvalido):
        m.aplicar(ProvocarEvento(TipoEvento.incendio))


def test_provocar_y_cancelar_lluvia_y_sequia_desde_los_botones():
    m = motor()
    for tipo in (TipoEvento.lluvia, TipoEvento.sequia):
        m.aplicar(ProvocarEvento(tipo))
        m.avanzar()
        assert tipo in [e.tipo for e in m.obtenerInstantanea().eventos]
        m.aplicar(CancelarEvento(tipo))
        m.avanzar()
        assert tipo not in [e.tipo for e in m.obtenerInstantanea().eventos]


def test_las_ordenes_sobre_especies_se_ven_de_inmediato_incluso_en_pausa():
    m = motor()
    m.aplicar(CrearEspecie("Conejos", 10))
    assert m.obtenerInstantanea().total_criaturas == 10 and m.tick == 0
    m.aplicar(AgregarCriaturas(1, 15))
    assert m.obtenerInstantanea().total_criaturas == 25
    m.aplicar(EliminarCriaturas(1, 5))
    assert m.obtenerInstantanea().total_criaturas == 20
    m.aplicar(ExtinguirEspecie(1))
    assert m.obtenerInstantanea().especies[0].extinguida
    assert any(isinstance(a, EspecieExtinguida) for a in m.avanzar())  # el aviso no se pierde


def test_agregar_con_el_cupo_lleno_se_rechaza_con_un_mensaje_y_con_poco_cupo_agrega_las_que_caben():
    m = motor()
    m.aplicar(CrearEspecie("Conejos", 495))
    m.aplicar(AgregarCriaturas(1, 50))
    assert m.obtenerInstantanea().total_criaturas == 500
    with pytest.raises(ComandoInvalido, match="500"):
        m.aplicar(AgregarCriaturas(1, 1))
    with pytest.raises(ComandoInvalido):
        m.aplicar(CrearEspecie("Otra", 1))
