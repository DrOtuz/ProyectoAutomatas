"""Flujo completo sin ventanas: almacenamiento SQLite + Ejecutor (hilo) + motor real."""
import time

import numpy as np

from simulador.app.almacenamiento import AlmacenamientoSqlite
from simulador.app.aplicacion import abrirMotor, crearMotor, crearYGuardar, mapaInicial
from simulador.app.ejecutor.ejecutor import Ejecutor
from simulador.contratos.avisos import EspecieExtinguida
from simulador.contratos.comandos import CrearEspecie, ExtinguirEspecie, FijarNutrientes
from simulador.contratos.instantanea import EstadoCasilla


def esperar(condicion, limite=20.0):
    fin = time.monotonic() + limite
    while time.monotonic() < fin:
        if condicion():
            return True
        time.sleep(0.02)
    return False


def test_el_mapa_inicial_es_valido_y_reproducible():
    t = mapaInicial(3)
    assert t.shape == (100, 100) and t.dtype == np.uint8
    assert (t == int(EstadoCasilla.agua)).any() and (t == int(EstadoCasilla.arbol)).any()
    assert (mapaInicial(3) == t).all() and not (mapaInicial(4) == t).all()


def test_crear_correr_guardar_cerrar_y_cargar(tmp_path):
    almacenamiento = AlmacenamientoSqlite(tmp_path / "biblioteca.db")
    try:
        motor, resumen = crearYGuardar(almacenamiento, "Prueba", semilla=2, velocidad=30)
        ejecutor = Ejecutor(motor, velocidad=30, almacenamiento=almacenamiento, simulacion_id=resumen.simulacion_id)
        ejecutor.iniciar()
        ejecutor.enviar(CrearEspecie("Conejos", 40, "herbivoro"))
        ejecutor.enviar(CrearEspecie("Lobos", 4, "carnivoro", (2.0, 1.5, 6.0)))
        ejecutor.enviar(FijarNutrientes(70))
        ejecutor.reanudar()
        assert esperar(lambda: ejecutor.obtenerInstantanea().tick >= 15)
        instantanea = ejecutor.obtenerInstantanea()
        assert {e.nombre for e in instantanea.especies} == {"Conejos", "Lobos"}
        assert instantanea.nutrientes == 70 and instantanea.total_criaturas > 0
        assert ejecutor.tomarErrores() == []

        ejecutor.enviar(ExtinguirEspecie(2))
        assert esperar(lambda: any(isinstance(a, EspecieExtinguida) for a in ejecutor.tomarAvisos()))

        ejecutor.pausar()  # al pausar se guarda
        assert esperar(lambda: ejecutor.ultimo_tick_guardado >= 15)
        ejecutor.detener()
        assert ejecutor.fallo is None

        guardado = abrirMotor(almacenamiento, resumen.simulacion_id)
        assert guardado.tick == ejecutor.ultimo_tick_guardado
        assert {e.nombre for e in guardado.obtenerInstantanea().especies} == {"Conejos", "Lobos"}
        antes = guardado.huellaEstado()
        guardado.avanzar()
        assert guardado.tick == ejecutor.ultimo_tick_guardado + 1 and guardado.huellaEstado() != antes
    finally:
        almacenamiento.cerrar()


def test_dos_motores_con_la_misma_semilla_dan_la_misma_huella():
    a, b = crearMotor(semilla=9), crearMotor(semilla=9)
    for m in (a, b):
        m.aplicar(CrearEspecie("Conejos", 20))
        for _ in range(5):
            m.avanzar()
    assert a.huellaEstado() == b.huellaEstado()


def test_agregar_criaturas_con_el_ejecutor_en_pausa_se_ve_sin_reanudar():
    from simulador.contratos.comandos import AgregarCriaturas

    m = crearMotor(semilla=5)
    e = Ejecutor(m, velocidad=30)  # arranca en pausa
    e.iniciar()
    e.enviar(CrearEspecie("Conejos", 10))
    assert esperar(lambda: e.obtenerInstantanea().total_criaturas == 10)
    e.enviar(AgregarCriaturas(1, 15))
    assert esperar(lambda: e.obtenerInstantanea().total_criaturas == 25)
    assert e.obtenerInstantanea().tick == 0 and e.en_pausa
    e.enviar(AgregarCriaturas(99, 1))  # especie inexistente: el error llega a la interfaz
    assert esperar(lambda: len(e.tomarErrores()) == 1)
    e.detener()
