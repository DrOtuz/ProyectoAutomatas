"""Automata celular de fuego (paso 4 del tick).

Los parametros salen de la seccion FUEGO de configuracion/ecosistema.py (RNF-06).
Todo el azar sale del generador unico del ciclo (RNF-05) y el consumo es fijo: cada tick
se sortean 2 * ancho * alto + 1 numeros, haya fuego o no.

Doble buffer: las llamas que se propagan y las que se apagan se deciden con el estado al
inicio del tick; las casillas que se prenden este tick no se propagan hasta el siguiente.
Se registra con ciclo.registrarPaso(4, automata.paso).
"""
from dataclasses import dataclass, field

from simulador.ecosistema.eventos import ErrorSimulador
from simulador.ecosistema.mapa import ARBOL, LLAMAS, PASTO, QUEMADA

OFFSETS_8 = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))
OFFSETS_4 = ((0, -1), (-1, 0), (1, 0), (0, 1))
NOMBRE_VEGETACION = {PASTO: "pasto", ARBOL: "arbol"}


@dataclass
class Incendio:
    origen: str
    tick_inicio: int
    focos: list = field(default_factory=list)


def _orden(coordenada):
    return (coordenada[1], coordenada[0])


class AutomataFuego:
    incendio: "Incendio | None"
    incendio_terminado: bool
    casillas_tocadas: set

    def __init__(self, mapa, config=None):
        if config is None:
            from simulador.configuracion.ecosistema import FUEGO

            config = FUEGO
        self._config = config
        self._mapa = mapa
        self._offsets = OFFSETS_8 if config["vecindad"] == 8 else OFFSETS_4
        self.incendio = None
        self.incendio_terminado = False
        self.casillas_tocadas = set()
        self._en_llamas: set = set()
        self._quemadas: set = set()
        self._pendientes_provocar: list = []
        self._pendiente_cancelar = False
        self.reconstruirIndice()

    # ---------- ordenes del usuario (RF-28, RF-32, RF-51) ----------

    def provocarIncendio(self, x: int, y: int, radio: int) -> None:
        """Provoca un incendio a mano. Prende las casillas inflamables a distancia <= radio."""
        if not self._mapa.enLimites(x, y):
            raise ErrorSimulador(f"La casilla ({x}, {y}) esta fuera del mapa")
        if not 0 <= radio <= self._config["radio_manual_maximo"]:
            raise ErrorSimulador(f"El radio debe estar entre 0 y {self._config['radio_manual_maximo']}")
        if self.incendio is not None or self._pendientes_provocar:
            raise ErrorSimulador("Ya hay un incendio activo")
        if not self._inflamablesEnRadio(x, y, radio):
            raise ErrorSimulador("No hay casillas inflamables en el area elegida")
        self._pendientes_provocar.append((x, y, radio))

    def cancelarIncendio(self) -> None:
        """Cancela el incendio activo. Sus llamas pasan a quemada al inicio del tick siguiente."""
        if self.incendio is None:
            raise ErrorSimulador("No hay un incendio activo")
        self._pendiente_cancelar = True

    # ---------- paso 4 ----------

    def paso(self, ciclo) -> None:
        tick = ciclo.reloj.tick
        rng = ciclo.rng
        ancho, alto = self._mapa.ancho, self._mapa.alto
        # Siempre el mismo consumo (RNF-05): propagacion, apagado por lluvia y posicion del foco
        sorteo_propagacion = rng.random((alto, ancho))
        sorteo_lluvia = rng.random((alto, ancho))
        sorteo_foco = rng.random()

        self.casillas_tocadas = set()
        self.incendio_terminado = False
        focos_nuevos = []

        if self._pendiente_cancelar:
            self._aplicarCancelacion(tick)

        llamas_previas = sorted(self._en_llamas, key=_orden)
        encendidas = self._propagar(llamas_previas, sorteo_propagacion, ciclo)
        self._avanzarLlamas(llamas_previas, tick, sorteo_lluvia, ciclo.eventos.probabilidadApagarLlama())

        for x, y in encendidas:
            self._encender(x, y, tick)

        for x, y, radio in self._pendientes_provocar:
            for cx, cy in self._inflamablesEnRadio(x, y, radio):
                self._encender(cx, cy, tick)
            focos_nuevos.append(("manual", (x, y)))
        self._pendientes_provocar.clear()

        if ciclo.foco_natural:
            candidatas = [c.coordenada for c in self._mapa.casillas() if c.esInflamable()]
            if candidatas:
                indice = min(int(sorteo_foco * len(candidatas)), len(candidatas) - 1)
                x, y = candidatas[indice]
                self._encender(x, y, tick)
                focos_nuevos.append(("natural", (x, y)))

        self._regenerar(tick)
        self._actualizarIncendio(tick, focos_nuevos)

    # ---------- consultas y estado ----------

    def casillasEnLlamas(self) -> list:
        """Coordenadas (x, y) en llamas, fila por fila. Para el snapshot y la etiqueta de eventos."""
        return sorted(self._en_llamas, key=_orden)

    def hayIncendio(self) -> bool:
        return self.incendio is not None

    def aEstado(self) -> dict:
        """Estado propio del fuego con tipos basicos. Las casillas las guarda el mapa."""
        incendio = None
        if self.incendio is not None:
            incendio = {
                "origen": self.incendio.origen,
                "tick_inicio": self.incendio.tick_inicio,
                "focos": [list(f) for f in self.incendio.focos],
            }
        return {
            "incendio": incendio,
            "pendientes_provocar": [list(p) for p in self._pendientes_provocar],
            "pendiente_cancelar": self._pendiente_cancelar,
        }

    def cargarEstado(self, estado: dict) -> None:
        """Restaura desde aEstado y reconstruye los indices leyendo el mapa ya cargado."""
        datos = estado["incendio"]
        if datos is None:
            self.incendio = None
        else:
            self.incendio = Incendio(
                datos["origen"], datos["tick_inicio"], [tuple(f) for f in datos["focos"]]
            )
        self._pendientes_provocar = [tuple(p) for p in estado["pendientes_provocar"]]
        self._pendiente_cancelar = estado["pendiente_cancelar"]
        self.incendio_terminado = False
        self.casillas_tocadas = set()
        self.reconstruirIndice()

    def reconstruirIndice(self) -> None:
        """Recorre el mapa y rehace los conjuntos de casillas en llamas y quemadas."""
        self._en_llamas = set()
        self._quemadas = set()
        for casilla in self._mapa.casillas():
            if casilla.tipo == LLAMAS:
                self._en_llamas.add(casilla.coordenada)
            elif casilla.tipo == QUEMADA:
                self._quemadas.add(casilla.coordenada)

    # ---------- interno ----------

    def _aplicarCancelacion(self, tick: int) -> None:
        for x, y in sorted(self._en_llamas, key=_orden):
            self._mapa.casilla(x, y).quemar(tick)
            self._quemadas.add((x, y))
            self.casillas_tocadas.add((x, y))
        self._en_llamas.clear()
        self._pendiente_cancelar = False

    def _inflamablesEnRadio(self, x: int, y: int, radio: int) -> list:
        return [
            (cx, cy)
            for cx, cy in self._mapa.casillasEnRadio(x, y, radio)
            if self._mapa.casilla(cx, cy).esInflamable()
        ]

    def _propagar(self, llamas_previas: list, sorteo, ciclo) -> list:
        """Decide que casillas se prenden, leyendo solo el estado al inicio del tick."""
        if not llamas_previas:
            return []
        cfg = self._config
        factor_temperatura = max(
            0.0, 1.0 + cfg["sensibilidad_temperatura"] * (ciclo.reloj.temperatura - cfg["temperatura_referencia"])
        )
        escala = (
            factor_temperatura
            * ciclo.reloj.factoresEstacion()["factor_inflamabilidad"]
            * ciclo.eventos.factorLluviaFuego()
        )
        vecinas_en_llamas = {}
        for x, y in llamas_previas:
            for dx, dy in self._offsets:
                nx, ny = x + dx, y + dy
                if self._mapa.enLimites(nx, ny) and self._mapa.casilla(nx, ny).esInflamable():
                    vecinas_en_llamas[(nx, ny)] = vecinas_en_llamas.get((nx, ny), 0) + 1
        encendidas = []
        for (nx, ny) in sorted(vecinas_en_llamas, key=_orden):
            casilla = self._mapa.casilla(nx, ny)
            base = cfg["probabilidad_propagacion"][NOMBRE_VEGETACION[casilla.tipo]]
            factor_humedad = max(0.0, 1.0 - cfg["peso_humedad"] * casilla.humedad)
            p_vecina = min(1.0, max(0.0, base * factor_humedad * escala))
            p = 1.0 - (1.0 - p_vecina) ** vecinas_en_llamas[(nx, ny)]
            if sorteo[ny, nx] < p:
                encendidas.append((nx, ny))
        return encendidas

    def _avanzarLlamas(self, llamas_previas: list, tick: int, sorteo, p_apagar: float) -> None:
        """Las llamas que cumplieron su duracion o apago la lluvia pasan a quemada."""
        for x, y in llamas_previas:
            casilla = self._mapa.casilla(x, y)
            duracion = self._config["duracion_llamas"][NOMBRE_VEGETACION[casilla.vegetacion_previa]]
            if tick - casilla.tick_inicio_llamas >= duracion or sorteo[y, x] < p_apagar:
                casilla.quemar(tick)
                self._en_llamas.discard((x, y))
                self._quemadas.add((x, y))
                self.casillas_tocadas.add((x, y))

    def _encender(self, x: int, y: int, tick: int) -> None:
        casilla = self._mapa.casilla(x, y)
        if casilla.esInflamable():
            casilla.encender(tick)
            self._en_llamas.add((x, y))
            self.casillas_tocadas.add((x, y))

    def _regenerar(self, tick: int) -> None:
        for x, y in sorted(self._quemadas, key=_orden):
            if self._mapa.casilla(x, y).regenerar(tick, self._config["ticks_para_regenerar"]):
                self._quemadas.discard((x, y))
                self.casillas_tocadas.add((x, y))

    def _actualizarIncendio(self, tick: int, focos_nuevos: list) -> None:
        if self._en_llamas:
            if self.incendio is None and focos_nuevos:
                self.incendio = Incendio(focos_nuevos[0][0], tick)
            if self.incendio is not None:
                self.incendio.focos.extend(coordenada for _, coordenada in focos_nuevos)
        elif self.incendio is not None:
            self.incendio = None
            self.incendio_terminado = True
