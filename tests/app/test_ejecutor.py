import threading
import time

import pytest

from simulador.app.almacenamiento.memoria import AlmacenamientoMemoria
from simulador.app.ejecutor.ejecutor import Ejecutor
from simulador.configuracion.app import ConfiguracionApp
from simulador.contratos.comandos import FijarNutrientes
from simulador.contratos.errores import ComandoInvalido
from simulador.contratos.motor_falso import MotorFalso


class MotorRoto(MotorFalso):
    def avanzar(self):
        raise RuntimeError("motor roto")


def esperarHasta(condicion, limite=3.0):
    fin = time.monotonic() + limite
    while time.monotonic() < fin:
        if condicion():
            return True
        time.sleep(0.005)
    return False


@pytest.fixture
def crearEjecutor():
    creados = []

    def crear(motor=None, velocidad=60):
        ejecutor = Ejecutor(motor or MotorFalso(), velocidad)
        creados.append(ejecutor)
        ejecutor.iniciar()
        return ejecutor

    yield crear
    for ejecutor in creados:
        ejecutor.detener()


@pytest.mark.requisito("RF-14")
def test_empieza_en_pausa_sin_avanzar(crearEjecutor):
    ejecutor = crearEjecutor()
    time.sleep(0.1)
    assert ejecutor.en_pausa
    assert ejecutor.obtenerInstantanea().tick == 0


@pytest.mark.requisito("RF-14")
def test_reanudar_avanza_y_pausar_detiene(crearEjecutor):
    ejecutor = crearEjecutor()
    ejecutor.reanudar()
    assert esperarHasta(lambda: ejecutor.obtenerInstantanea().tick >= 3)
    ejecutor.pausar()
    time.sleep(0.1)  # deja terminar el tick en curso
    tick = ejecutor.obtenerInstantanea().tick
    time.sleep(0.2)
    assert ejecutor.obtenerInstantanea().tick == tick


@pytest.mark.requisito("RF-15")
def test_velocidad_fuera_de_rango_se_rechaza(crearEjecutor):
    ejecutor = crearEjecutor()
    configuracion = ConfiguracionApp()
    with pytest.raises(ValueError):
        ejecutor.fijarVelocidad(configuracion.velocidad_minima - 1)
    with pytest.raises(ValueError):
        ejecutor.fijarVelocidad(configuracion.velocidad_maxima + 1)
    with pytest.raises(ValueError):
        Ejecutor(MotorFalso(), 0)


@pytest.mark.requisito("RF-15")
def test_velocidad_regula_el_ritmo(crearEjecutor):
    ejecutor = crearEjecutor(velocidad=20)
    ejecutor.reanudar()
    time.sleep(0.5)
    ejecutor.pausar()
    assert 4 <= ejecutor.obtenerInstantanea().tick <= 16  # esperado: cerca de 10
    ejecutor.fijarVelocidad(30)
    assert ejecutor.velocidad == 30


@pytest.mark.requisito("RF-15")
def test_sin_velocidad_arranca_con_la_inicial_de_la_configuracion():
    configuracion = ConfiguracionApp(velocidad_minima=2, velocidad_inicial=7, velocidad_maxima=30)
    ejecutor = Ejecutor(MotorFalso(), configuracion=configuracion)
    assert ejecutor.velocidad == 7


@pytest.mark.requisito("RF-15")
def test_los_limites_de_velocidad_salen_de_la_configuracion():
    configuracion = ConfiguracionApp(velocidad_minima=2, velocidad_inicial=7, velocidad_maxima=30)
    ejecutor = Ejecutor(MotorFalso(), configuracion=configuracion)
    ejecutor.fijarVelocidad(30)
    with pytest.raises(ValueError):
        ejecutor.fijarVelocidad(31)
    with pytest.raises(ValueError):
        ejecutor.fijarVelocidad(1)


@pytest.mark.requisito("RNF-03")
@pytest.mark.requisito("RNF-12")
def test_leer_la_instantanea_no_espera_al_motor_lento(crearEjecutor):
    ejecutor = crearEjecutor(MotorFalso(retardo=0.3))
    ejecutor.reanudar()
    time.sleep(0.05)
    inicio = time.monotonic()
    for _ in range(20):
        ejecutor.obtenerInstantanea()
    assert time.monotonic() - inicio < 0.1


@pytest.mark.requisito("RF-19")
def test_comando_en_pausa_rige_en_el_tick_siguiente(crearEjecutor):
    ejecutor = crearEjecutor()
    ejecutor.enviar(FijarNutrientes(80))
    time.sleep(0.1)
    assert ejecutor.obtenerInstantanea().nutrientes == 50  # sigue en pausa
    ejecutor.reanudar()
    assert esperarHasta(lambda: ejecutor.obtenerInstantanea().nutrientes == 80)


@pytest.mark.requisito("RF-19")
def test_comando_invalido_queda_en_los_errores(crearEjecutor):
    ejecutor = crearEjecutor()
    ejecutor.enviar(FijarNutrientes(500))
    errores = []

    def hayError():
        errores.extend(ejecutor.tomarErrores())
        return bool(errores)

    assert esperarHasta(hayError)
    assert isinstance(errores[0], ComandoInvalido)


@pytest.mark.requisito("RNF-03")
def test_fallo_del_motor_detiene_el_hilo_sin_colgar(crearEjecutor):
    ejecutor = crearEjecutor(MotorRoto())
    ejecutor.reanudar()
    assert esperarHasta(lambda: ejecutor.fallo is not None)
    assert isinstance(ejecutor.fallo, RuntimeError)
    assert esperarHasta(lambda: not ejecutor.activo)


@pytest.mark.requisito("RNF-03")
def test_detener_termina_el_hilo(crearEjecutor):
    ejecutor = crearEjecutor()
    assert ejecutor.activo
    ejecutor.detener()
    assert not ejecutor.activo


@pytest.mark.requisito("RF-48")
def test_autoguardado_al_pausar():
    almacenamiento = AlmacenamientoMemoria()
    motor = MotorFalso()
    resumen = almacenamiento.crear("Test", motor.aEstado(), tick=0, velocidad=60)
    ejecutor = Ejecutor(
        motor, velocidad=60, almacenamiento=almacenamiento, simulacion_id=resumen.simulacion_id
    )
    ejecutor.iniciar()
    ejecutor.reanudar()
    assert esperarHasta(lambda: ejecutor.obtenerInstantanea().tick >= 3)
    ejecutor.pausar()
    assert esperarHasta(
        lambda: almacenamiento.cargar(resumen.simulacion_id) is not None
        and ejecutor.ultimo_tick_guardado >= 3
    )
    ejecutor.detener()


@pytest.mark.requisito("RF-48")
def test_autoguardado_al_detener():
    almacenamiento = AlmacenamientoMemoria()
    motor = MotorFalso()
    resumen = almacenamiento.crear("Test", motor.aEstado(), tick=0, velocidad=60)
    ejecutor = Ejecutor(
        motor, velocidad=60, almacenamiento=almacenamiento, simulacion_id=resumen.simulacion_id
    )
    ejecutor.iniciar()
    ejecutor.reanudar()
    assert esperarHasta(lambda: ejecutor.obtenerInstantanea().tick >= 3)
    tick_al_parar = ejecutor.obtenerInstantanea().tick
    ejecutor.detener()
    assert ejecutor.ultimo_tick_guardado >= tick_al_parar


@pytest.mark.requisito("RF-48")
def test_autoguardado_periodico_cada_n_ticks():
    configuracion = ConfiguracionApp(autoguardado_cada_ticks=4)
    almacenamiento = AlmacenamientoMemoria()
    motor = MotorFalso()
    resumen = almacenamiento.crear("Test", motor.aEstado(), tick=0, velocidad=60)
    ejecutor = Ejecutor(
        motor,
        velocidad=60,
        configuracion=configuracion,
        almacenamiento=almacenamiento,
        simulacion_id=resumen.simulacion_id,
    )
    ejecutor.iniciar()
    ejecutor.reanudar()
    assert esperarHasta(lambda: ejecutor.ultimo_tick_guardado >= 4)
    ejecutor.detener()


@pytest.mark.requisito("RF-48")
def test_solicitar_guardado_manual():
    almacenamiento = AlmacenamientoMemoria()
    motor = MotorFalso()
    resumen = almacenamiento.crear("Test", motor.aEstado(), tick=0, velocidad=60)
    ejecutor = Ejecutor(
        motor, velocidad=60, almacenamiento=almacenamiento, simulacion_id=resumen.simulacion_id
    )
    ejecutor.iniciar()
    ejecutor.solicitarGuardado()
    assert esperarHasta(lambda: ejecutor.ultimo_tick_guardado == 0)
    ejecutor.detener()


class MotorConRastreoDeHilo(MotorFalso):
    def __init__(self):
        super().__init__()
        self.hilo_a_estado = None

    def aEstado(self) -> bytes:
        self.hilo_a_estado = threading.current_thread().name
        return super().aEstado()


@pytest.mark.requisito("RF-48")
def test_a_estado_solo_se_llama_desde_el_hilo_del_ejecutor():
    almacenamiento = AlmacenamientoMemoria()
    motor = MotorConRastreoDeHilo()
    resumen = almacenamiento.crear("Test", motor.aEstado(), tick=0, velocidad=60)
    motor.hilo_a_estado = None  # resetear tras crear
    ejecutor = Ejecutor(
        motor, velocidad=60, almacenamiento=almacenamiento, simulacion_id=resumen.simulacion_id
    )
    ejecutor.iniciar()
    ejecutor.solicitarGuardado()
    assert esperarHasta(lambda: motor.hilo_a_estado is not None)
    assert motor.hilo_a_estado == "ejecutor"
    ejecutor.detener()
