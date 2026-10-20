"""Seccion de configuracion de App: guardado, ejecutor, mapa y editor."""

from __future__ import annotations

from dataclasses import dataclass

from simulador.configuracion.base import ErrorConfiguracion, campo, validarSeccion


@dataclass(frozen=True)
class ConfiguracionApp:
    # Guardado (RF-48, A-DP-06)
    autoguardado_cada_ticks: int = campo(1000, minimo=1, maximo=1_000_000)
    largo_maximo_nombre: int = campo(60, minimo=1, maximo=255)
    # Velocidad del ejecutor (RF-15)
    velocidad_minima: int = campo(1, minimo=1, maximo=1000)
    velocidad_inicial: int = campo(10, minimo=1, maximo=1000)
    velocidad_maxima: int = campo(60, minimo=1, maximo=1000)
    # Mapa (RF-13, RF-20, D-40)
    tamano_casilla_px: int = campo(6, minimo=1, maximo=64)
    zoom_minimo: int = campo(1, minimo=1, maximo=64)
    zoom_maximo: int = campo(8, minimo=1, maximo=64)
    figura_criatura: str = campo(
        "circulo", opciones=("circulo", "cuadrado", "triangulo", "rombo")
    )
    # Editor de mapa (RF-08)
    pasos_deshacer: int = campo(50, minimo=1, maximo=1000)
    pincel_minimo: int = campo(1, minimo=1, maximo=100)
    pincel_maximo: int = campo(5, minimo=1, maximo=100)

    def __post_init__(self):
        validarSeccion(self)
        if not self.velocidad_minima <= self.velocidad_inicial <= self.velocidad_maxima:
            raise ErrorConfiguracion(
                "ConfiguracionApp: se exige velocidad_minima <= velocidad_inicial "
                "<= velocidad_maxima"
            )
        if self.zoom_minimo > self.zoom_maximo:
            raise ErrorConfiguracion("ConfiguracionApp: zoom_minimo no puede superar a zoom_maximo")
        if self.pincel_minimo > self.pincel_maximo:
            raise ErrorConfiguracion(
                "ConfiguracionApp: pincel_minimo no puede superar a pincel_maximo"
            )