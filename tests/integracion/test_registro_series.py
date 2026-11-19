"""RegistroSeries: series por tick para las graficas, sin ventanas."""
import time

from simulador.app.aplicacion import crearMotor
from simulador.app.ejecutor.ejecutor import Ejecutor
from simulador.app.registro_series import METRICAS, RegistroSeries
from simulador.contratos.comandos import CrearEspecie


def test_el_registro_guarda_un_punto_por_tick_con_promedios():
    m = crearMotor(semilla=1)
    m.aplicar(CrearEspecie("Conejos", 20))
    reg = RegistroSeries()
    for _ in range(10):
        m.avanzar()
        reg.registrar(m.obtenerInstantanea())
    ticks, valores = reg.serie(1)
    assert ticks == list(range(1, 11))
    assert set(valores) == set(METRICAS) and all(len(v) == 10 for v in valores.values())
    assert all(v is not None and v > 0 for v in valores["tamano"] + valores["energia"])
    assert reg.serie(99) == ([], {k: [] for k in METRICAS})


def test_registrar_dos_veces_el_mismo_tick_no_duplica():
    m = crearMotor(semilla=1)
    m.aplicar(CrearEspecie("Conejos", 5))
    m.avanzar()
    reg = RegistroSeries()
    reg.registrar(m.obtenerInstantanea())
    reg.registrar(m.obtenerInstantanea())
    assert reg.serie(1)[0] == [1]


def test_sembrar_con_el_historial_de_una_simulacion_cargada_y_seguir():
    m = crearMotor(semilla=2)
    m.aplicar(CrearEspecie("Conejos", 20))
    for _ in range(5):
        m.avanzar()
    reg = RegistroSeries()
    reg.sembrar(m.seriesPorEspecie())
    assert reg.serie(1)[0] == [1, 2, 3, 4, 5]
    m.avanzar()
    reg.registrar(m.obtenerInstantanea())
    assert reg.serie(1)[0] == [1, 2, 3, 4, 5, 6]


def test_se_limita_a_max_puntos_conservando_lo_reciente():
    m = crearMotor(semilla=3)
    m.aplicar(CrearEspecie("Conejos", 5))
    reg = RegistroSeries(max_puntos=20)
    for _ in range(60):
        m.avanzar()
        reg.registrar(m.obtenerInstantanea())
    ticks, valores = reg.serie(1)
    assert len(ticks) <= 21 and ticks[-1] == 60 and ticks == sorted(ticks)
    assert all(len(v) == len(ticks) for v in valores.values())


def test_el_ejecutor_alimenta_el_registro_en_cada_tick():
    m = crearMotor(semilla=4)
    reg = RegistroSeries()
    e = Ejecutor(m, velocidad=30)
    e.alAvanzar(reg.registrar)
    e.enviar(CrearEspecie("Conejos", 10))
    e.iniciar()
    e.reanudar()
    fin = time.monotonic() + 20
    while time.monotonic() < fin and (not reg.serie(1)[0] or reg.serie(1)[0][-1] < 6):
        time.sleep(0.02)
    e.detener()
    ticks, _ = reg.serie(1)
    assert ticks[:6] == [1, 2, 3, 4, 5, 6] and e.fallo is None
