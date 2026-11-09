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
EVENTOS = {
    "lambda": {
        "primavera": {"sequia": 0.15, "lluvia": 0.50, "foco": 0.10},
        "verano": {"sequia": 0.50, "lluvia": 0.15, "foco": 0.50},
        "otono": {"sequia": 0.10, "lluvia": 0.75, "foco": 0.05},
        "invierno": {"sequia": 0.10, "lluvia": 0.40, "foco": 0.025},
    },
    "duracion": {"sequia": (0.3, 0.6), "lluvia": (0.10, 0.24)},
    "modificador_humedad": {"sequia": -0.35, "lluvia": 0.35},
    "factor_crecimiento": {"sequia": 0.3, "lluvia": 1.5},
    "delta_temperatura_sequia": 3.0,
    "multiplicador_foco_sequia": 3.0,
}

"""Eventos naturales globales: sequia y lluvia (paso 2 del tick).

Los parametros salen de la seccion EVENTOS de configuracion/ecosistema.py (RNF-06).
Todo el azar sale del generador unico que se pasa al constructor (RNF-05).
"""
from dataclasses import dataclass

TIPOS_CLIMA = ("sequia", "lluvia")


class ErrorSimulador(Exception):
    """Provisional: reemplazar por el error del contrato cuando exista."""


@dataclass
class EventoNatural:
    tipo: str
    origen: str
    tick_inicio: int
    duracion: int
    ticks_restantes: int


class GestorEventos:
    esta_en_sequia: bool
    esta_lloviendo: bool
    eventos_activos: list[EventoNatural]

    def __init__(self, rng, config=None):
        if config is None:
            from simulador.configuracion.ecosistema import EVENTOS

            config = EVENTOS
        self.esta_en_sequia = False
        self.esta_lloviendo = False
        self.eventos_activos = []
        self._rng = rng
        self._config = config
        self._pendientes_provocar: list[str] = []
        self._pendientes_cancelar: list[str] = []

    def cancelarEvento(self, tipo: str) -> None:
        if not self._hayActivo(tipo):
            raise ErrorSimulador(f"No hay evento activo de tipo {tipo}")
        self._pendientes_cancelar.append(tipo)

    def factorCrecimiento(self) -> float:
        return self._config["factor_crecimiento"].get(self._tipoClima(), 1.0)

    def modificadorHumedad(self) -> float:
        return self._config["modificador_humedad"].get(self._tipoClima(), 0.0)

    def modificadorTemperatura(self) -> float:
        if self._hayActivo("sequia"):
            return self._config["delta_temperatura_sequia"]
        return 0.0

    def paso(self, tick: int, estacion: str, ticks_por_estacion: int) -> bool:
        """Paso 2 del tick. Devuelve True si hay foco natural de incendio este tick."""
        # Siempre 5 sorteos, aunque no hagan falta (RNF-05):
        # 0 sequia, 1 lluvia, 2 foco, 3 duracion sequia, 4 duracion lluvia
        sorteos = self._rng.random(5)
        L = ticks_por_estacion

        for evento in self.eventos_activos:
            evento.ticks_restantes -= 1
        self.eventos_activos = [
            e
            for e in self.eventos_activos
            if e.ticks_restantes > 0 and e.tipo not in self._pendientes_cancelar
        ]
        self._pendientes_cancelar.clear()

        for tipo in self._pendientes_provocar:
            self._iniciar(tipo, "manual", tick, sorteos, L)
        self._pendientes_provocar.clear()

        lam = self._config["lambda"][estacion]
        sequia_nueva = False
        if sorteos[0] < lam["sequia"] / L:
            sequia_nueva = self._iniciar("sequia", "natural", tick, sorteos, L)
        if not sequia_nueva and sorteos[1] < lam["lluvia"] / L:
            self._iniciar("lluvia", "natural", tick, sorteos, L)

        self._actualizarBanderas()

        p_foco = lam["foco"] / L
        if self.esta_en_sequia:
            p_foco *= self._config["multiplicador_foco_sequia"]
        return bool(sorteos[2] < p_foco)

    def provocarEvento(self, tipo: str) -> None:
        if tipo not in TIPOS_CLIMA:
            raise ErrorSimulador(f"Tipo de evento invalido: {tipo}")
        if self._hayActivo(tipo):
            raise ErrorSimulador(f"Ya hay un evento activo de tipo {tipo}")
        self._pendientes_provocar.append(tipo)

    def _actualizarBanderas(self) -> None:
        self.esta_en_sequia = self._hayActivo("sequia")
        self.esta_lloviendo = self._hayActivo("lluvia")

    def _hayActivo(self, tipo: str) -> bool:
        return any(e.tipo == tipo for e in self.eventos_activos)

    def _iniciar(self, tipo: str, origen: str, tick: int, sorteos, L: int) -> bool:
        if self._hayActivo(tipo):
            return False
        opuesto = "lluvia" if tipo == "sequia" else "sequia"
        self.eventos_activos = [e for e in self.eventos_activos if e.tipo != opuesto]
        minimo, maximo = self._config["duracion"][tipo]
        u = sorteos[3] if tipo == "sequia" else sorteos[4]
        duracion = max(1, round((minimo + (maximo - minimo) * u) * L))
        self.eventos_activos.append(EventoNatural(tipo, origen, tick, duracion, duracion))
        return True

    def _tipoClima(self):
        for evento in self.eventos_activos:
            if evento.tipo in TIPOS_CLIMA:
                return evento.tipo
        return None
