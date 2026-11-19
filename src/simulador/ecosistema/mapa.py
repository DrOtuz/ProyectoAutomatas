"""Casillas y mapa del ecosistema.

Casilla es la de ecosistema.py (configuracion) corregida y movida aqui: era una dataclass
`frozen` con un __post_init__ que no podia ejecutarse, y leia un `tick_actual` global que
nadie actualizaba. Ahora el tick siempre llega como argumento, desde Reloj.tick.

Mapa es lo minimo que necesita el fuego (ancho, alto, casilla, vecinas, casillasEnRadio).
Si el grupo ya tiene su propio Mapa, basta con que ofrezca esos miembros.
"""
from simulador.contratos.instantanea import EstadoCasilla

AGUA = EstadoCasilla["agua"]
TIERRA = EstadoCasilla["tierra"]
PASTO = EstadoCasilla["pasto"]
ARBOL = EstadoCasilla["arbol"]
LLAMAS = EstadoCasilla["llamas"]  # ajustar aqui si el contrato usa otro nombre
QUEMADA = EstadoCasilla["quemada"]

INFLAMABLES = (PASTO, ARBOL)


class Casilla:
    __slots__ = (
        "tipo",
        "coordenada",
        "humedad",
        "alimento",
        "tick_inicio_llamas",
        "tick_quemada",
        "vegetacion_previa",
    )

    def __init__(self, tipo_casilla: EstadoCasilla, coordenada: tuple, humedad: float = 0.0, alimento: float = 0):
        self.tipo = tipo_casilla
        self.coordenada = coordenada
        self.humedad = humedad
        self.alimento = alimento
        self.tick_inicio_llamas = 0
        self.tick_quemada = 0
        self.vegetacion_previa = None

    def getTipo(self) -> EstadoCasilla:
        """Obtiene el tipo de la casilla"""
        return self.tipo

    def getHumedad(self) -> float:
        """Obtiene la humedad presente en la casilla"""
        return self.humedad

    def esInflamable(self) -> bool:
        """Solo el pasto y el arbol se prenden; agua, tierra, llamas y quemada no."""
        return self.tipo in INFLAMABLES

    def encender(self, tick: int) -> None:
        """Pasa de pasto o arbol a llamas. Pierde el alimento y recuerda la vegetacion (RF-35)."""
        if not self.esInflamable():
            raise ValueError(f"Una casilla de tipo {self.tipo.name} no se puede encender")
        self.vegetacion_previa = self.tipo
        self.alimento = 0
        self.tipo = LLAMAS
        self.tick_inicio_llamas = tick

    def quemar(self, tick: int) -> None:
        """Cambia el estado de una casilla a quemada"""
        self.tipo = QUEMADA
        self.alimento = 0
        self.vegetacion_previa = None
        self.tick_quemada = tick

    def regenerar(self, tick: int, ticks_para_regenerar: int) -> bool:
        """Si lleva quemada ticks_para_regenerar o mas, pasa a tierra. Devuelve True si cambio."""
        if self.tipo == QUEMADA and tick - self.tick_quemada >= ticks_para_regenerar:
            self.tipo = TIERRA
            return True
        return False

    def evolucionar(self) -> None:
        """Tierra a pasto o pasto a arbol (un solo nivel por llamada)."""
        if self.tipo == TIERRA:
            self.tipo = PASTO
        elif self.tipo == PASTO:
            self.tipo = ARBOL

    def involucionar(self) -> None:
        """Arbol a pasto o pasto a tierra (un solo nivel por llamada)."""
        if self.tipo == ARBOL:
            self.tipo = PASTO
        elif self.tipo == PASTO:
            self.tipo = TIERRA


class Mapa:
    def __init__(self, ancho: int, alto: int, tipo_inicial: EstadoCasilla = TIERRA):
        self.ancho = ancho
        self.alto = alto
        self._casillas = [[Casilla(tipo_inicial, (x, y)) for x in range(ancho)] for y in range(alto)]

    def casilla(self, x: int, y: int) -> Casilla:
        return self._casillas[y][x]

    def casillas(self):
        """Todas las casillas, fila por fila (y, luego x)."""
        for fila in self._casillas:
            yield from fila

    def casillasEnRadio(self, x: int, y: int, radio: int) -> list:
        """Coordenadas (x, y) a distancia de Chebyshev <= radio, dentro del mapa, fila por fila."""
        return [
            (cx, cy)
            for cy in range(max(0, y - radio), min(self.alto, y + radio + 1))
            for cx in range(max(0, x - radio), min(self.ancho, x + radio + 1))
        ]

    def enLimites(self, x: int, y: int) -> bool:
        return 0 <= x < self.ancho and 0 <= y < self.alto

    # ---------- conversion con el arreglo de terreno de la aplicacion ----------

    def aTerreno(self):
        """Arreglo uint8 [alto, ancho] con los codigos de EstadoCasilla (lo que ve la interfaz)."""
        import numpy as np

        return np.array([[int(c.tipo) for c in fila] for fila in self._casillas], dtype=np.uint8)

    @classmethod
    def desdeTerreno(cls, terreno, alimento_maximo: dict | None = None) -> "Mapa":
        """Mapa a partir de un arreglo [alto, ancho] de codigos de EstadoCasilla.

        El pasto y el arbol empiezan con el alimento maximo; las llamas se toman como pasto.
        """
        alto, ancho = terreno.shape
        mapa = cls(ancho, alto)
        maximo = alimento_maximo or {"pasto": 30.0, "arbol": 60.0}
        for y in range(alto):
            for x in range(ancho):
                tipo = EstadoCasilla(int(terreno[y, x]))
                if tipo == LLAMAS:
                    tipo = PASTO
                c = mapa.casilla(x, y)
                c.tipo = tipo
                if tipo == PASTO:
                    c.alimento = maximo["pasto"]
                elif tipo == ARBOL:
                    c.alimento = maximo["arbol"]
        return mapa

    def aEstado(self) -> dict:
        """Estado completo con tipos basicos, por filas (para guardar)."""
        filas = lambda f: [[f(c) for c in fila] for fila in self._casillas]  # noqa: E731
        return {
            "ancho": self.ancho,
            "alto": self.alto,
            "tipo": filas(lambda c: int(c.tipo)),
            "humedad": filas(lambda c: c.humedad),
            "alimento": filas(lambda c: c.alimento),
            "tick_inicio_llamas": filas(lambda c: c.tick_inicio_llamas),
            "tick_quemada": filas(lambda c: c.tick_quemada),
            "vegetacion_previa": filas(lambda c: None if c.vegetacion_previa is None else int(c.vegetacion_previa)),
        }

    @classmethod
    def desdeEstado(cls, estado: dict) -> "Mapa":
        mapa = cls(estado["ancho"], estado["alto"])
        for y, fila in enumerate(mapa._casillas):
            for x, c in enumerate(fila):
                c.tipo = EstadoCasilla(estado["tipo"][y][x])
                c.humedad = estado["humedad"][y][x]
                c.alimento = estado["alimento"][y][x]
                c.tick_inicio_llamas = estado["tick_inicio_llamas"][y][x]
                c.tick_quemada = estado["tick_quemada"][y][x]
                previa = estado["vegetacion_previa"][y][x]
                c.vegetacion_previa = None if previa is None else EstadoCasilla(previa)
        return mapa
