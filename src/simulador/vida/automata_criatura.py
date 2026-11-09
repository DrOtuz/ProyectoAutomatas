import random
from typing import NamedTuple, Optional
 
from .config import UMBRAL_REPRODUCCION, UMBRAL_SALIDA_PAREJA
from .criatura import EstadoCriatura, distancia_chebyshev
 
# Nombres de tipo que el autómata le pide al mapa en buscar_en_radio.
# Si el Subgrupo A usa otros nombres, se cambian solo aquí.
TIPO_COMIDA = "comida"
TIPO_FUEGO = "fuego"
 
# Probabilidad de conservar la dirección anterior al explorar
# (conviene moverla a config.py).
PROB_INERCIA = 0.7
 
# Las 8 direcciones posibles
_DIRECCIONES = [
    (dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)
]
 
 
class Objetivo(NamedTuple):
    clase: str                      # "planta", "presa" o "pareja"
    x: int
    y: int
    criatura: Optional[object]      # la presa o la pareja (None si es planta)
    valor: float                    # ganancia / (distancia + 1) para comida
 
 
class AutomataCriatura:
    """
    Máquina de estados de las criaturas. NO guarda estado por criatura: el
    estado, la intención y la energía viven en Criatura. Basta con UNA
    instancia compartida por toda la población.
 
    Prioridad: HUIR > BUSCAR_ALIMENTO / BUSCAR_PAREJA > EXPLORAR.
 
    Interfaz que necesita (ver notas de entrega):
      mapa.es_valida(x, y) -> bool
      mapa.buscar_en_radio(x, y, radio, tipo) -> list[(x, y)]
      mapa.biomasa_en(x, y) -> float
      mapa.consumir_biomasa(x, y) -> float      (deja la casilla en 0)
      poblacion.criaturas_en_radio(x, y, radio) -> list[Criatura]
      poblacion.reproducir(criatura, pareja) -> bool
    """
 
    def __init__(
        self,
        rng=None,
        prob_inercia=PROB_INERCIA,
        volver_a_alimento_tras_reproducir=False,
    ):
        # Pasar el mismo random.Random(semilla) que usa Poblacion para que
        # las pruebas sean repetibles.
        self.rng = rng if rng is not None else random.Random()
        self.prob_inercia = prob_inercia  # P(seguir recto) al explorar
        # Decisión pendiente (sección 12): evita reproducciones en cadena.
        self.volver_a_alimento_tras_reproducir = volver_a_alimento_tras_reproducir
 
    # Turno completo de una criatura
 
    def turno(self, criatura, mapa, poblacion, temperatura):
        """
        decidir estado -> actuar -> cobrar metabolismo.
        El gasto se cobra al final porque depende de si se movió (m).
        Si la criatura ya murió en este tick (la cazaron), se salta el turno.
        """
        if not criatura.viva:
            return
 
        self._actualizar_intencion(criatura)
 
        # R = visión; vecinas = otras criaturas vivas dentro de R
        radio = int(criatura.estadisticas.vision)
        vecinas = [
            o
            for o in poblacion.criaturas_en_radio(criatura.x, criatura.y, radio)
            if o is not criatura and o.viva
        ]
 
        se_movio = self._decidir_y_actuar(criatura, vecinas, mapa, poblacion, radio)
        criatura.actualizar_metabolismo(temperatura, se_movio)
 
    # Decisión
 
    def _actualizar_intencion(self, c):
        """
        Histéresis: entra a buscar pareja con e >= 70 y solo sale con e < 50.
        Al salir, la intención pasa a ALIMENTO y se mantiene hasta volver a
        llegar a 70 (no hay que decidir nada especial entre 50 y 70).
        """
        if c.intencion == EstadoCriatura.BUSCAR_PAREJA:
            if c.energia < UMBRAL_SALIDA_PAREJA:
                c.intencion = EstadoCriatura.BUSCAR_ALIMENTO
        elif c.energia >= UMBRAL_REPRODUCCION:
            c.intencion = EstadoCriatura.BUSCAR_PAREJA
 
    def _decidir_y_actuar(self, c, vecinas, mapa, poblacion, radio):
        # 1) HUIR tiene prioridad absoluta
        amenazas = self._amenazas(c, vecinas, mapa, radio)
        if amenazas:
            c.estado = EstadoCriatura.HUIR
            return c.mover_alejando(amenazas, mapa.es_valida)
 
        # 2) Buscar lo que necesita
        if c.intencion == EstadoCriatura.BUSCAR_PAREJA:
            objetivo = self._mejor_pareja(c, vecinas)
        else:
            objetivo = self._mejor_comida(c, vecinas, mapa, radio)
 
        # 3) Sin objetivo visible: explorar (la intención se conserva)
        if objetivo is None:
            c.estado = EstadoCriatura.EXPLORAR
            return self._explorar(c, mapa)
 
        c.estado = c.intencion
        return self._ir_hacia(c, objetivo, mapa, poblacion)
 
    # Percepción
 
    def _amenazas(self, c, vecinas, mapa, radio):
        """
        Posiciones peligrosas dentro de R: criaturas de otra especie que
        pueden cazarme (dieta con carne y S >= 1.2 * mi S) y fuego.
        """
        posiciones = [(o.x, o.y) for o in vecinas if o.puede_cazar_a(c)]
        posiciones.extend(mapa.buscar_en_radio(c.x, c.y, radio, TIPO_FUEGO))
        return posiciones
 
    def _mejor_comida(self, c, vecinas, mapa, radio):
        """Maximiza ganancia / (distancia + 1) entre plantas y presas."""
        S = c.estadisticas.tamano
        mejor = None
 
        # Plantas: solo si la dieta las admite
        if c.eficiencia_planta > 0:
            casillas = set(mapa.buscar_en_radio(c.x, c.y, radio, TIPO_COMIDA))
            casillas.add((c.x, c.y))  # también la casilla donde está parada
            for x, y in sorted(casillas):  # sorted: resultados repetibles
                biomasa = mapa.biomasa_en(x, y)
                if biomasa <= 0:
                    continue
                # ganancia% = ETA * biomasa / S (igual que Criatura.comer)
                ganancia = c.eficiencia_planta * biomasa / S
                valor = ganancia / (c.distancia_a(x, y) + 1)
                mejor = self._elegir(mejor, Objetivo("planta", x, y, None, valor), c)
 
        # Presas: solo si la dieta incluye carne
        if c.eficiencia_carne > 0:
            for o in vecinas:
                if not c.puede_cazar_a(o):
                    continue
                # ganancia% = 100 * ETA * S_presa / S (igual que Criatura.depredar)
                ganancia = 100 * c.eficiencia_carne * o.estadisticas.tamano / S
                valor = ganancia / (c.distancia_a(o.x, o.y) + 1)
                mejor = self._elegir(mejor, Objetivo("presa", o.x, o.y, o, valor), c)
 
        return mejor
 
    @staticmethod
    def _elegir(actual, candidato, c):
        """Mayor valor; a igualdad, el más cercano."""
        if actual is None or candidato.valor > actual.valor:
            return candidato
        if candidato.valor == actual.valor and c.distancia_a(
            candidato.x, candidato.y
        ) < c.distancia_a(actual.x, actual.y):
            return candidato
        return actual
 
    @staticmethod
    def es_pareja_elegible(c, otra):
        """
        Misma especie, viva, que también busque pareja y que no esté huyendo.
        Se usa la INTENCIÓN (no el estado) para que dos criaturas que exploran
        buscando pareja puedan encontrarse. Poblacion.reproducir puede
        reutilizar esta función para validar.
        """
        return (
            otra.viva
            and otra is not c
            and otra.especie_id == c.especie_id
            and otra.intencion == EstadoCriatura.BUSCAR_PAREJA
            and otra.estado != EstadoCriatura.HUIR
        )
 
    def _mejor_pareja(self, c, vecinas):
        candidatas = [o for o in vecinas if self.es_pareja_elegible(c, o)]
        if not candidatas:
            return None
        # La más cercana; a igualdad, la de menor id (determinista)
        o = min(candidatas, key=lambda o: (c.distancia_a(o.x, o.y), o.id))
        return Objetivo("pareja", o.x, o.y, o, 0.0)  # valor no se usa
 
    # Acción
 
    def _ir_hacia(self, c, obj, mapa, poblacion):
        """Devuelve True si la criatura se movió este tick."""
        d = c.distancia_a(obj.x, obj.y)
 
        if obj.clase == "pareja":
            if d <= 1:
                # Poblacion valida espacio libre y el límite de 1000, y cobra
                # el costo a AMBOS padres (solo si la reproducción ocurre).
                if poblacion.reproducir(c, obj.criatura):
                    if self.volver_a_alimento_tras_reproducir:
                        c.intencion = EstadoCriatura.BUSCAR_ALIMENTO
                        obj.criatura.intencion = EstadoCriatura.BUSCAR_ALIMENTO
                return False  # reproducirse ocupa el tick: m = 0
            return c.mover_hacia((obj.x, obj.y), mapa.es_valida)
 
        if obj.clase == "planta":
            if d == 0:
                c.comer(mapa.consumir_biomasa(c.x, c.y))
                return False  # comer ocupa el tick: m = 0
            return c.mover_hacia((obj.x, obj.y), mapa.es_valida)
 
        # Presa: si alcanza d menor o igual a los  pasos entra a su casilla y se la come
        # si no, avanza V casillas hacia ella.
        presa = obj.criatura
        se_movio = False
        if d > 0:
            pasos = c.consumir_pasos()
            se_movio = c.mover_hacia((presa.x, presa.y), mapa.es_valida, pasos=pasos)
        # Llegó a su casilla: la caza
        if (c.x, c.y) == (presa.x, presa.y):
            c.depredar(presa)
        return se_movio
 
    def _explorar(self, c, mapa):
        """Paso al azar que tiende a conservar la dirección anterior."""
        # Solo direcciones cuya casilla destino es válida
        validas = [
            (dx, dy)
            for dx, dy in _DIRECCIONES
            if mapa.es_valida(c.x + dx, c.y + dy)
        ]
        if not validas:
            return False  # encerrada
 
        previa = c.direccion_previa
        if previa in validas and self.rng.random() < self.prob_inercia:
            direccion = previa
        else:
            direccion = self.rng.choice(validas)
        return c.mover(direccion, mapa.es_valida)