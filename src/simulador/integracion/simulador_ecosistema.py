"""SimuladorEcosistema: el Motor real. Une el mapa y el clima de A con la poblacion de B.

Orden de un tick (avanzar):
  1. se aplican los comandos pendientes del usuario;
  2. CicloTick de A: reloj, eventos, fuego (paso 4) y vegetacion (paso 5);
  3. las criaturas que quedaron en una casilla en llamas mueren (Poblacion.eliminar_en);
  4. Vida actualiza a todas las criaturas (Poblacion.actualizar) y registra el historial.
Despues se arman los avisos del tick.

Hay dos generadores al azar: el de A (numpy) y el de Vida (random.Random). Los dos salen de
la misma semilla y se guardan con el estado.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import zlib
from random import Random

import numpy as np

from simulador.contratos import comandos as cmd
from simulador.contratos.avisos import (
    CupoAlcanzado,
    EspecieExtinguida,
    EventoNaturalIniciado,
    EventoNaturalTerminado,
    OrigenEvento,
)
from simulador.contratos.comandos import TipoEvento
from simulador.contratos.errores import (
    ComandoInvalido,
    ComandoNoSoportado,
    ErrorSimulador,
)
from simulador.contratos.instantanea import (
    Estacion,
    InfoEspecie,
    InfoEvento,
    Instantanea,
)
from simulador.contratos.motor import Aviso, Comando, Motor
from simulador.ecosistema.ciclo import CicloTick
from simulador.ecosistema.eventos import GestorEventos
from simulador.ecosistema.fuego import AutomataFuego
from simulador.ecosistema.mapa import Mapa
from simulador.ecosistema.reloj import Reloj
from simulador.ecosistema.vegetacion import Vegetacion
from simulador.integracion.mapa_vida import MapaVida
from simulador.vida.config import ConfigVida
from simulador.vida.estadisticas import Estadisticas
from simulador.vida.poblacion import EXTINCION, EventoVida, Poblacion
from simulador.vida.tipos import Dieta, EstadoEspecie

VERSION_ESTADO = 1
PALETA = 12  # colores de la paleta oficial (RF-55); el color de una especie es un indice
TAMANO_MAPA = 100
MAX_NOMBRE = 30
_COMANDOS = {c.__name__: c for c in (
    cmd.FijarNutrientes, cmd.ProvocarEvento, cmd.CancelarEvento, cmd.CrearEspecie,
    cmd.AgregarCriaturas, cmd.EliminarCriaturas, cmd.ExtinguirEspecie, cmd.EliminarEspecie,
)}  # fmt: skip


def _codificar(comando) -> dict:
    datos = dataclasses.asdict(comando)
    if isinstance(comando, (cmd.ProvocarEvento, cmd.CancelarEvento)):
        datos["tipo"] = comando.tipo.value
    return {"clase": type(comando).__name__, "datos": datos}


def _decodificar(registro: dict):
    clase = _COMANDOS[registro["clase"]]
    datos = dict(registro["datos"])
    if "tipo" in datos:
        datos["tipo"] = TipoEvento(datos["tipo"])
    if datos.get("genes") is not None:
        datos["genes"] = tuple(datos["genes"])
    return clase(**datos)


class SimuladorEcosistema(Motor):
    def __init__(
        self,
        terreno: np.ndarray | None = None,
        semilla: int = 0,
        cfg_vida: ConfigVida | None = None,
        *,
        _mapa: Mapa | None = None,
    ) -> None:
        from simulador.configuracion.ecosistema import (
            CALENDARIO,
            EVENTOS,
            FUEGO,
            VEGETACION,
        )

        self.semilla = int(semilla)
        self.cfg_vida = cfg_vida or ConfigVida()
        if _mapa is not None:
            self.mapa = _mapa
        elif terreno is not None:
            if terreno.shape != (TAMANO_MAPA, TAMANO_MAPA):
                raise ComandoInvalido(f"El terreno debe ser de {TAMANO_MAPA} x {TAMANO_MAPA}.")
            self.mapa = Mapa.desdeTerreno(terreno, VEGETACION["alimento_maximo"])
        else:
            self.mapa = Mapa.desdeTerreno(
                np.full((TAMANO_MAPA, TAMANO_MAPA), 2, dtype=np.uint8), VEGETACION["alimento_maximo"]
            )

        self._rng = np.random.default_rng(self.semilla)
        self.ciclo = CicloTick(self._rng, Reloj(CALENDARIO), GestorEventos(self._rng, EVENTOS))
        self.fuego = AutomataFuego(self.mapa, FUEGO)
        self.vegetacion = Vegetacion(self.mapa, VEGETACION)
        if _mapa is None and not any(c.esInflamable() for c in self.mapa.casillas()):
            # mapa dibujado a mano (solo tierra y agua): se siembra la vegetacion inicial
            self.vegetacion.sembrar(np.random.default_rng(self.semilla + 1))
        self.ciclo.registrarPaso(4, self.fuego.paso)
        self.ciclo.registrarPaso(5, self.vegetacion.paso)

        self.poblacion = Poblacion(self.cfg_vida, Random(self.semilla))
        self.poblacion.suscribir(self._alEventoVida)
        self._mapa_vida = MapaVida(self.mapa, self.fuego)

        self._ids: dict[str, int] = {}  # nombre de especie -> id
        self._nombres: dict[int, str] = {}  # id -> nombre
        self._colores: dict[int, int] = {}
        self._bloqueados: set[str] = set()  # nombres en minusculas de especies eliminadas
        self._siguiente_id = 1
        self._pendientes: list = []
        self._avisos: list[Aviso] = []
        self._cupo_lleno = False
        self._incendio_activo = False
        self._incendio_cancelado = False
        self._cache_terreno: tuple[int, np.ndarray] | None = None

    # ================================================================================
    # Motor
    # ================================================================================

    @property
    def tick(self) -> int:
        return self.ciclo.reloj.tick

    def avanzar(self) -> list[Aviso]:
        pendientes, self._pendientes = self._pendientes, []
        for comando in pendientes:
            self._ejecutar(comando)

        self.ciclo.ejecutarTick()
        tick = self.tick
        self._avisosDeEventos(tick)

        for x, y in self.fuego.casillasEnLlamas():
            self.poblacion.eliminar_en(x, y)
        self._mapa_vida.sincronizar()
        self.poblacion.actualizar(self._mapa_vida, self.ciclo.reloj.temperatura)
        self._avisosDeCupo(tick)
        avisos, self._avisos = self._avisos, []
        return avisos

    def aplicar(self, comando: Comando) -> None:
        """Valida y encola. Eventos e incendios se encolan en sus propios gestores, que ya
        los aplican al inicio del tick siguiente."""
        try:
            self._validar(comando)
        except ErrorSimulador:
            raise
        except (ValueError, TypeError) as error:
            raise ComandoInvalido(str(error)) from error
        if isinstance(comando, cmd.ProvocarEvento):
            self._provocar(comando)
        elif isinstance(comando, cmd.CancelarEvento):
            self._cancelar(comando)
        elif isinstance(comando, cmd.FijarNutrientes):
            self._pendientes.append(comando)
        else:
            # Las ordenes sobre especies y criaturas se aplican ya, no al tick siguiente: asi se
            # ven tambien con la simulacion en pausa (la ventana de especies lo promete).
            self._ejecutar(comando)

    def obtenerInstantanea(self) -> Instantanea:
        if self._cache_terreno is None or self._cache_terreno[0] != self.tick:
            self._cache_terreno = (self.tick, self.mapa.aTerreno())
        terreno = self._cache_terreno[1].copy()
        vivas = sorted(self.poblacion.criaturas_vivas(), key=lambda c: c.id)
        criaturas = np.array([(*c.pos, self._ids[c.especie]) for c in vivas], dtype=np.int32).reshape(-1, 3)
        especies = tuple(self._infoEspecie(n, e) for n, e in self.poblacion.especies.items()
                         if e.estado != EstadoEspecie.ELIMINADA)  # fmt: skip
        eventos = [InfoEvento(TipoEvento(t), ticks_restantes=r) for t, r in sorted(self.ciclo.eventos.activos.items())]
        if self.fuego.hayIncendio():
            eventos.append(InfoEvento(TipoEvento.incendio, casillas_en_llamas=len(self.fuego.casillasEnLlamas())))
        return Instantanea(
            tick=self.tick,
            estacion=Estacion(self.ciclo.reloj.estacion),
            temperatura=float(self.ciclo.reloj.temperatura),
            nutrientes=self.vegetacion.nutrientes,
            terreno=terreno,
            criaturas=criaturas,
            especies=especies,
            eventos=tuple(eventos),
            cupo=self.cfg_vida.MAX_CRIATURAS,
        )

    def _infoEspecie(self, nombre: str, especie) -> InfoEspecie:
        ultimo = self.poblacion.historial[nombre].ultimo() if nombre in self.poblacion.historial else None
        promedios = ultimo or {}
        return InfoEspecie(
            especie_id=self._ids[nombre],
            nombre=nombre,
            color=self._colores[self._ids[nombre]],
            poblacion=especie.contar(),
            extinguida=especie.estado == EstadoEspecie.EXTINTA,
            tamano=promedios.get("tamano"),
            velocidad=promedios.get("velocidad"),
            vision=promedios.get("vision"),
            energia=promedios.get("energia"),
        )

    # ---------- consultas extra para la interfaz (no son parte de Motor) ----------

    def serie(self, especie_id: int, metrica: str) -> list[tuple[int, float | None]]:
        """Serie del historial de una especie: [(tick, valor), ...]. Ver Vida: HistorialEspecie."""
        return self.poblacion.historial[self._nombres[especie_id]].serie(metrica)

    def seriesPorEspecie(self) -> dict[int, dict[str, list[tuple[int, float | None]]]]:
        """Todo el historial guardado, por id de especie: para sembrar las graficas al abrir o
        cargar una simulacion. Solo se llama antes de iniciar el hilo del Ejecutor."""
        from simulador.vida.historial import METRICAS

        return {
            id_: {m: self.poblacion.historial[nombre].serie(m) for m in METRICAS}
            for nombre, id_ in self._ids.items()
            if nombre in self.poblacion.historial
        }

    def historialDe(self, especie_id: int):
        return self.poblacion.historial[self._nombres[especie_id]]

    def idDe(self, nombre: str) -> int:
        return self._ids[nombre]

    # ================================================================================
    # estado
    # ================================================================================

    def _estado(self) -> dict:
        return {
            "version": VERSION_ESTADO,
            "semilla": self.semilla,
            "mapa": self.mapa.aEstado(),
            "reloj": self.ciclo.reloj.aEstado(),
            "eventos": self.ciclo.eventos.aEstado(),
            "fuego": self.fuego.aEstado(),
            "vegetacion": self.vegetacion.aEstado(),
            "rng": self._rng.bit_generator.state,
            "poblacion": self.poblacion.a_dict(),
            "ids": self._ids,
            "colores": {str(k): v for k, v in self._colores.items()},
            "bloqueados": sorted(self._bloqueados),
            "siguiente_id": self._siguiente_id,
            "pendientes": [_codificar(c) for c in self._pendientes],
            "cupo_lleno": self._cupo_lleno,
            "incendio_activo": self._incendio_activo,
            "incendio_cancelado": self._incendio_cancelado,
        }

    def _bytesCanonicos(self) -> bytes:
        return json.dumps(self._estado(), sort_keys=True, separators=(",", ":")).encode("utf-8")

    def aEstado(self) -> bytes:
        return zlib.compress(self._bytesCanonicos(), 6)

    def huellaEstado(self) -> str:
        return hashlib.sha256(self._bytesCanonicos()).hexdigest()

    @classmethod
    def desdeEstado(cls, estado: bytes) -> SimuladorEcosistema:
        try:
            datos = json.loads(zlib.decompress(estado).decode("utf-8"))
        except (zlib.error, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ErrorSimulador("El estado guardado esta danado o no es de este motor.") from error
        if datos.get("version") != VERSION_ESTADO:
            raise ErrorSimulador(f"Version de estado no soportada: {datos.get('version')!r}.")
        cfg = ConfigVida.desde_dict(datos["poblacion"]["cfg"])
        sim = cls(semilla=datos["semilla"], cfg_vida=cfg, _mapa=Mapa.desdeEstado(datos["mapa"]))
        sim.ciclo.reloj.cargarEstado(datos["reloj"])
        sim.ciclo.eventos.cargarEstado(datos["eventos"])
        sim.fuego.cargarEstado(datos["fuego"])
        sim.vegetacion.cargarEstado(datos["vegetacion"])
        sim._rng.bit_generator.state = datos["rng"]
        sim.poblacion = Poblacion.desde_dict(datos["poblacion"], cfg)
        sim.poblacion.suscribir(sim._alEventoVida)
        sim._ids = dict(datos["ids"])
        sim._nombres = {i: n for n, i in sim._ids.items()}
        sim._colores = {int(k): v for k, v in datos["colores"].items()}
        sim._bloqueados = set(datos["bloqueados"])
        sim._siguiente_id = datos["siguiente_id"]
        sim._pendientes = [_decodificar(r) for r in datos["pendientes"]]
        sim._cupo_lleno = datos["cupo_lleno"]
        sim._incendio_activo = datos["incendio_activo"]
        sim._incendio_cancelado = datos["incendio_cancelado"]
        return sim

    # ================================================================================
    # validacion y ejecucion de comandos
    # ================================================================================

    def _nombresEnUso(self) -> set[str]:
        usados = {n.lower() for n, e in self.poblacion.especies.items() if e.estado != EstadoEspecie.ELIMINADA}
        usados |= self._bloqueados
        usados |= {c.nombre.lower() for c in self._pendientes if isinstance(c, cmd.CrearEspecie)}
        return usados

    def _especieViva(self, especie_id: int, activa: bool = False):
        nombre = self._nombres.get(especie_id)
        especie = self.poblacion.especies.get(nombre) if nombre else None
        if especie is None or especie.estado == EstadoEspecie.ELIMINADA:
            raise ComandoInvalido("La especie no existe.")
        if activa and especie.estado == EstadoEspecie.EXTINTA:
            raise ComandoInvalido("La especie esta extinguida.")
        return especie

    def _validar(self, c: Comando) -> None:
        if isinstance(c, cmd.FijarNutrientes):
            if not isinstance(c.nivel, int) or not 0 <= c.nivel <= 100:
                raise ComandoInvalido("Los nutrientes deben estar entre 0 y 100.")
        elif isinstance(c, (cmd.ProvocarEvento, cmd.CancelarEvento)):
            if not isinstance(c.tipo, TipoEvento):
                raise ComandoInvalido("Tipo de evento invalido.")
        elif isinstance(c, cmd.CrearEspecie):
            nombre = c.nombre.strip() if isinstance(c.nombre, str) else ""
            if not nombre or len(nombre) > MAX_NOMBRE:
                raise ComandoInvalido(f"El nombre debe tener de 1 a {MAX_NOMBRE} caracteres.")
            if nombre.lower() in self._nombresEnUso():
                raise ComandoInvalido("Ya existe una especie con ese nombre (o fue eliminada).")
            if not isinstance(c.cantidad, int) or c.cantidad < 1:
                raise ComandoInvalido("La cantidad debe ser al menos 1.")
            self._exigirCupo()
            try:
                Dieta(c.dieta)
            except ValueError as error:
                raise ComandoInvalido(f"Dieta invalida: {c.dieta!r}.") from error
            if c.genes is not None:
                if len(c.genes) != 3:
                    raise ComandoInvalido("Los genes son (tamano, velocidad, vision).")
                self.cfg_vida.comprobar_estadisticas(*c.genes)
        elif isinstance(c, (cmd.AgregarCriaturas, cmd.EliminarCriaturas)):
            self._especieViva(c.especie_id)  # una extinguida puede repoblarse: Vida la reactiva
            if not isinstance(c.cantidad, int) or c.cantidad < 1:
                raise ComandoInvalido("La cantidad debe ser al menos 1.")
            if isinstance(c, cmd.AgregarCriaturas):
                self._exigirCupo()
        elif isinstance(c, (cmd.ExtinguirEspecie, cmd.EliminarEspecie)):
            self._especieViva(c.especie_id)
        else:
            raise ComandoNoSoportado(f"No se reconoce el comando {type(c).__name__}.")

    def _exigirCupo(self) -> None:
        if self.poblacion.total() >= self.cfg_vida.MAX_CRIATURAS:
            raise ComandoInvalido(f"Ya hay {self.cfg_vida.MAX_CRIATURAS} criaturas: no caben mas.")

    def _provocar(self, c: cmd.ProvocarEvento) -> None:
        try:
            if c.tipo == TipoEvento.incendio:
                x, y = (c.foco_x, c.foco_y) if c.foco_x is not None and c.foco_y is not None else self._focoAlAzar()
                self.fuego.provocarIncendio(x, y, c.radio)
            else:
                self.ciclo.eventos.provocarEvento(c.tipo.value)
        except ErrorSimulador as error:
            raise ComandoInvalido(str(error)) from error

    def _focoAlAzar(self) -> tuple[int, int]:
        """Foco para un incendio pedido sin lugar (el boton de la interfaz): una casilla con
        vegetacion elegida al azar. Depende solo de la semilla y del tick, asi que es repetible."""
        candidatas = [c.coordenada for c in self.mapa.casillas() if c.esInflamable()]
        if not candidatas:
            raise ComandoInvalido("No hay vegetacion que se pueda quemar.")
        return candidatas[Random(self.semilla * 7919 + self.tick).randrange(len(candidatas))]

    def _cancelar(self, c: cmd.CancelarEvento) -> None:
        try:
            if c.tipo == TipoEvento.incendio:
                self.fuego.cancelarIncendio()
                self._incendio_cancelado = True
            else:
                self.ciclo.eventos.cancelarEvento(c.tipo.value)
        except ErrorSimulador as error:
            raise ComandoInvalido(str(error)) from error

    def _ejecutar(self, c: Comando) -> None:
        if isinstance(c, cmd.FijarNutrientes):
            self.vegetacion.nutrientes = c.nivel
        elif isinstance(c, cmd.CrearEspecie):
            nombre = c.nombre.strip()
            id_ = self._siguiente_id
            self._siguiente_id += 1
            self._ids[nombre], self._nombres[id_] = id_, nombre
            self._colores[id_] = self._colorLibre()
            plantilla = Estadisticas(*c.genes) if c.genes is not None else None
            self.poblacion.crear_especie(
                nombre, Dieta(c.dieta), c.cantidad, self._mapa_vida,
                plantilla=plantilla, color=str(self._colores[id_]),
            )  # fmt: skip
        elif isinstance(c, cmd.AgregarCriaturas):
            self.poblacion.agregar_individuos(
                self._nombres[c.especie_id], c.cantidad, self._mapa_vida, promedio_actual=c.promedio_actual
            )
        elif isinstance(c, cmd.EliminarCriaturas):
            self.poblacion.eliminar_criaturas(self._nombres[c.especie_id], c.cantidad)
        elif isinstance(c, cmd.ExtinguirEspecie):
            self.poblacion.extinguir_especie(self._nombres[c.especie_id])
        elif isinstance(c, cmd.EliminarEspecie):
            nombre = self._nombres[c.especie_id]
            self.poblacion.eliminar_especie(nombre)
            self.poblacion.historial.eliminar(nombre)
            self._bloqueados.add(nombre.lower())

    def _colorLibre(self) -> int:
        usados = {
            self._colores[self._ids[n]]
            for n, e in self.poblacion.especies.items()
            if e.estado != EstadoEspecie.ELIMINADA and n in self._ids
        }
        for color in range(PALETA):
            if color not in usados:
                return color
        return (self._siguiente_id - 1) % PALETA

    # ================================================================================
    # avisos
    # ================================================================================

    def _alEventoVida(self, evento: EventoVida) -> None:
        if evento.tipo == EXTINCION and evento.especie in self._ids:
            self._avisos.append(EspecieExtinguida(self._ids[evento.especie], evento.especie, evento.tick))

    def _avisosDeEventos(self, tick: int) -> None:
        ev = self.ciclo.eventos
        for tipo, cancelado in ev.terminados:
            self._avisos.append(EventoNaturalTerminado(TipoEvento(tipo), tick, cancelado))
        for tipo, origen in ev.iniciados:
            self._avisos.append(EventoNaturalIniciado(TipoEvento(tipo), OrigenEvento(origen), tick))
        hay = self.fuego.hayIncendio()
        if hay and not self._incendio_activo:
            self._avisos.append(
                EventoNaturalIniciado(TipoEvento.incendio, OrigenEvento(self.fuego.incendio.origen), tick)
            )
        if self.fuego.incendio_terminado:
            self._avisos.append(EventoNaturalTerminado(TipoEvento.incendio, tick, self._incendio_cancelado))
            self._incendio_cancelado = False
        self._incendio_activo = hay

    def _avisosDeCupo(self, tick: int) -> None:
        lleno = self.poblacion.total() >= self.cfg_vida.MAX_CRIATURAS
        if lleno and not self._cupo_lleno:
            self._avisos.append(CupoAlcanzado(tick, self.cfg_vida.MAX_CRIATURAS))
        self._cupo_lleno = lleno
