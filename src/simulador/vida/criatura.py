
from enum import Enum
 
from .config import (
    E_MAX,
    ENERGIA_CRIA,
    A,
    C,
    K,
    T_OPT,
    ALFA,
    COSTO_REPRODUCCION,
    RATIO_DEPREDACION,
    ETA_PLANTA_HERBIVORO,
    ETA_PLANTA_OMNIVORO,
    ETA_CARNE_CARNIVORO,
    ETA_CARNE_OMNIVORO,
)
 
 
class EstadoCriatura(Enum):
    HUIR = "huir"
    BUSCAR_ALIMENTO = "buscar_alimento"
    BUSCAR_PAREJA = "buscar_pareja"
    EXPLORAR = "explorar"
    MUERTA = "muerta"
 
 
class Dieta(Enum):
    HERBIVORO = "herbivoro"
    CARNIVORO = "carnivoro"
    OMNIVORO = "omnivoro"
 
 
# Eficiencia de absorción por dieta (0 = no puede comer eso)
_ETA_PLANTA = {
    Dieta.HERBIVORO: ETA_PLANTA_HERBIVORO,
    Dieta.OMNIVORO: ETA_PLANTA_OMNIVORO,
    Dieta.CARNIVORO: 0.0,
}
_ETA_CARNE = {
    Dieta.CARNIVORO: ETA_CARNE_CARNIVORO,
    Dieta.OMNIVORO: ETA_CARNE_OMNIVORO,
    Dieta.HERBIVORO: 0.0,
}
_EPS = 1e-9
 
# Las 8 direcciones posibles
_DIRECCIONES = [
    (dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)
]
 
def _signo(n):
    return (n > 0) - (n < 0)
 
 
def distancia_chebyshev(x1, y1, x2, y2):
    return max(abs(x1 - x2), abs(y1 - y2))
 
 
class Criatura:
    """
    Una criatura individual: posición, energía, estado, metabolismo y
    acciones (mover, comer, depredar, pagar reproducción).
 
    La decisión de qué hacer corresponde a automata_criatura y a otros. Aquí únicamente vive el cómo
    """
 
    def __init__(
        self,
        id,
        especie_id,
        pos_x,
        pos_y,
        estadisticas,
        dieta,
        energia=ENERGIA_CRIA,
        estado=EstadoCriatura.EXPLORAR,
        direccion_previa=(0, 0),
        acumulador_velocidad=0.0,
        intencion=EstadoCriatura.BUSCAR_ALIMENTO,
    ):
        self.id = id
        self.especie_id = especie_id
        self.x = pos_x
        self.y = pos_y
        self.estadisticas = estadisticas  # S, V, R
        self.dieta = dieta                # fija por especie, no muta
        self.energia = energia
        self.estado = estado
        self.direccion_previa = direccion_previa
        self.acumulador_velocidad = acumulador_velocidad
        # EXPLORAR guarda qué buscaba (BUSCAR_ALIMENTO o BUSCAR_PAREJA)
        self.intencion = intencion
 
    @property
    def viva(self):
        return self.estado != EstadoCriatura.MUERTA
 
    @property
    def eficiencia_planta(self):
        return _ETA_PLANTA[self.dieta]
 
    @property
    def eficiencia_carne(self):
        return _ETA_CARNE[self.dieta]
 
    def distancia_a(self, x, y):
        return distancia_chebyshev(self.x, self.y, x, y)
 
    def puede_cazar_a(self, otra):
        """
        Presa elegible: viva, de otra especie, con S_depredador >= 1.2 * S_presa
        y dieta que incluya carne. Si A.puede_cazar_a(B), entonces A es una
        amenaza para B.
        """
        return (
            self.viva
            and otra.viva
            and self.eficiencia_carne > 0
            and self.especie_id != otra.especie_id
            and self.estadisticas.tamano
            >= RATIO_DEPREDACION * otra.estadisticas.tamano
        )
 
    def consumir_pasos(self):
        """
        Casillas que puede avanzar por tick
        """
        self.acumulador_velocidad += self.estadisticas.velocidad
        pasos = int(self.acumulador_velocidad + _EPS)
        self.acumulador_velocidad = max(0.0, self.acumulador_velocidad - pasos)
        return pasos
 
    def _dar_paso(self, dx, dy, es_valida):
        nueva_x = self.x + dx
        nueva_y = self.y + dy
        if not es_valida(nueva_x, nueva_y):
            return False
        self.x = nueva_x
        self.y = nueva_y
        self.direccion_previa = (dx, dy)
        return True
 
    def mover(self, direccion, es_valida, pasos=None):
        """
        Avanza en una dirección fija.
        Devuelve True si se movio.
        """
        dx, dy = direccion
        if dx not in (-1, 0, 1) or dy not in (-1, 0, 1):
            raise ValueError("Dirección no válida")
        if dx == 0 and dy == 0:
            raise ValueError("La dirección no puede ser (0, 0)")
 
        if pasos is None:
            pasos = self.consumir_pasos()
 
        se_movio = False
        for _ in range(pasos):
            if not self._dar_paso(dx, dy, es_valida):
                break
            se_movio = True
        return se_movio
 
    def mover_hacia(self, objetivo, es_valida, pasos=None):
        """
        Avanza hacia (x, y) recalculando la dirección en cada paso, sin pasarse
        del objetivo. Si el paso directo está bloqueado, prueba cada eje por
        separado. Sirve para ir a comida, a una pareja o para perseguir.
        """
        tx, ty = objetivo
        if pasos is None:
            pasos = self.consumir_pasos()
 
        se_movio = False
        for _ in range(pasos):
            dx = _signo(tx - self.x)
            dy = _signo(ty - self.y)
            if dx == 0 and dy == 0:
                break
            if self._dar_paso(dx, dy, es_valida):
                se_movio = True
                continue
            if dx != 0 and dy != 0:
                if self._dar_paso(dx, 0, es_valida) or self._dar_paso(0, dy, es_valida):
                    se_movio = True
                    continue
            break
        return se_movio
 
    def mover_alejando(self, amenazas, es_valida, pasos=None):
        """
        HUIR: en cada paso elige la casilla que más aumenta la distancia a la
        amenaza MÁS CERCANA (desempata por distancia euclidiana). Si ningún
        paso mejora la situación (acorralada), se queda quieta.
        `amenazas` es una lista de (x, y): criaturas peligrosas y/o fuego.
        """
        if not amenazas:
            return False
        if pasos is None:
            pasos = self.consumir_pasos()
 
        def clave(x, y):
            return (
                min(distancia_chebyshev(x, y, ax, ay) for ax, ay in amenazas),
                min((x - ax) ** 2 + (y - ay) ** 2 for ax, ay in amenazas),
            )
 
        se_movio = False
        for _ in range(pasos):
            clave_actual = clave(self.x, self.y)
            mejor_dir, mejor_clave = None, clave_actual
            for dx, dy in _DIRECCIONES:
                nx, ny = self.x + dx, self.y + dy
                if not es_valida(nx, ny):
                    continue
                c = clave(nx, ny)
                if c > mejor_clave:
                    mejor_dir, mejor_clave = (dx, dy), c
            if mejor_dir is None:
                break
            self._dar_paso(*mejor_dir, es_valida)
            se_movio = True
        return se_movio
 
    @staticmethod
    def factor_temperatura(temperatura):
        return 1 + ALFA * ((temperatura - T_OPT) / 10) ** 2
 
    def calcular_gasto_metabolico(self, temperatura, se_movio):
        """
        gasto = f_T * S^(-0.25) * (A + C*R + K*V^2*m)
        m = 1 si se movió este tick, 0 si se quedó quieta.
        """
        S = self.estadisticas.tamano
        V = self.estadisticas.velocidad
        R = self.estadisticas.vision
        m = 1 if se_movio else 0
 
        return (
            self.factor_temperatura(temperatura)
            * (S ** -0.25)
            * (A + C * R + K * (V ** 2) * m)
        )
 
    def actualizar_metabolismo(self, temperatura, se_movio):
        """
        
        """
        if not self.viva:
            return 0.0
 
        gasto = self.calcular_gasto_metabolico(temperatura, se_movio)
        self.energia = max(0.0, self.energia - gasto)
 
        if self.energia <= 0:
            self.morir()
 
        return gasto
 
    def _ganar_energia(self, ganancia):
        energia_anterior = self.energia
        self.energia = min(E_MAX, self.energia + ganancia)
        return self.energia - energia_anterior
 
    def comer(self, biomasa_consumida):
        """
        Come la biomasa de la casilla .
        ganancia% = ETA * biomasa / S. Devuelve la energía realmente ganada.
        """
        eficiencia = self.eficiencia_planta
        if not self.viva or biomasa_consumida <= 0 or eficiencia <= 0:
            return 0.0
 
        ganancia = eficiencia * biomasa_consumida / self.estadisticas.tamano
        return self._ganar_energia(ganancia)
 
    def depredar(self, presa):
        """
        Se come a la presa completa.
        ganancia% = 100 * ETA * S_presa / S_depredador.
        Devuelve 0 si la presa no es elegible (muerta, misma especie,
        demasiado grande o dieta sin carne) y no la mata en tal caso.
        """
        if not self.puede_cazar_a(presa):
            return 0.0
 
        ganancia = (
            100
            * self.eficiencia_carne
            * presa.estadisticas.tamano
            / self.estadisticas.tamano
        )
        presa.morir()
        return self._ganar_energia(ganancia)
 
    def puede_pagar_reproduccion(self):
        return self.viva and self.energia >= COSTO_REPRODUCCION
 
    def pagar_reproduccion(self):
        """
        Cobra el costo de reproducirse.
        """
        if not self.puede_pagar_reproduccion():
            return False
        self.energia -= COSTO_REPRODUCCION
        return True
 
    def morir(self):
        self.estado = EstadoCriatura.MUERTA