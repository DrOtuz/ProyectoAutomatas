"""Seccion de configuracion de Ecosistema.

Los valores los define Ecosistema a partir de la tabla de parametros de la especificacion.
Cada parametro se declara con `campo(valor, minimo=..., maximo=...)`, igual que en app.py.

Aqui solo van parametros. Las clases (Casilla, Mapa, GestorEventos, AutomataFuego) viven en
src/simulador/ecosistema/ y leen estas secciones (RNF-06).
"""

from __future__ import annotations

from dataclasses import dataclass

from simulador.configuracion.base import validarSeccion


@dataclass(frozen=True)
class ConfiguracionEcosistema:
    def __post_init__(self):
        validarSeccion(self)


EVENTOS = {
    "lambda": {
        "primavera": {"sequia": 0.15, "lluvia": 0.50, "foco": 0.20},
        "verano": {"sequia": 0.50, "lluvia": 0.15, "foco": 1.00},
        "otono": {"sequia": 0.10, "lluvia": 0.75, "foco": 0.10},
        "invierno": {"sequia": 0.10, "lluvia": 0.40, "foco": 0.05},
    },
    "duracion": {"sequia": (0.3, 0.6), "lluvia": (0.10, 0.24)},
    "modificador_humedad": {"sequia": -0.35, "lluvia": 0.35},
    "factor_crecimiento": {"sequia": 0.3, "lluvia": 1.5},
    "delta_temperatura_sequia": 3.0,
    "multiplicador_foco_sequia": 3.0,
    "factor_lluvia_fuego": 0.3,
    "probabilidad_apagar_llama": 0.30,
}


CALENDARIO = {
    "ticks_por_estacion": 500,
    "ticks_por_dia": 24,
    "amplitud_dia": 3.0,
    "estaciones": ("primavera", "verano", "otono", "invierno"),
    "por_estacion": {
        "primavera": {"temperatura_base": 20.0, "factor_humedad": 1.0, "factor_crecimiento": 1.2, "factor_inflamabilidad": 0.8},
        "verano": {"temperatura_base": 30.0, "factor_humedad": 0.7, "factor_crecimiento": 0.8, "factor_inflamabilidad": 1.5},
        "otono": {"temperatura_base": 18.0, "factor_humedad": 1.0, "factor_crecimiento": 1.0, "factor_inflamabilidad": 1.0},
        "invierno": {"temperatura_base": 10.0, "factor_humedad": 0.9, "factor_crecimiento": 0.3, "factor_inflamabilidad": 0.5},
    },
}


# Valores marcados "provisional" no salen de la especificacion que tengo a la vista:
# confirmarlos contra la tabla A.6 y calibrarlos en las semanas 7 a 9.
FUEGO = {
    # ticks que una casilla permanece en llamas antes de pasar a quemada (RF-34)
    "duracion_llamas": {"pasto": 3, "arbol": 8},
    # ticks que una casilla quemada tarda en volver a tierra (RF-26)
    "ticks_para_regenerar": 150,
    # probabilidad base por vecina en llamas y por tick, segun la vegetacion de la casilla
    # que podria prenderse (RF-33). Provisional. Bajados de 0.30/0.20 porque con eso 7 de cada 10
    # incendios quemaban casi todo el mapa; con estos, la mitad se apaga casi enseguida y los
    # grandes queman hasta un tercio (medido en 20 semillas, mapa de lagos y arboledas).
    "probabilidad_propagacion": {"pasto": 0.12, "arbol": 0.08},
    # cuanto reduce la humedad la probabilidad: factor = max(0, 1 - peso * humedad). Provisional.
    "peso_humedad": 1.0,
    # factor de temperatura = max(0, 1 + sensibilidad * (T - referencia)). Provisional.
    "temperatura_referencia": 20.0,
    "sensibilidad_temperatura": 0.02,
    # vecinas que cuentan para la propagacion: 8 (con diagonales) o 4. Provisional.
    "vecindad": 8,
    # radio maximo (distancia de Chebyshev) del incendio provocado a mano (RF-32)
    "radio_manual_maximo": 3,
}


# Crecimiento de la vegetacion, alimento por casilla y humedad. NO viene del plan de A:
# lo agrego el trabajo de integracion para poder cerrar el bucle con Vida. Los valores de
# alimento son los que Vida le propuso a A (pasto 30 u que regenera 1 u/tick, arbol 60 u
# que regenera 2 u/tick). El resto es provisional y A debe confirmarlo o reemplazarlo.
VEGETACION = {
    "alimento_maximo": {"pasto": 30.0, "arbol": 60.0},
    "regeneracion": {"pasto": 0.5, "arbol": 1.0},
    # probabilidad por tick de pasar de tierra a pasto y de pasto a arbol (con nutrientes 50
    # y crecimiento 1.0)
    "probabilidad_crecer": {"tierra": 0.002, "pasto": 0.0005},
    # la humedad base de una casilla baja con la distancia al agua hasta este radio
    "radio_humedad": 5,
    # que tan rapido sigue la humedad a su valor objetivo (0 a 1 por tick)
    "inercia_humedad": 0.1,
    # nutrientes iniciales del suelo (0 a 100)
    "nutrientes_iniciales": 50,
}
