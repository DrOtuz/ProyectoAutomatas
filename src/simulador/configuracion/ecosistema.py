"""Seccion de configuracion de Ecosistema.

Los valores los define Ecosistema a partir de la tabla de parametros de la especificacion.
Cada parametro se declara con `campo(valor, minimo=..., maximo=...)`, igual que en app.py.
"""

from __future__ import annotations

from dataclasses import dataclass

from simulador.configuracion.base import validarSeccion
from simulador.contratos.instantanea import EstadoCasilla

tick_actual = 0
ticks_para_regenerar=150

def getTickActual():
    return tick_actual

@dataclass(frozen=True)
class ConfiguracionEcosistema:
    def __post_init__(self):
        validarSeccion(self)
@dataclass(frozen=True)
class Casilla:

    def __post_init__(self, tipo_casilla:EstadoCasilla, coordenada:tuple):
        self.tipo:EstadoCasilla = tipo_casilla
        self.humedad = 0
        self.coordenada = coordenada
        self.alimento = 0
        self.tick_quemada = 0
        
    def getTipo(self) -> EstadoCasilla:
        """Obtiene el tipo de la casilla"""
        return self.tipo
    def getHumedad(self)->float:
        """Obtiene la humedad presente en la casilla"""
        return self.humedad #cambiar dependiente al tipo de dato de humedad

    def quemar(self)->None: 
        """Cambia el estado de una casilla a quemado"""
        self.tick_quemada = tick_actual
        self.tipo = EstadoCasilla['quemada']
    def regenerar(self):
        """En caso de estar quemada, cambia el estado de una casilla a tierra"""
        if (self.getTipo()==EstadoCasilla['quemada'] and getTickActual() - self.tick_quemada > ticks_para_regenerar):self.tipo = EstadoCasilla['tierra']
    def evolucionar(self):
        """Evoluciona de  tierra a pasto o de pasto a arbol, no tiene restricciones por el momento"""
        if (self.getTipo()==EstadoCasilla['tierra']):self.tipo = EstadoCasilla['pasto'] #posiblemente meter restricciones luego
        if (self.getTipo()==EstadoCasilla['pasto']):self.tipo = EstadoCasilla['arbol']#posiblemente meter restricciones luego
    def involucionar(self):
        """Involuciona de  pasto a tierra  o de arbol a pasto , no tiene restricciones por el momento"""
        if (self.getTipo()==EstadoCasilla['pasto']):self.tipo = EstadoCasilla['tierra']#posiblemente meter restricciones luego
        if (self.getTipo()==EstadoCasilla['arbol']):self.tipo = EstadoCasilla['pasto']#posiblemente meter restricciones luego