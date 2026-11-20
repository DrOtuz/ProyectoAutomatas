"""Poblacion: todas las criaturas de todas las especies y el tick de Vida.

Es el unico punto de entrada de la aplicacion hacia vida/:

    actualizar(mapa, temperatura)   un tick completo (lo llama el bucle de simulacion)
    crear_especie / eliminar_especie / agregar_individuos   (lo llama la interfaz)
    eliminar_en(x, y)               (lo llama el automata del incendio de A)
    snapshot()                      resumen por especie
    historial                       series por especie para las graficas (se llena solo en actualizar)
    suscribir(escucha)              eventos de nacimiento, muerte y extincion
    a_dict() / desde_dict()         guardado y carga

Implementa `ContextoVida`: el automata la usa para ver a las demas criaturas,
moverse y reproducirse. Mantiene un indice por casilla {(x, y): [criaturas]}
para no recorrer listas completas al buscar presas y parejas.

Orden de `actualizar`:
    1. iniciar_tick() en todas las vivas, y barajarlas (orden aleatorio, repetible)
    2. cada una juega su turno (las que murieron antes de su turno se saltan)
    3. retirar las muertas, incorporar las crias y declarar las extinciones
"""
from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from random import Random
from typing import Any

from .automata_criatura import AutomataCriatura
from .config import ConfigVida
from .criatura import Criatura
from .especie import Especie
from .estadisticas import Estadisticas
from .historial import GestorHistorial
from .percepcion import casillas_en_radio, distancia
from .puertos import MapaPuerto
from .tipos import CausaMuerte, Dieta, EstadoEspecie, Pos

NACIMIENTO = "nacimiento"
MUERTE = "muerte"
EXTINCION = "extincion"


@dataclass(frozen=True)
class EventoVida:
    """Lo que Poblacion le avisa a quien se suscriba (por ejemplo, la interfaz)."""

    tipo: str  # NACIMIENTO, MUERTE o EXTINCION
    tick: int
    especie: str
    criatura_id: int | None = None
    causa: CausaMuerte | None = None  # solo en MUERTE


class Poblacion:
    VERSION_ESQUEMA = 1

    def __init__(self, cfg: ConfigVida, rng: Random) -> None:
        self.cfg = cfg
        self.rng = rng
        self.automata = AutomataCriatura(cfg, rng)
        self.especies: dict[str, Especie] = {}
        self.tick = 0
        # una serie por especie, alimentada al final de cada tick (para las graficas)
        self.historial = GestorHistorial(cfg.MAX_PUNTOS_HISTORIAL)

        self._criaturas: dict[int, Criatura] = {}  # vivas y muertas aun sin retirar
        self._indice: dict[Pos, list[Criatura]] = {}
        self._nacimientos: list[Criatura] = []  # crias de este tick, aun fuera del juego
        self._pos_nacimientos: dict[Pos, int] = {}  # casillas reservadas por esas crias
        self._muertas: list[Criatura] = []  # muertas de este tick, por retirar
        self._n_vivas = 0
        self._siguiente_id = 1
        self._escuchas: list[Callable[[EventoVida], None]] = []

    # ================================================================================
    # consultas
    # ================================================================================

    def total(self) -> int:
        """Criaturas vivas."""
        return self._n_vivas

    def hay_cupo(self) -> bool:
        """True si se puede sumar una criatura mas sin pasar de MAX_CRIATURAS
        (cuenta las crias que nacen este tick)."""
        return self._n_vivas + len(self._nacimientos) < self.cfg.MAX_CRIATURAS

    def criaturas_vivas(self) -> list[Criatura]:
        """Las criaturas vivas (para que la interfaz dibuje el mapa)."""
        return [c for c in self._criaturas.values() if c.viva]

    def snapshot(self) -> dict[str, dict[str, Any]]:
        """Resumen por especie (sin las eliminadas): poblacion y promedios de
        S, V, R y energia. Una especie extinta tiene poblacion 0 y promedios None.

        Los promedios usan math.fsum: el resultado no depende del orden en que
        se sumen las criaturas (el conjunto de ids de la especie no tiene un
        orden fijo), asi que una poblacion cargada da exactamente los mismos
        numeros que la original, en cualquier maquina."""
        resumen: dict[str, dict[str, Any]] = {}
        for nombre, especie in self.especies.items():
            if especie.estado == EstadoEspecie.ELIMINADA:
                continue
            vivas = [self._criaturas[i] for i in sorted(especie.ids)]
            n = len(vivas)
            if n == 0:
                resumen[nombre] = {
                    "poblacion": 0, "tamano": None, "velocidad": None, "vision": None, "energia": None
                }
                continue
            resumen[nombre] = {
                "poblacion": n,
                "tamano": math.fsum(c.stats.tamano for c in vivas) / n,
                "velocidad": math.fsum(c.stats.velocidad for c in vivas) / n,
                "vision": math.fsum(c.stats.vision for c in vivas) / n,
                "energia": math.fsum(c.energia for c in vivas) / n,
            }
        return resumen

    # ================================================================================
    # eventos
    # ================================================================================

    def suscribir(self, escucha: Callable[[EventoVida], None]) -> None:
        """Registra una funcion que recibe cada `EventoVida`."""
        self._escuchas.append(escucha)

    def desuscribir(self, escucha: Callable[[EventoVida], None]) -> None:
        if escucha in self._escuchas:
            self._escuchas.remove(escucha)

    def _emitir(
        self, tipo: str, especie: str, criatura: Criatura | None = None,
        causa: CausaMuerte | None = None,
    ) -> None:
        if not self._escuchas:
            return
        evento = EventoVida(tipo, self.tick, especie, criatura.id if criatura else None, causa)
        for escucha in list(self._escuchas):
            escucha(evento)

    # ================================================================================
    # ContextoVida: lo que usa el automata
    # ================================================================================

    def criaturas_en(self, pos: Pos) -> list[Criatura]:
        """Criaturas en una casilla (pueden incluir muertas de este tick)."""
        return list(self._indice.get(pos, ()))

    def criaturas_en_radio(self, pos: Pos, radio: int) -> list[Criatura]:
        """Criaturas a distancia de Chebyshev <= radio (incluye la de `pos`).

        Recorre el menor de dos conjuntos: las casillas del cuadrado (via el
        indice) o todas las criaturas, segun cual sea mas chico.
        """
        x, y = pos
        if (2 * radio + 1) ** 2 <= len(self._criaturas):
            encontradas: list[Criatura] = []
            for j in range(y - radio, y + radio + 1):
                for i in range(x - radio, x + radio + 1):
                    lista = self._indice.get((i, j))
                    if lista:
                        encontradas.extend(lista)
            return encontradas
        return [
            c for c in self._criaturas.values()
            if abs(c.pos[0] - x) <= radio and abs(c.pos[1] - y) <= radio
        ]

    def mover(self, criatura: Criatura, pos: Pos) -> None:
        """Mueve a la criatura y actualiza el indice por casilla."""
        if pos == criatura.pos:
            return
        self._sacar_del_indice(criatura)
        criatura.mover_a(pos)
        self._indice.setdefault(criatura.pos, []).append(criatura)

    def reproducir(self, madre: Criatura, padre: Criatura, mapa: MapaPuerto) -> bool:
        """Intenta que nazca una cria. Si algo falla, devuelve False y no cobra nada.

        Condiciones: ambos vivos, de la misma especie, que quieran pareja y
        puedan pagar el costo, sin haber actuado este tick, a distancia <= 1;
        y que haya cupo (< MAX_CRIATURAS) y una casilla libre cerca.
        """
        if madre is padre or madre.especie != padre.especie:
            return False
        for c in (madre, padre):
            if (not c.viva or c.turno_hecho or not c.quiere_pareja()
                    or not c.puede_pagar_reproduccion()):
                return False
        if distancia(madre.pos, padre.pos) > 1 or not self.hay_cupo():
            return False
        pos = self.casilla_libre_cerca(madre.pos, mapa)
        if pos is None:
            return False

        madre.pagar_reproduccion()
        padre.pagar_reproduccion()
        stats = Estadisticas.cruzar(madre.stats, padre.stats, self.cfg, self.rng)
        cria = Criatura.nueva(
            self._nuevo_id(), madre.especie, madre.dieta, stats, pos, self.cfg, self.rng,
            energia=self.cfg.ENERGIA_CRIA,
        )
        self._nacimientos.append(cria)
        self._pos_nacimientos[pos] = self._pos_nacimientos.get(pos, 0) + 1
        madre.turno_hecho = True
        padre.turno_hecho = True
        return True

    # ================================================================================
    # espacio libre
    # ================================================================================

    def ocupacion(self, pos: Pos) -> int:
        """Criaturas vivas en la casilla, mas las crias que van a nacer ahi este tick."""
        lista = self._indice.get(pos)
        n = sum(1 for c in lista if c.viva) if lista else 0
        if self._pos_nacimientos:
            n += self._pos_nacimientos.get(pos, 0)
        return n

    def _casilla_libre(self, mapa: MapaPuerto, pos: Pos) -> bool:
        x, y = pos
        return (
            mapa.en_limites(x, y)
            and mapa.es_transitable(x, y)
            and not mapa.hay_fuego(x, y)
            and self.ocupacion(pos) < self.cfg.MAX_POR_CASILLA
        )

    def casilla_libre_cerca(self, pos: Pos, mapa: MapaPuerto) -> Pos | None:
        """La casilla libre mas cercana a `pos` (hasta RADIO_BUSQUEDA_CRIA); si
        hay varias a la misma distancia, una al azar. None si no hay ninguna."""
        for r in range(1, self.cfg.RADIO_BUSQUEDA_CRIA + 1):
            anillo = [
                p for p in casillas_en_radio(pos, r, mapa.ancho, mapa.alto)
                if distancia(p, pos) == r and self._casilla_libre(mapa, p)
            ]
            if anillo:
                return self.rng.choice(anillo)
        return None

    # ================================================================================
    # el tick
    # ================================================================================

    def actualizar(self, mapa: MapaPuerto, temperatura: float) -> None:
        """Un tick de Vida: cada criatura juega su turno en orden aleatorio."""
        self.tick += 1
        vivas = [c for c in self._criaturas.values() if c.viva]
        for c in vivas:
            c.iniciar_tick()
        self.rng.shuffle(vivas)
        for c in vivas:
            self.automata.turno(c, mapa, self, temperatura)  # salta a las ya muertas
        self._limpiar()
        self.historial.registrar(self.tick, self.snapshot())

    def _limpiar(self) -> None:
        """Retira a las muertas, incorpora las crias y declara las extinciones."""
        self._retirar_muertas()
        for cria in self._nacimientos:
            if self._n_vivas < self.cfg.MAX_CRIATURAS:
                self._registrar(cria)
        self._nacimientos.clear()
        self._pos_nacimientos.clear()
        self._revisar_extinciones()

    def _retirar_muertas(self) -> None:
        for c in self._muertas:
            self._sacar_del_indice(c)
            self._criaturas.pop(c.id, None)
            especie = self.especies.get(c.especie)
            if especie is not None:
                especie.quitar(c)
        self._muertas.clear()

    def _revisar_extinciones(self) -> None:
        for especie in self.especies.values():
            if especie.estado == EstadoEspecie.ACTIVA and especie.contar() == 0:
                especie.extinguir()
                self._emitir(EXTINCION, especie.nombre)

    # ================================================================================
    # altas y bajas de criaturas
    # ================================================================================

    def _nuevo_id(self) -> int:
        nuevo = self._siguiente_id
        self._siguiente_id += 1
        return nuevo

    def _sacar_del_indice(self, c: Criatura) -> None:
        lista = self._indice.get(c.pos)
        if lista is not None and c in lista:
            lista.remove(c)
            if not lista:
                del self._indice[c.pos]

    def _registrar(self, c: Criatura, emitir: bool = True) -> None:
        """Mete a la criatura en el juego (diccionario, indice, especie, cuenta)."""
        self._criaturas[c.id] = c
        self._indice.setdefault(c.pos, []).append(c)
        especie = self.especies[c.especie]
        especie.reactivar()
        especie.agregar(c)
        self._n_vivas += 1
        c.al_morir = self._al_morir
        if emitir:
            self._emitir(NACIMIENTO, c.especie, c)

    def _al_morir(self, c: Criatura) -> None:
        """Aviso de Criatura.morir: cuenta la baja al instante (libera cupo) y
        la deja en la lista para retirarla al final del tick."""
        self._n_vivas -= 1
        self._muertas.append(c)
        self._emitir(MUERTE, c.especie, c, c.causa_muerte)

    def agregar_criatura(
        self,
        nombre: str,
        pos: Pos,
        energia: float | None = None,
        stats: Estadisticas | None = None,
    ) -> Criatura:
        """Agrega UNA criatura a una especie en `pos` (sin revisar el mapa: quien
        llama se asegura de que la casilla sirva). Falla si se pasaria del limite."""
        especie = self.especies[nombre]
        if especie.estado == EstadoEspecie.ELIMINADA:
            raise ValueError(f"la especie {nombre!r} fue eliminada")
        if not self.hay_cupo():
            raise ValueError(f"se alcanzo el limite de {self.cfg.MAX_CRIATURAS} criaturas")
        if stats is None:
            stats = especie.plantilla.variar(self.cfg.VARIACION_INICIAL, self.rng)
        criatura = Criatura.nueva(
            self._nuevo_id(), nombre, especie.dieta, stats, pos, self.cfg, self.rng, energia
        )
        self._registrar(criatura)
        return criatura

    def _estadisticas_medias(self, nombre: str) -> Estadisticas:
        """S, V y R promedio de los individuos vivos de la especie; si no queda
        ninguno (extinta), la plantilla con la que se creo."""
        especie = self.especies[nombre]
        vivas = [self._criaturas[i] for i in sorted(especie.ids)]
        if not vivas:
            return especie.plantilla
        n = len(vivas)
        return Estadisticas(
            tamano=math.fsum(c.stats.tamano for c in vivas) / n,
            velocidad=math.fsum(c.stats.velocidad for c in vivas) / n,
            vision=math.fsum(c.stats.vision for c in vivas) / n,
        )

    def agregar_individuos(
        self,
        nombre: str,
        cantidad: int,
        mapa: MapaPuerto,
        posiciones: list[Pos] | None = None,
        energia: float | None = None,
        promedio_actual: bool = False,
    ) -> int:
        """Agrega hasta `cantidad` criaturas a una especie ya creada.

        Nacen con la plantilla de la especie o, con `promedio_actual`, con los
        S, V y R promedio de sus vivos (si esta extinta, la plantilla); en ambos
        casos con la variacion inicial. Van a las `posiciones` dadas (las que
        sirvan) o a casillas libres al azar. Respeta MAX_CRIATURAS y MAX_POR_CASILLA. Devuelve cuantas agrego.
        """
        if nombre not in self.especies:
            raise KeyError(nombre)
        if cantidad < 0:
            raise ValueError("cantidad no puede ser negativa")
        cupo = max(0, self.cfg.MAX_CRIATURAS - self._n_vivas - len(self._nacimientos))
        objetivo = min(cantidad, cupo)
        agregadas = 0
        base = self._estadisticas_medias(nombre) if promedio_actual else self.especies[nombre].plantilla

        if posiciones is not None:
            for pos in posiciones:
                if agregadas >= objetivo:
                    break
                if self._casilla_libre(mapa, pos):
                    self.agregar_criatura(nombre, pos, energia, base.variar(self.cfg.VARIACION_INICIAL, self.rng))
                    agregadas += 1
            return agregadas

        intentos = objetivo * 20 + 100
        while agregadas < objetivo and intentos > 0:
            intentos -= 1
            pos = (self.rng.randrange(mapa.ancho), self.rng.randrange(mapa.alto))
            if self._casilla_libre(mapa, pos):
                self.agregar_criatura(nombre, pos, energia, base.variar(self.cfg.VARIACION_INICIAL, self.rng))
                agregadas += 1
        if agregadas < objetivo:  # mapa casi lleno: revisa todas las casillas
            todas = [(x, y) for y in range(mapa.alto) for x in range(mapa.ancho)]
            self.rng.shuffle(todas)
            for pos in todas:
                if agregadas >= objetivo:
                    break
                if self._casilla_libre(mapa, pos):
                    self.agregar_criatura(nombre, pos, energia, base.variar(self.cfg.VARIACION_INICIAL, self.rng))
                    agregadas += 1
        return agregadas

    # ================================================================================
    # operaciones de la interfaz (C) y del incendio (A)
    # ================================================================================

    def crear_especie(
        self,
        nombre: str,
        dieta: Dieta,
        cantidad: int,
        mapa: MapaPuerto,
        plantilla: Estadisticas | None = None,
        color: str | None = None,
        energia: float | None = None,
    ) -> Especie:
        """Crea una especie y coloca `cantidad` criaturas en casillas libres al azar.

        `plantilla` son los S, V y R de referencia (por defecto, los de la
        configuracion para esa dieta); cada criatura sale con una variacion
        individual de VARIACION_INICIAL. Los nombres no se repiten, salvo el de
        una especie ya eliminada.
        """
        if not isinstance(dieta, Dieta):
            raise TypeError(f"dieta invalida: {dieta!r}")
        if cantidad < 0:
            raise ValueError("cantidad no puede ser negativa")
        existente = self.especies.get(nombre)
        if existente is not None and existente.estado != EstadoEspecie.ELIMINADA:
            raise ValueError(f"ya existe una especie llamada {nombre!r}")
        if plantilla is None:
            plantilla = Estadisticas(*self.cfg.PLANTILLAS[dieta])
        else:  # lo eligio el usuario: debe caer dentro del rango permitido
            self.cfg.comprobar_estadisticas(
                plantilla.tamano, plantilla.velocidad, plantilla.vision
            )
        especie = Especie(nombre, dieta, plantilla, color)
        self.especies[nombre] = especie
        self.agregar_individuos(nombre, cantidad, mapa, energia=energia)
        self._revisar_extinciones()  # si no cupo ninguna, nace extinta
        return especie

    def eliminar_especie(self, nombre: str) -> int:
        """Elimina una especie: mata a todas sus criaturas (causa ELIMINACION).
        Devuelve cuantas murieron."""
        especie = self.especies[nombre]
        if especie.estado == EstadoEspecie.ELIMINADA:
            return 0
        muertas = 0
        for c in [c for c in self._criaturas.values() if c.especie == nombre and c.viva]:
            c.morir(CausaMuerte.ELIMINACION)
            muertas += 1
        for cria in [c for c in self._nacimientos if c.especie == nombre]:
            self._nacimientos.remove(cria)
            self._pos_nacimientos[cria.pos] -= 1
        especie.eliminar()
        self._retirar_muertas()
        return muertas

    def eliminar_en(self, x: int, y: int) -> int:
        """Mata (causa FUEGO) a las criaturas de una casilla. Lo usa el automata
        del incendio. Devuelve cuantas murieron."""
        muertas = 0
        for c in list(self._indice.get((x, y), ())):
            if c.viva:
                c.morir(CausaMuerte.FUEGO)
                muertas += 1
        self._retirar_muertas()
        self._revisar_extinciones()
        return muertas

    def eliminar_criaturas(self, nombre: str, cantidad: int) -> int:
        """Retira `cantidad` criaturas de la especie, elegidas al azar (causa
        ELIMINACION). La especie sigue existiendo, y si se queda sin ninguna
        pasa a extinta. Devuelve cuantas murieron."""
        if cantidad < 0:
            raise ValueError("cantidad no puede ser negativa")
        especie = self.especies[nombre]
        if especie.estado == EstadoEspecie.ELIMINADA:
            return 0
        elegidas = self.rng.sample(sorted(especie.ids), min(cantidad, especie.contar()))
        for id_ in elegidas:
            self._criaturas[id_].morir(CausaMuerte.ELIMINACION)
        self._retirar_muertas()
        self._revisar_extinciones()
        return len(elegidas)

    def extinguir_especie(self, nombre: str) -> int:
        """Mata a todas las criaturas de la especie, que queda extinta (sigue en
        la lista y se le pueden agregar individuos). Devuelve cuantas murieron."""
        return self.eliminar_criaturas(nombre, self.especies[nombre].contar())

    # ================================================================================
    # revision interna
    # ================================================================================

    def verificar_consistencia(self) -> list[str]:
        """Revisa los invariantes internos. Devuelve la lista de problemas (vacia si todo bien).

        Pensada para pruebas y depuracion: el indice por casilla coincide con las
        posiciones reales, las cuentas cuadran y no se pasa de los limites.
        """
        problemas: list[str] = []
        vivas = [c for c in self._criaturas.values() if c.viva]
        if self._n_vivas != len(vivas):
            problemas.append(f"contador de vivas {self._n_vivas} != {len(vivas)} reales")
        if self._n_vivas > self.cfg.MAX_CRIATURAS:
            problemas.append(f"hay {self._n_vivas} criaturas (limite {self.cfg.MAX_CRIATURAS})")
        en_indice = [c for lista in self._indice.values() for c in lista]
        for c in en_indice:
            if self._criaturas.get(c.id) is not c:
                problemas.append(f"{c!r} esta en el indice pero no en la poblacion")
        for c in self._criaturas.values():
            if sum(1 for o in self._indice.get(c.pos, ()) if o is c) != 1:
                problemas.append(f"{c!r} no esta exactamente una vez en el indice de {c.pos}")
        for pos, lista in self._indice.items():
            if not lista:
                problemas.append(f"lista vacia en el indice de {pos}")
            if sum(1 for c in lista if c.viva) > self.cfg.MAX_POR_CASILLA:
                problemas.append(f"demasiadas criaturas en {pos}")
            for c in lista:
                if c.pos != pos:
                    problemas.append(f"{c!r} esta indexada en {pos}")
        cuenta_especies = sum(e.contar() for e in self.especies.values())
        if cuenta_especies != len(self._criaturas):  # las muertas cuentan hasta retirarlas
            problemas.append(
                f"las especies cuentan {cuenta_especies}, la poblacion {len(self._criaturas)}"
            )
        for e in self.especies.values():
            for i in e.ids:
                c = self._criaturas.get(i)
                if c is None or c.especie != e.nombre:
                    problemas.append(f"la especie {e.nombre!r} tiene un id fantasma: {i}")
        return problemas

    # ================================================================================
    # guardado y carga
    # ================================================================================

    def a_dict(self) -> dict[str, Any]:
        """Estado completo entre ticks (incluye el estado del generador al azar,
        para que una simulacion cargada siga exactamente igual)."""
        version, interno, gauss = self.rng.getstate()
        return {
            "version": self.VERSION_ESQUEMA,
            "tick": self.tick,
            "siguiente_id": self._siguiente_id,
            "cfg": self.cfg.a_dict(),
            "rng": [version, list(interno), gauss],
            "especies": [e.a_dict() for e in self.especies.values()],
            "criaturas": [c.a_dict() for c in self._criaturas.values() if c.viva],
            "historial": self.historial.a_dict(),
        }

    @classmethod
    def desde_dict(
        cls, datos: Mapping[str, Any], cfg: ConfigVida | None = None
    ) -> Poblacion:
        """Reconstruye una poblacion guardada con `a_dict` (sin avisar eventos)."""
        if cfg is None:
            cfg = ConfigVida.desde_dict(datos["cfg"])
        rng = Random()
        version, interno, gauss = datos["rng"]
        rng.setstate((version, tuple(interno), gauss))
        pob = cls(cfg, rng)
        pob.tick = int(datos["tick"])
        pob._siguiente_id = int(datos["siguiente_id"])
        for d in datos["especies"]:
            especie = Especie.desde_dict(d)
            pob.especies[especie.nombre] = especie
        for d in datos["criaturas"]:
            pob._registrar(Criatura.desde_dict(d, cfg), emitir=False)
        if "historial" in datos:  # los guardados anteriores no lo traen
            pob.historial = GestorHistorial.desde_dict(datos["historial"])
        return pob
