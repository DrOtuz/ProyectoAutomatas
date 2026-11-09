E_MAX = 100
ENERGIA_CRIA = 30                      # energía con la que nace una criatura
A = 0.30                               # costo basal (estar vivo)
C = 0.05                               # costo por casilla de visión
K = 0.15                               # costo de moverse (va con V^2)
 
# Factor de temperatura: f_T = 1 + ALFA * ((T - T_OPT) / 10)^2
T_OPT = 22                             # temperatura ideal (°C)
ALFA = 0.15
ETA_PLANTA_HERBIVORO = 0.50
ETA_PLANTA_OMNIVORO = 0.35
ETA_CARNE_CARNIVORO = 0.80
ETA_CARNE_OMNIVORO = 0.60
RATIO_DEPREDACION = 1.2
UMBRAL_REPRODUCCION_PCT = 0.70         
UMBRAL_SALIDA_PAREJA_PCT = 0.50       
UMBRAL_REPRODUCCION = UMBRAL_REPRODUCCION_PCT * E_MAX
UMBRAL_SALIDA_PAREJA = UMBRAL_SALIDA_PAREJA_PCT * E_MAX
 
PROB_INERCIA = 0.7                     #Probabilidad de conservar dirección
VOLVER_A_ALIMENTO_TRAS_REPRODUCIR = False
 
COSTO_REPRODUCCION = 25                #
SIGMA = 0.05                           #Mutaciones
MAX_CRIATURAS = 1000                   
PLANTILLAS_ESPECIE = {
    "herbivoro": {"tamano": 1.0, "velocidad": 1.0, "vision": 4},
    "omnivoro":  {"tamano": 1.5, "velocidad": 1.2, "vision": 5},
    "carnivoro": {"tamano": 2.5, "velocidad": 1.6, "vision": 6},
}
VARIACION_INICIAL = 0.10               # ±10 % individual sobre la plantilla al crear una especie
PASTO_BIOMASA_MAX = 30
PASTO_REGENERACION = 1                 # u por tick
ARBOL_BIOMASA_MAX = 60
ARBOL_REGENERACION = 2 