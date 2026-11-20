"""Configuracion del paquete vida/: todas las constantes en un solo lugar.

`ConfigVida` es inmutable. Para cambiar algo se crea una copia:

    cfg = ConfigVida().con(SIGMA=0.08)

La logica de vida/ nunca debe tener numeros magicos: los lee de aqui. Las
constantes marcadas "depende de A" o "depende de C" son las que otros grupos
pueden cambiar; se ajustan aqui o en el adaptador, sin tocar la logica.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields, replace
from typing import Any, ClassVar

from .tipos import Dieta

# --- valores por defecto de las tablas por dieta ---------------------------


def _eta_planta_defecto() -> dict[Dieta, float]:
    return {Dieta.HERBIVORO: 0.60, Dieta.CARNIVORO: 0.0, Dieta.OMNIVORO: 0.20}


def _eta_carne_defecto() -> dict[Dieta, float]:
    return {Dieta.HERBIVORO: 0.0, Dieta.CARNIVORO: 0.70, Dieta.OMNIVORO: 0.40}


def _plantillas_defecto() -> dict[Dieta, tuple[float, float, float]]:
    # (tamano S, velocidad V, vision R)
    return {
        Dieta.HERBIVORO: (1.0, 2.0, 7.0),
        Dieta.OMNIVORO: (1.3, 1.5, 5.0),
        Dieta.CARNIVORO: (1.6, 1.0, 4.0),
    }


# Campos que son diccionarios indexados por Dieta (necesitan conversion al
# guardar y cargar).
_CAMPOS_ETA = ("ETA_PLANTA", "ETA_CARNE")
_CAMPO_PLANTILLAS = "PLANTILLAS"
_CAMPOS_RANGO = ("RANGO_TAMANO", "RANGO_VELOCIDAD", "RANGO_VISION")


def _a_dieta(clave: Any) -> Dieta:
    return clave if isinstance(clave, Dieta) else Dieta(clave)


@dataclass(frozen=True)
class ConfigVida:
    """Constantes de la simulacion de criaturas (valores iniciales del v0.1)."""

    VERSION_ESQUEMA: ClassVar[int] = 1

    # --- energia -----------------------------------------------------------
    E_MAX: float = 100.0
    UMBRAL_REPRODUCCION_PCT: float = 0.70  # fraccion de E_MAX para buscar pareja
    UMBRAL_SALIDA_PAREJA_PCT: float = 0.50  # por debajo, deja de buscar pareja
    COSTO_REPRODUCCION: float = 25.0  # energia que paga cada padre
    ENERGIA_CRIA: float = 30.0  # energia con la que nace la cria
    COOLDOWN_REPRODUCCION: int = 60  # ticks que debe esperar un padre antes de reproducirse otra vez

    # --- metabolismo: gasto = f_T * S^-EXPONENTE_KLEIBER * (A + C*R + K*V^2*m)
    A: float = 0.30
    C: float = 0.10
    K: float = 0.30
    EXPONENTE_KLEIBER: float = 0.25
    T_OPT: float = 22.0  # temperatura ideal (grados C)
    ALFA: float = 0.15  # fuerza del efecto de la temperatura

    # --- alimentacion ------------------------------------------------------
    ETA_PLANTA: dict = field(default_factory=_eta_planta_defecto)
    ETA_CARNE: dict = field(default_factory=_eta_carne_defecto)
    RATIO_DEPREDACION: float = 1.2  # S_depredador >= RATIO * S_presa
    UNIDADES_POR_TAMANO: float = 100.0  # una criatura de tamano S pesa 100*S u

    # --- herencia ----------------------------------------------------------
    SIGMA: float = 0.10  # desviacion de la mutacion (proporcional)
    VARIACION_INICIAL: float = 0.10  # variacion individual al crear una especie
    PLANTILLAS: dict = field(default_factory=_plantillas_defecto)

    # Rango valido de S, V y R cuando el usuario elige las estadisticas de su
    # especie: (minimo, maximo), ambos incluidos.
    RANGO_TAMANO: tuple = (0.5, 3.0)
    RANGO_VELOCIDAD: tuple = (0.5, 3.0)  # casillas por tick
    RANGO_VISION: tuple = (1.0, 10.0)  # radio

    # --- vejez -------------------------------------------------------------
    VEJEZ_ACTIVA: bool = True
    VIDA_BASE: float = 1500.0  # ticks; vida_max = VIDA_BASE * S^EXPONENTE_VEJEZ
    EXPONENTE_VEJEZ: float = 0.25
    VARIACION_VIDA: float = 0.15  # +-15 % al nacer

    # --- mundo -------------------------------------------------------------
    MAX_CRIATURAS: int = 500
    MAX_POR_CASILLA: int = 1
    RADIO_BUSQUEDA_CRIA: int = 2  # a que distancia de los padres puede nacer
    INERCIA_EXPLORAR: float = 0.7  # probabilidad de seguir recto al explorar
    MAX_PUNTOS_HISTORIAL: int = 2000  # puntos por especie antes de reducir el historial

    # --- depende de A (mapa) -----------------------------------------------
    FACTOR_BIOMASA: float = 1.0  # multiplica la comida que reporta el mapa
    TEMPERATURA_POR_DEFECTO: float = 22.0  # si A no entrega temperatura

    # --- derivados ---------------------------------------------------------

    @property
    def umbral_reproduccion(self) -> float:
        """Energia minima para buscar pareja."""
        return self.UMBRAL_REPRODUCCION_PCT * self.E_MAX

    @property
    def umbral_salida_pareja(self) -> float:
        """Por debajo de esta energia deja de buscar pareja."""
        return self.UMBRAL_SALIDA_PAREJA_PCT * self.E_MAX

    def con(self, **cambios: Any) -> ConfigVida:
        """Copia de esta configuracion con algunos campos cambiados."""
        return replace(self, **cambios)

    # --- validacion --------------------------------------------------------

    def validar(self) -> ConfigVida:
        """Revisa que los valores sean coherentes. Devuelve self si todo esta bien.

        Lanza ValueError con la lista de todos los problemas encontrados.
        """
        errores: list[str] = []

        def exigir(condicion: bool, mensaje: str) -> None:
            if not condicion:
                errores.append(mensaje)

        exigir(self.E_MAX > 0, "E_MAX debe ser > 0")
        exigir(
            0 < self.UMBRAL_SALIDA_PAREJA_PCT < self.UMBRAL_REPRODUCCION_PCT <= 1,
            "se exige 0 < UMBRAL_SALIDA_PAREJA_PCT < UMBRAL_REPRODUCCION_PCT <= 1",
        )
        exigir(self.COSTO_REPRODUCCION > 0, "COSTO_REPRODUCCION debe ser > 0")
        exigir(self.COOLDOWN_REPRODUCCION >= 0, "COOLDOWN_REPRODUCCION debe ser >= 0")
        exigir(
            self.COSTO_REPRODUCCION < self.umbral_reproduccion,
            "COSTO_REPRODUCCION debe ser menor que el umbral de reproduccion",
        )
        exigir(0 < self.ENERGIA_CRIA <= self.E_MAX, "ENERGIA_CRIA debe estar en (0, E_MAX]")
        exigir(
            self.ENERGIA_CRIA <= 2 * self.COSTO_REPRODUCCION,
            "ENERGIA_CRIA no puede superar lo que pagan los dos padres (se crearia energia)",
        )
        exigir(self.A >= 0 and self.C >= 0 and self.K >= 0, "A, C y K deben ser >= 0")
        exigir(self.A + self.C + self.K > 0, "A, C y K no pueden ser todos 0")
        exigir(self.EXPONENTE_KLEIBER >= 0, "EXPONENTE_KLEIBER debe ser >= 0")
        exigir(self.ALFA >= 0, "ALFA debe ser >= 0")
        exigir(self.RATIO_DEPREDACION >= 1.0, "RATIO_DEPREDACION debe ser >= 1")
        exigir(self.UNIDADES_POR_TAMANO > 0, "UNIDADES_POR_TAMANO debe ser > 0")
        exigir(self.SIGMA >= 0, "SIGMA debe ser >= 0")
        exigir(0 <= self.VARIACION_INICIAL < 1, "VARIACION_INICIAL debe estar en [0, 1)")
        exigir(self.VIDA_BASE > 0, "VIDA_BASE debe ser > 0")
        exigir(self.EXPONENTE_VEJEZ >= 0, "EXPONENTE_VEJEZ debe ser >= 0")
        exigir(0 <= self.VARIACION_VIDA < 1, "VARIACION_VIDA debe estar en [0, 1)")
        exigir(self.MAX_CRIATURAS >= 1, "MAX_CRIATURAS debe ser >= 1")
        exigir(self.MAX_POR_CASILLA >= 1, "MAX_POR_CASILLA debe ser >= 1")
        exigir(self.RADIO_BUSQUEDA_CRIA >= 1, "RADIO_BUSQUEDA_CRIA debe ser >= 1")
        exigir(0 <= self.INERCIA_EXPLORAR <= 1, "INERCIA_EXPLORAR debe estar en [0, 1]")
        exigir(self.FACTOR_BIOMASA > 0, "FACTOR_BIOMASA debe ser > 0")
        exigir(self.MAX_PUNTOS_HISTORIAL >= 4, "MAX_PUNTOS_HISTORIAL debe ser >= 4")
        for nombre in _CAMPOS_RANGO:
            rango = getattr(self, nombre)
            exigir(
                len(rango) == 2 and 0 < rango[0] <= rango[1],
                f"{nombre} debe ser (minimo, maximo) con 0 < minimo <= maximo",
            )

        for dieta in Dieta:
            eta_p = self.ETA_PLANTA.get(dieta)
            eta_c = self.ETA_CARNE.get(dieta)
            exigir(eta_p is not None, f"falta ETA_PLANTA[{dieta.name}]")
            exigir(eta_c is not None, f"falta ETA_CARNE[{dieta.name}]")
            if eta_p is not None:
                exigir(0 <= eta_p <= 1, f"ETA_PLANTA[{dieta.name}] debe estar en [0, 1]")
                exigir(
                    (eta_p > 0) == dieta.come_plantas,
                    f"ETA_PLANTA[{dieta.name}] no coincide con lo que come esa dieta",
                )
            if eta_c is not None:
                exigir(0 <= eta_c <= 1, f"ETA_CARNE[{dieta.name}] debe estar en [0, 1]")
                exigir(
                    (eta_c > 0) == dieta.come_carne,
                    f"ETA_CARNE[{dieta.name}] no coincide con lo que come esa dieta",
                )
            plantilla = self.PLANTILLAS.get(dieta)
            exigir(plantilla is not None, f"falta PLANTILLAS[{dieta.name}]")
            if plantilla is not None:
                exigir(
                    len(plantilla) == 3 and all(x > 0 for x in plantilla),
                    f"PLANTILLAS[{dieta.name}] debe ser (S, V, R) con valores > 0",
                )
                if len(plantilla) == 3 and all(x > 0 for x in plantilla):
                    try:
                        self.comprobar_estadisticas(*plantilla)
                    except ValueError as error:
                        errores.append(f"PLANTILLAS[{dieta.name}] fuera de rango: {error}")

        if errores:
            raise ValueError("Configuracion invalida:\n- " + "\n- ".join(errores))
        return self

    def comprobar_estadisticas(self, tamano: float, velocidad: float, vision: float) -> None:
        """Lanza ValueError (en espanol, para mostrar al usuario) si S, V o R
        quedan fuera del rango permitido."""
        for etiqueta, valor, (minimo, maximo) in (
            ("El tamano", tamano, self.RANGO_TAMANO),
            ("La velocidad", velocidad, self.RANGO_VELOCIDAD),
            ("La vision", vision, self.RANGO_VISION),
        ):
            if not minimo <= valor <= maximo:
                raise ValueError(f"{etiqueta} debe estar entre {minimo:g} y {maximo:g} (llego {valor:g})")

    # --- guardado y carga ---------------------------------------------------

    def a_dict(self) -> dict[str, Any]:
        """Diccionario simple (solo tipos JSON) para guardar la configuracion."""
        datos: dict[str, Any] = {"version": self.VERSION_ESQUEMA}
        for campo in fields(self):
            valor = getattr(self, campo.name)
            if campo.name in _CAMPOS_ETA:
                valor = {_a_dieta(d).value: float(v) for d, v in valor.items()}
            elif campo.name == _CAMPO_PLANTILLAS:
                valor = {_a_dieta(d).value: [float(x) for x in t] for d, t in valor.items()}
            elif campo.name in _CAMPOS_RANGO:
                valor = [float(x) for x in valor]
            datos[campo.name] = valor
        return datos

    @classmethod
    def desde_dict(cls, datos: Mapping[str, Any]) -> ConfigVida:
        """Reconstruye una configuracion.

        Ignora claves desconocidas (por ejemplo, de una version posterior) y
        usa el valor por defecto de las claves que falten.
        """
        conocidos = {campo.name for campo in fields(cls)}
        base = cls()
        kwargs: dict[str, Any] = {}
        for nombre, valor in datos.items():
            if nombre not in conocidos:
                continue
            if nombre in _CAMPOS_ETA:
                convertido = {_a_dieta(d): float(v) for d, v in valor.items()}
                kwargs[nombre] = {**getattr(base, nombre), **convertido}
            elif nombre == _CAMPO_PLANTILLAS:
                convertido = {
                    _a_dieta(d): tuple(float(x) for x in t) for d, t in valor.items()
                }
                kwargs[nombre] = {**base.PLANTILLAS, **convertido}
            elif nombre in _CAMPOS_RANGO:
                kwargs[nombre] = tuple(float(x) for x in valor)
            else:
                kwargs[nombre] = valor
        return cls(**kwargs)
