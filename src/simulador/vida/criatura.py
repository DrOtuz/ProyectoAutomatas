"""Criatura: el estado de un individuo y sus acciones simples.

Una criatura sabe gastar energia, comer, envejecer, pagar una reproduccion y
morir. NO decide que hacer ni conoce el mapa: eso es del automata
(automata_criatura.py) y de Poblacion. Por eso se puede probar sola.

Orden de un turno (lo coordina el automata):
    iniciar_tick -> decidir y actuar (mover_a / comer_* / reproducir)
    -> cobrar_metabolismo -> envejecer
El metabolismo se cobra DESPUES de actuar porque el costo de moverse depende de
`m` (si la criatura se movio este tick), que solo se sabe al terminar de actuar.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from random import Random
from typing import Any

from .config import ConfigVida
from .estadisticas import Estadisticas
from .tipos import (
    INTENCION_ALIMENTO,
    INTENCION_PAREJA,
    CausaMuerte,
    Dieta,
    Estado,
    Pos,
)

# Tolerancia numerica para acumular velocidades decimales (1.6 + 1.6 + ...)
_EPS = 1e-9


def factor_temperatura(temperatura: float, cfg: ConfigVida) -> float:
    """f_T = 1 + ALFA * ((T - T_OPT) / 10)^2: curva en U, minima (1.0) en T_OPT."""
    return 1.0 + cfg.ALFA * ((temperatura - cfg.T_OPT) / 10.0) ** 2


def _signo(n: int) -> int:
    return (n > 0) - (n < 0)


class Criatura:
    def __init__(
        self,
        id: int,
        especie: str,
        dieta: Dieta,
        stats: Estadisticas,
        pos: Pos,
        cfg: ConfigVida,
        vida_max: int,
        energia: float | None = None,
    ) -> None:
        energia = cfg.ENERGIA_CRIA if energia is None else float(energia)
        if not 0 < energia <= cfg.E_MAX:
            raise ValueError(f"energia debe estar en (0, {cfg.E_MAX}], no {energia}")
        if vida_max <= 0:
            raise ValueError("vida_max debe ser > 0")

        self.cfg = cfg
        self.id = id
        self.especie = especie
        self.dieta = dieta
        self.stats = stats
        self.pos: Pos = (int(pos[0]), int(pos[1]))

        self.energia = energia
        self.estado = Estado.EXPLORAR
        self.intencion = INTENCION_ALIMENTO
        self.direccion: tuple[int, int] = (0, 0)

        self.acumulador_mov = 0.0
        self.pasos_tick = 0
        self.se_movio = False  # es la `m` del metabolismo
        self.turno_hecho = False  # para que la pareja no actue dos veces

        self.espera_reproduccion = 0  # ticks que faltan para poder reproducirse otra vez
        self.edad = 0
        self.vida_max = int(vida_max)
        self.viva = True
        self.causa_muerte: CausaMuerte | None = None
        # Aviso opcional al morir (lo pone Poblacion para llevar la cuenta y los
        # eventos al instante). No se guarda.
        self.al_morir: Callable[[Criatura], None] | None = None

    # --- creacion ---------------------------------------------------------------

    @staticmethod
    def calcular_vida_max(stats: Estadisticas, cfg: ConfigVida, rng: Random) -> int:
        """Vida maxima en ticks: VIDA_BASE * S^EXPONENTE_VEJEZ con +-VARIACION_VIDA.

        Se calcula al nacer y no se hereda. Siempre consume un numero al azar,
        aunque la vejez este apagada, para que la semilla sea repetible.
        """
        variacion = rng.uniform(-cfg.VARIACION_VIDA, cfg.VARIACION_VIDA)
        vida = cfg.VIDA_BASE * stats.tamano**cfg.EXPONENTE_VEJEZ * (1 + variacion)
        return max(1, round(vida))

    @classmethod
    def nueva(
        cls,
        id: int,
        especie: str,
        dieta: Dieta,
        stats: Estadisticas,
        pos: Pos,
        cfg: ConfigVida,
        rng: Random,
        energia: float | None = None,
    ) -> Criatura:
        """Crea una criatura recien nacida (sortea su vida maxima)."""
        vida_max = cls.calcular_vida_max(stats, cfg, rng)
        return cls(id, especie, dieta, stats, pos, cfg, vida_max, energia)

    # --- tick -------------------------------------------------------------------

    def iniciar_tick(self) -> None:
        """Prepara el turno: reinicia las marcas y calcula los pasos del tick.

        La velocidad decimal se acumula: con V = 1.6 avanza 1 casilla un tick y
        2 el siguiente.
        """
        self.se_movio = False
        self.turno_hecho = False
        if self.espera_reproduccion > 0:
            self.espera_reproduccion -= 1
        self.acumulador_mov += self.stats.velocidad
        pasos = int(self.acumulador_mov + _EPS)
        self.acumulador_mov = max(0.0, self.acumulador_mov - pasos)
        self.pasos_tick = pasos

    def mover_a(self, pos: Pos) -> None:
        """Cambia la posicion (hasta `pasos_tick` casillas) y marca que se movio.

        El indice por casilla lo actualiza Poblacion, no la criatura.
        """
        pos = (int(pos[0]), int(pos[1]))
        if pos == self.pos:
            return
        self.direccion = (_signo(pos[0] - self.pos[0]), _signo(pos[1] - self.pos[1]))
        self.pos = pos
        self.se_movio = True

    # --- metabolismo y vejez --------------------------------------------------------

    def gasto(self, temperatura: float) -> float:
        """Porcentaje de energia que gasta en un tick (usa `se_movio` como m).

        gasto = f_T * S^-0.25 * (A + C*R + K*V^2*m)
        """
        cfg, s = self.cfg, self.stats
        m = 1.0 if self.se_movio else 0.0
        base = cfg.A + cfg.C * s.vision + cfg.K * s.velocidad**2 * m
        return (
            factor_temperatura(temperatura, cfg) * s.tamano ** (-cfg.EXPONENTE_KLEIBER) * base
        )

    def cobrar_metabolismo(self, temperatura: float) -> float:
        """Resta el gasto del tick. Si la energia llega a 0, muere de HAMBRE.

        Devuelve el gasto cobrado (0 si ya estaba muerta).
        """
        if not self.viva:
            return 0.0
        g = self.gasto(temperatura)
        self.energia -= g
        if self.energia <= 0:
            self.energia = 0.0
            self.morir(CausaMuerte.HAMBRE)
        return g

    def envejecer(self) -> None:
        """Suma un tick de edad; si la vejez esta activa y llega a vida_max, muere."""
        if not self.viva:
            return
        self.edad += 1
        if self.cfg.VEJEZ_ACTIVA and self.edad >= self.vida_max:
            self.morir(CausaMuerte.VEJEZ)

    # --- alimentacion -----------------------------------------------------------------

    def eficiencia_planta(self) -> float:
        """ETA de plantas de su dieta (0 si no puede comerlas)."""
        return self.cfg.ETA_PLANTA[self.dieta]

    def eficiencia_carne(self) -> float:
        """ETA de carne de su dieta (0 si no puede comerla)."""
        return self.cfg.ETA_CARNE[self.dieta]

    def puede_comer_planta(self) -> bool:
        return self.dieta.come_plantas

    def puede_cazar(self, otra: Criatura) -> bool:
        """Presa elegible: otra especie, viva, y S_propia >= RATIO * S_presa."""
        return (
            self.viva
            and otra.viva
            and self.dieta.come_carne
            and otra.especie != self.especie
            and self.stats.tamano
            >= self.cfg.RATIO_DEPREDACION * otra.stats.tamano - 1e-12
        )

    def es_amenaza_para(self, otra: Criatura) -> bool:
        """True si `self` es una amenaza para `otra` (es decir, podria cazarla).

        Un herbivoro grande no es amenaza: no come carne.
        """
        return self.puede_cazar(otra)

    def ganancia_planta(self, biomasa_u: float) -> float:
        """% de energia que daria comer `biomasa_u` de planta (no modifica nada)."""
        return self.eficiencia_planta() * biomasa_u / self.stats.tamano

    def ganancia_presa(self, presa: Criatura) -> float:
        """% de energia que daria comerse a `presa` completa (no modifica nada).

        ganancia = ETA * masa_presa / S = 100 * ETA * S_presa / S_depredador
        """
        return (
            self.eficiencia_carne() * presa.stats.masa_u(self.cfg) / self.stats.tamano
        )

    def _sumar_energia(self, ganancia: float) -> float:
        """Suma energia con tope E_MAX (lo que sobra se pierde). Devuelve lo ganado de verdad."""
        antes = self.energia
        self.energia = min(self.cfg.E_MAX, self.energia + ganancia)
        return self.energia - antes

    def comer_planta(self, biomasa_u: float) -> float:
        """Come `biomasa_u` unidades de planta. Devuelve la energia realmente ganada."""
        if not self.puede_comer_planta():
            raise ValueError(f"un {self.dieta.value} no puede comer plantas")
        if biomasa_u < 0:
            raise ValueError("biomasa_u debe ser >= 0")
        return self._sumar_energia(self.ganancia_planta(biomasa_u))

    def comer_presa(self, presa: Criatura) -> float:
        """Se come a la presa completa (no hay mordida) y la mata por DEPREDACION.

        Devuelve la energia realmente ganada.
        """
        if not self.puede_cazar(presa):
            raise ValueError("la presa no es elegible para esta criatura")
        ganado = self._sumar_energia(self.ganancia_presa(presa))
        presa.morir(CausaMuerte.DEPREDACION)
        return ganado

    # --- reproduccion ---------------------------------------------------------------

    def en_umbral_reproduccion(self) -> bool:
        """energia >= UMBRAL_REPRODUCCION (70 % de E_MAX por defecto)."""
        return self.energia >= self.cfg.umbral_reproduccion

    def en_umbral_salida(self) -> bool:
        """energia < UMBRAL_SALIDA_PAREJA (50 % de E_MAX por defecto)."""
        return self.energia < self.cfg.umbral_salida_pareja

    def actualizar_intencion(self) -> str:
        """Histeresis: pasa a "pareja" con e >= 70 y vuelve a "alimento" con e < 50.

        Entre 50 y 70 conserva lo que queria. Evita oscilar entre estados.
        """
        if self.espera_reproduccion > 0:  # recien se reprodujo: solo busca comida
            self.intencion = INTENCION_ALIMENTO
        elif self.intencion == INTENCION_ALIMENTO and self.en_umbral_reproduccion():
            self.intencion = INTENCION_PAREJA
        elif self.intencion == INTENCION_PAREJA and self.en_umbral_salida():
            self.intencion = INTENCION_ALIMENTO
        return self.intencion

    def quiere_pareja(self) -> bool:
        """Si buscaria pareja en este momento (consulta pura: no cambia `intencion`).

        La intencion solo se actualiza en el turno de la propia criatura; esto
        permite a otra saber si esta quiere pareja aunque aun no le toque jugar.
        """
        if self.espera_reproduccion > 0:
            return False
        if self.intencion == INTENCION_PAREJA:
            return not self.en_umbral_salida()
        return self.en_umbral_reproduccion()

    def puede_pagar_reproduccion(self) -> bool:
        """Le alcanza la energia para pagar el costo y seguir viva."""
        return self.energia > self.cfg.COSTO_REPRODUCCION

    def pagar_reproduccion(self) -> None:
        """Resta COSTO_REPRODUCCION. Se llama solo si la reproduccion va a ocurrir."""
        if not self.puede_pagar_reproduccion():
            raise ValueError("energia insuficiente para reproducirse")
        self.energia -= self.cfg.COSTO_REPRODUCCION
        self.espera_reproduccion = self.cfg.COOLDOWN_REPRODUCCION

    # --- muerte -----------------------------------------------------------------------

    def morir(self, causa: CausaMuerte) -> None:
        """Marca la muerte. Si ya estaba muerta se conserva la primera causa."""
        if not self.viva:
            return
        self.viva = False
        self.estado = Estado.MUERTA
        self.causa_muerte = causa
        if self.al_morir is not None:
            self.al_morir(self)

    # --- guardado y carga -----------------------------------------------------------------

    def a_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "especie": self.especie,
            "dieta": self.dieta.value,
            "stats": self.stats.a_dict(),
            "pos": list(self.pos),
            "energia": self.energia,
            "estado": self.estado.value,
            "intencion": self.intencion,
            "direccion": list(self.direccion),
            "acumulador_mov": self.acumulador_mov,
            "pasos_tick": self.pasos_tick,
            "se_movio": self.se_movio,
            "turno_hecho": self.turno_hecho,
            "espera_reproduccion": self.espera_reproduccion,
            "edad": self.edad,
            "vida_max": self.vida_max,
            "viva": self.viva,
            "causa_muerte": self.causa_muerte.value if self.causa_muerte else None,
        }

    @classmethod
    def desde_dict(cls, datos: Mapping[str, Any], cfg: ConfigVida) -> Criatura:
        c = cls(
            id=datos["id"],
            especie=datos["especie"],
            dieta=Dieta(datos["dieta"]),
            stats=Estadisticas.desde_dict(datos["stats"]),
            pos=tuple(datos["pos"]),  # type: ignore[arg-type]
            cfg=cfg,
            vida_max=datos["vida_max"],
            energia=datos["energia"] if datos["energia"] > 0 else cfg.ENERGIA_CRIA,
        )
        # el constructor exige energia > 0; una criatura muerta puede tener 0
        c.energia = float(datos["energia"])
        c.estado = Estado(datos["estado"])
        c.intencion = datos["intencion"]
        c.direccion = tuple(datos["direccion"])  # type: ignore[assignment]
        c.acumulador_mov = float(datos["acumulador_mov"])
        c.pasos_tick = int(datos["pasos_tick"])
        c.se_movio = bool(datos["se_movio"])
        c.turno_hecho = bool(datos["turno_hecho"])
        c.espera_reproduccion = int(datos.get("espera_reproduccion", 0))
        c.edad = int(datos["edad"])
        c.viva = bool(datos["viva"])
        causa = datos["causa_muerte"]
        c.causa_muerte = CausaMuerte(causa) if causa else None
        return c

    def __repr__(self) -> str:
        return (
            f"Criatura(id={self.id}, {self.especie}, pos={self.pos}, "
            f"e={self.energia:.1f}, {self.estado.name}, edad={self.edad}/{self.vida_max})"
        )
