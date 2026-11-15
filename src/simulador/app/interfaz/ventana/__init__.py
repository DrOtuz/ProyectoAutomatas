"""Componentes de la ventana principal de simulacion."""

from simulador.app.interfaz.ventana.barra_estado import BarraEstado
from simulador.app.interfaz.ventana.inspector import InspectorWidget
from simulador.app.interfaz.ventana.panel_eventos import PanelEventos
from simulador.app.interfaz.ventana.ventana_simulacion import VentanaSimulacion
from simulador.app.interfaz.ventana.visor_mapa import VisorMapa

__all__ = [
    "BarraEstado",
    "InspectorWidget",
    "PanelEventos",
    "VentanaSimulacion",
    "VisorMapa",
]
