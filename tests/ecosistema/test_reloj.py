"""Pruebas del Reloj. CONFIG es el calendario que usan tambien las pruebas del fuego."""
import math

from simulador.configuracion.ecosistema import CALENDARIO
from simulador.ecosistema.reloj import Reloj

CONFIG = CALENDARIO


def test_el_tick_empieza_en_0_y_avanza_de_a_uno():
    r = Reloj(CONFIG)
    assert r.tick == 0
    assert r.avanzar() == 1 and r.tick == 1


def test_las_estaciones_cambian_cada_ticks_por_estacion():
    r = Reloj(CONFIG)
    n = CONFIG["ticks_por_estacion"]
    vistas = []
    for t in range(4 * n + 1):
        r.tick = t
        vistas.append(r.estacion)
    assert vistas[0] == "primavera" and vistas[n] == "verano"
    assert vistas[2 * n] == "otono" and vistas[3 * n] == "invierno"
    assert vistas[4 * n] == "primavera"


def test_la_temperatura_oscila_alrededor_de_la_base():
    r = Reloj(CONFIG)
    r.tick = CONFIG["ticks_por_dia"] // 4
    base = CONFIG["por_estacion"]["primavera"]["temperatura_base"]
    assert math.isclose(r.temperatura, base + CONFIG["amplitud_dia"])
    r.delta_temperatura = 3.0
    assert math.isclose(r.temperatura, base + CONFIG["amplitud_dia"] + 3.0)


def test_estado_ida_y_vuelta():
    r = Reloj(CONFIG)
    r.tick = 777
    r2 = Reloj(CONFIG)
    r2.cargarEstado(r.aEstado())
    assert r2.tick == 777
