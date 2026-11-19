"""Integracion: une Ecosistema (A), Vida (B) y la aplicacion (C) detras del contrato Motor.

Este paquete no importa simulador.app (el motor no importa la aplicacion).
"""
from simulador.integracion.mapa_vida import MapaVida
from simulador.integracion.simulador_ecosistema import SimuladorEcosistema

__all__ = ["MapaVida", "SimuladorEcosistema"]
