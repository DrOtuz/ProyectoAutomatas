"""Errores de contrato entre subgrupos."""


class ErrorSimulador(Exception):
    """Error base del simulador. Todo error propio del motor hereda de esta clase."""


class ComandoInvalido(ErrorSimulador):
    """El comando trae valores invalidos. No se cambio nada en el motor."""


class ComandoNoSoportado(ErrorSimulador):
    """El motor todavia no implementa este comando."""

class NombreInvalido(ErrorSimulador):
    """El nombre de la simulacion no cumple las reglas o ya existe."""


class SimulacionNoEncontrada(ErrorSimulador):
    """No existe una simulacion guardada con ese identificador."""