"""Modulo de interfaz grafica de usuario en PySide6."""

from simulador.app.interfaz.dialogos import (
    confirmarEliminarSimulacion,
    confirmarMapaSinAgua,
    mostrarSimulacionNoEncontrada,
)
from simulador.app.interfaz.ventana.ventana_simulacion import VentanaSimulacion

__all__ = [
    "VentanaSimulacion",
    "confirmarEliminarSimulacion",
    "confirmarMapaSinAgua",
    "mostrarSimulacionNoEncontrada",
]
