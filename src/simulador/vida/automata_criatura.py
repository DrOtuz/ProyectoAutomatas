"""AutomataCriatura: la maquina de estados que decide y ejecuta el turno.

Un solo automata sirve a todas las criaturas: no guarda datos de ninguna (todo
queda en `Criatura`). Para mirar y actuar usa dos cosas:

  * el `MapaPuerto` (comida, fuego, casillas transitables), y
  * un `ContextoVida` (las demas criaturas y como moverse/reproducirse), que
    `Poblacion` implementa. Asi el automata se prueba con un contexto falso.

Turno de una criatura (Poblacion ya llamo `iniciar_tick()` a todas al empezar
el tick):

    si ya actuo este tick (la pareja de una reproduccion): solo paga y envejece
    si no: percibir -> elegir estado -> actuar -> pagar metabolismo -> envejecer

Prioridad: HUIR > BUSCAR_ALIMENTO o BUSCAR_PAREJA > EXPLORAR.

Comer es como capturar una pieza en ajedrez (plantas y presas): si el objetivo
esta a una distancia menor o igual a los pasos del tick, la criatura entra a su
casilla y se lo come en ese mismo tick.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from random import Random
from typing import Callable, Optional, Protocol, runtime_checkable

from .config import ConfigVida
from .criatura import Criatura
from .percepcion import distancia, paso_alejando, paso_aleatorio, paso_hacia
from .puertos import TIPO_COMIDA, TIPO_FUEGO, MapaPuerto
from .tipos import INTENCION_PAREJA, Estado, Objetivo, Pos, TipoObjetivo


@runtime_checkable
class ContextoVida(Protocol):
    """Lo que el automata necesita de la poblacion (la implementa Poblacion)."""

    def criaturas_en(self, pos: Pos) -> list[Criatura]:
        """Criaturas en una casilla (pueden incluir muertas de este tick)."""
        ...

    def criaturas_en_radio(self, pos: Pos, radio: int) -> list[Criatura]:
        """Criaturas a distancia de Chebyshev <= radio (incluye la que esta en `pos`)."""
        ...

    def ocupacion(self, pos: Pos) -> int:
        """Criaturas vivas en la casilla, mas las crias que van a nacer ahi este tick."""
        ...

    def mover(self, criatura: Criatura, pos: Pos) -> None:
        """Mueve a la criatura (actualiza su posicion y el indice por casilla)."""
        ...

    def reproducir(self, madre: Criatura, padre: Criatura, mapa: MapaPuerto) -> bool:
        """Intenta que nazca una cria. Si falla (sin cupo o sin casilla) devuelve
        False y no cobra nada."""
        ...


@dataclass
class Percepcion:
    """Todo lo que una criatura ve dentro de su radio de vision."""

    amenazas: list[Objetivo] = field(default_factory=list)  # criaturas peligrosas
    fuegos: list[Pos] = field(default_factory=list)  # casillas en llamas
    plantas: list[Objetivo] = field(default_factory=list)  # comida del mapa
    presas: list[Objetivo] = field(default_factory=list)  # presas elegibles
    parejas: list[Objetivo] = field(default_factory=list)  # parejas elegibles

    @property
    def hay_amenaza(self) -> bool:
        return bool(self.amenazas or self.fuegos)


class AutomataCriatura:
    def __init__(self, cfg: ConfigVida, rng: Random) -> None:
        self.cfg = cfg
        self.rng = rng

    # --- el turno completo ----------------------------------------------------------

    def turno(
        self,
        criatura: Criatura,
        mapa: MapaPuerto,
        ctx: ContextoVida,
        temperatura: float,
    ) -> None:
        """Un turno completo. No hace nada si la criatura ya esta muerta."""
        if not criatura.viva:
            return
        if not criatura.turno_hecho:
            percepcion = self.percibir(criatura, mapa, ctx)
            estado, objetivo = self.elegir_estado(criatura, percepcion)
            criatura.estado = estado
            self.actuar(criatura, estado, objetivo, percepcion, mapa, ctx)
        # El metabolismo se cobra al final: el costo de moverse depende de si
        # se movio en este tick. La pareja de una reproduccion tambien paga.
        criatura.cobrar_metabolismo(temperatura)
        criatura.envejecer()

    # --- percepcion -----------------------------------------------------------------

    def _es_libre(
        self, criatura: Criatura, mapa: MapaPuerto, ctx: ContextoVida
    ) -> Callable[[Pos], bool]:
        """Casilla a la que `criatura` puede entrar: dentro del mapa, transitable,
        sin fuego y con cupo (MAX_POR_CASILLA)."""

        def libre(pos: Pos) -> bool:
            x, y = pos
            if not mapa.en_limites(x, y) or not mapa.es_transitable(x, y):
                return False
            if mapa.hay_fuego(x, y):
                return False
            return self._ocupantes(criatura, pos, ctx) < self.cfg.MAX_POR_CASILLA

        return libre

    @staticmethod
    def _ocupantes(c: Criatura, pos: Pos, ctx: ContextoVida) -> int:
        """Otras criaturas (vivas o por nacer) en la casilla, sin contar a `c`."""
        return ctx.ocupacion(pos) - (1 if c.pos == pos else 0)

    def percibir(self, c: Criatura, mapa: MapaPuerto, ctx: ContextoVida) -> Percepcion:
        """Todo lo visible dentro de `c.stats.radio_entero()`."""
        x, y = c.pos
        radio = c.stats.radio_entero()
        p = Percepcion()

        p.fuegos = list(mapa.buscar_en_radio(x, y, radio, TIPO_FUEGO))

        for otra in ctx.criaturas_en_radio(c.pos, radio):
            if otra is c or not otra.viva:
                continue
            d = distancia(c.pos, otra.pos)
            if otra.es_amenaza_para(c):
                p.amenazas.append(Objetivo(TipoObjetivo.AMENAZA, otra.pos, otra, 0.0, d))
            if c.puede_cazar(otra):
                p.presas.append(
                    Objetivo(TipoObjetivo.PRESA, otra.pos, otra, c.ganancia_presa(otra), d)
                )
            if self._es_pareja_elegible(c, otra):
                p.parejas.append(Objetivo(TipoObjetivo.PAREJA, otra.pos, otra, 0.0, d))

        if c.puede_comer_planta():
            factor = c.eficiencia_planta() / c.stats.tamano  # ganancia % por unidad u
            maximo = self.cfg.MAX_POR_CASILLA
            px, py = c.pos
            for pos in mapa.buscar_en_radio(x, y, radio, TIPO_COMIDA):
                cx, cy = pos
                biomasa = mapa.biomasa_en(cx, cy)
                if biomasa <= 0 or mapa.hay_fuego(cx, cy):
                    continue
                # no se puede entrar a una casilla sin cupo
                if ctx.ocupacion(pos) - (1 if pos == c.pos else 0) >= maximo:
                    continue
                d = max(abs(cx - px), abs(cy - py))
                p.plantas.append(Objetivo(TipoObjetivo.PLANTA, pos, None, factor * biomasa, d))
        return p

    @staticmethod
    def _es_pareja_elegible(c: Criatura, otra: Criatura) -> bool:
        """Misma especie, que quiera pareja (e >= 70 con histeresis) y con energia
        para pagar. Se usa la intencion y no el estado: el estado BUSCAR_PAREJA
        solo se activa al ver a una pareja, asi que dos criaturas que se buscan
        nunca se encontrarian si se exigiera el estado del otro."""
        return (
            otra.viva
            and otra.especie == c.especie
            and otra.quiere_pareja()
            and not otra.turno_hecho
            and otra.puede_pagar_reproduccion()
        )

    # --- decision -------------------------------------------------------------------

    def elegir_estado(
        self, c: Criatura, p: Percepcion
    ) -> tuple[Estado, Optional[Objetivo]]:
        """Decide el estado y el objetivo. Prioridad HUIR > comer/pareja > EXPLORAR.

        La histeresis (pareja con e >= 70, alimento con e < 50) vive en
        `Criatura.actualizar_intencion`. EXPLORAR conserva la intencion y vuelve
        al estado correspondiente cuando aparece un objetivo visible.
        """
        intencion = c.actualizar_intencion()
        if p.hay_amenaza:
            return Estado.HUIR, None
        if intencion == INTENCION_PAREJA:
            pareja = self.elegir_pareja(c, p)
            if pareja is not None:
                return Estado.BUSCAR_PAREJA, pareja
            return Estado.EXPLORAR, None
        comida = self.elegir_objetivo_comida(c, p)
        if comida is not None:
            return Estado.BUSCAR_ALIMENTO, comida
        return Estado.EXPLORAR, None

    @staticmethod
    def puntuar_comida(c: Criatura, objetivo: Objetivo) -> float:
        """ganancia / (distancia + 1): prefiere lo que mas da y mas cerca esta."""
        return objetivo.ganancia / (objetivo.distancia + 1)

    def elegir_objetivo_comida(self, c: Criatura, p: Percepcion) -> Optional[Objetivo]:
        """El objetivo de mayor puntaje entre plantas y presas elegibles."""
        candidatos = p.plantas + p.presas
        if not candidatos:
            return None
        return max(
            candidatos,
            key=lambda o: (self.puntuar_comida(c, o), o.ganancia, -o.distancia),
        )

    @staticmethod
    def elegir_pareja(c: Criatura, p: Percepcion) -> Optional[Objetivo]:
        """La pareja elegible mas cercana (desempata por id, para ser determinista)."""
        if not p.parejas:
            return None
        return min(p.parejas, key=lambda o: (o.distancia, o.criatura.id))  # type: ignore[union-attr]

    # --- acciones -------------------------------------------------------------------

    def actuar(
        self,
        c: Criatura,
        estado: Estado,
        objetivo: Optional[Objetivo],
        p: Percepcion,
        mapa: MapaPuerto,
        ctx: ContextoVida,
    ) -> None:
        if estado == Estado.HUIR:
            self.actuar_huir(c, p, mapa, ctx)
        elif estado == Estado.BUSCAR_ALIMENTO and objetivo is not None:
            self.actuar_alimento(c, objetivo, mapa, ctx)
        elif estado == Estado.BUSCAR_PAREJA and objetivo is not None:
            self.actuar_pareja(c, objetivo, mapa, ctx)
        else:
            self.actuar_explorar(c, mapa, ctx)

    def actuar_huir(self, c: Criatura, p: Percepcion, mapa: MapaPuerto, ctx: ContextoVida) -> None:
        """Da `pasos_tick` pasos, cada uno el que mas aumenta la distancia a la amenaza."""
        amenazas = [o.pos for o in p.amenazas] + list(p.fuegos)
        destino = paso_alejando(c.pos, amenazas, c.pasos_tick, self._es_libre(c, mapa, ctx))
        if destino != c.pos:
            ctx.mover(c, destino)

    def actuar_alimento(
        self, c: Criatura, objetivo: Objetivo, mapa: MapaPuerto, ctx: ContextoVida
    ) -> None:
        """Captura su comida (planta o presa) en este tick si le alcanza el paso;
        si no, avanza hacia ella. Con una planta bajo los pies, come sin moverse."""
        libre = self._es_libre(c, mapa, ctx)
        d = distancia(c.pos, objetivo.pos)
        es_presa = objetivo.tipo == TipoObjetivo.PRESA

        if d <= c.pasos_tick:
            if es_presa:
                # d-1 pasos hasta quedar al lado y un ultimo paso a su casilla
                llegada = paso_hacia(c.pos, objetivo.pos, d - 1, libre) if d > 1 else c.pos
                alcanzable = distancia(llegada, objetivo.pos) <= 1
            else:
                llegada = paso_hacia(c.pos, objetivo.pos, d, libre)
                alcanzable = llegada == objetivo.pos
            if alcanzable:
                if c.pos != objetivo.pos:
                    ctx.mover(c, objetivo.pos)
                self._comer(c, objetivo, mapa)
                return
            if llegada != c.pos:  # un obstaculo corta el camino: avanza lo que pueda
                ctx.mover(c, llegada)
            return

        destino = paso_hacia(c.pos, objetivo.pos, c.pasos_tick, libre)
        if destino != c.pos:
            ctx.mover(c, destino)

    @staticmethod
    def _comer(c: Criatura, objetivo: Objetivo, mapa: MapaPuerto) -> None:
        if objetivo.tipo == TipoObjetivo.PRESA and objetivo.criatura is not None:
            c.comer_presa(objetivo.criatura)
        else:
            c.comer_planta(mapa.consumir_biomasa(*objetivo.pos))

    def actuar_pareja(
        self, c: Criatura, objetivo: Objetivo, mapa: MapaPuerto, ctx: ContextoVida
    ) -> None:
        """Si la pareja esta a distancia <= 1, intenta reproducirse (sin moverse);
        si no, avanza hacia ella. Si la reproduccion falla, se queda donde esta."""
        pareja = objetivo.criatura
        if pareja is None:
            return
        if distancia(c.pos, pareja.pos) <= 1:
            ctx.reproducir(c, pareja, mapa)
            return
        destino = paso_hacia(c.pos, pareja.pos, c.pasos_tick, self._es_libre(c, mapa, ctx))
        if destino != c.pos:
            ctx.mover(c, destino)

    def actuar_explorar(self, c: Criatura, mapa: MapaPuerto, ctx: ContextoVida) -> None:
        """Pasos al azar que tienden a conservar la direccion (inercia)."""
        libre = self._es_libre(c, mapa, ctx)
        pos, direccion = c.pos, c.direccion
        for _ in range(c.pasos_tick):
            nueva, nueva_direccion = paso_aleatorio(
                pos, direccion, self.cfg.INERCIA_EXPLORAR, self.rng, libre
            )
            if nueva == pos:  # sin casillas libres alrededor
                direccion = (0, 0)
                break
            pos, direccion = nueva, nueva_direccion
        if pos != c.pos:
            ctx.mover(c, pos)
        c.direccion = direccion  # conserva la direccion del ultimo paso
