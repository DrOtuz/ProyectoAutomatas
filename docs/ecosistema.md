# Ecosistema (Grupo A)

El **mundo**: mapa, paso del tiempo, clima, eventos naturales, fuego y vegetación (que es la comida de las criaturas). Código en `src/simulador/ecosistema/`; parámetros en `src/simulador/configuracion/ecosistema.py`; pruebas en `tests/ecosistema/`.

## Archivos

| Archivo | Contenido |
|---|---|
| `mapa.py` | `Casilla` (tipo, humedad, alimento…) y `Mapa` (cuadrícula 100 × 100, vecinas, radios, conversión a y desde arreglo y estado). |
| `reloj.py` | Tick, estación (cada 500 ticks) y temperatura (con ciclo de día de 24 ticks). |
| `eventos.py` | `GestorEventos`: sequía, lluvia y foco natural de incendio; órdenes del usuario. |
| `fuego.py` | `AutomataFuego`: el autómata celular del incendio. |
| `vegetacion.py` | Humedad, regeneración de comida y crecimiento tierra → pasto → árbol. |
| `ciclo.py` | `CicloTick`: orden fijo de pasos con un generador aleatorio único. |

## Estados de la casilla

| Estado | Significado | ¿Se quema? |
|---|---|---|
| Tierra | Suelo desnudo, sin comida | No |
| Agua | Lagos; no transitables; dan humedad alrededor; nunca cambia | No |
| Pasto | Vegetación baja; comida máxima 30 u | Sí |
| Árbol | Vegetación alta; comida máxima 60 u | Sí |
| Llamas | Casilla ardiendo | — |
| Quemada | Ya ardió; sin comida; se regenera | No |

Cada casilla guarda además su **humedad** (0 a 1) y su **alimento**. El editor solo pinta tierra y agua; al empezar, la vegetación se **siembra** con más densidad cerca del agua.

## El autómata celular del fuego

- Cuadrícula de casillas con un número finito de estados, **vecindad de Moore** (8 vecinas; configurable a 4) y regla local probabilística.
- **Doble buffer:** todas las decisiones del tick se toman con el estado del *inicio* del tick; las casillas que se prenden ahora no propagan hasta el siguiente. Así el resultado no depende del orden de recorrido.

| De | A | Cuándo |
|---|---|---|
| Pasto / Árbol | Llamas | Una vecina arde y sale el sorteo, o es el foco de un incendio (manual o natural). |
| Llamas | Quemada | Cumple su duración (3 ticks el pasto, 8 el árbol) o la lluvia la apaga (30 % por tick). |
| Quemada | Tierra | Pasan 150 ticks. |
| Tierra | Pasto | Crecimiento: 0.002 por tick, escalado. |
| Pasto | Árbol | Crecimiento: 0.0005 por tick, escalado. |

**Probabilidad de propagación** para una casilla inflamable con *k* vecinas en llamas:

```
p_vecina = base × (1 − peso_humedad × humedad) × escala      (limitada a [0, 1])
base     = 0.12 (pasto) · 0.08 (árbol)
escala   = factor_temperatura × inflamabilidad_estación × factor_lluvia
factor_temperatura = max(0, 1 + 0.02 × (T − 20))
p        = 1 − (1 − p_vecina)^k          # probabilidad de que al menos una la contagie
```

Las probabilidades base se bajaron (antes 0.30 y 0.20) porque 7 de cada 10 incendios quemaban casi todo el mapa; con los valores actuales la mitad se apaga casi enseguida y los grandes queman hasta un tercio (medido en 20 semillas).

**Incendios provocados:** el usuario elige la casilla en el mapa (el comando admite radio de 0 a 3). Se rechaza si la casilla está fuera del mapa, si no hay casillas inflamables en el área o si ya hay un incendio activo. Se puede cancelar: sus llamas pasan a quemada al inicio del tick siguiente. Los **focos naturales** son aleatorios.

## Reloj, estaciones y temperatura

`temperatura = base de la estación + 3·sin(2π · fase del día) + ajuste por sequía`. Cada estación dura 500 ticks (año de 2000) y el día 24.

| Estación | Temp. base | Humedad | Crecimiento | Inflamabilidad |
|---|---|---|---|---|
| Primavera | 20 °C | 1.0 | 1.2 | 0.8 |
| Verano | 30 °C | 0.7 | 0.8 | 1.5 |
| Otoño | 18 °C | 1.0 | 1.0 | 1.0 |
| Invierno | 10 °C | 0.9 | 0.3 | 0.5 |

La temperatura llega a Vida y cambia el gasto de energía de todas las criaturas.

## Eventos naturales

| Evento | Inicio | Duración | Efectos |
|---|---|---|---|
| **Sequía** | Al azar con probabilidad λ_estación / 500 por tick (más probable en verano); o manual | 0.3 a 0.6 de estación (150–300 ticks) | Humedad −0.35, crecimiento ×0.3, +3 °C, focos naturales de incendio ×3 |
| **Lluvia** | Igual (más probable en otoño); o manual | 0.10 a 0.24 de estación (50–120 ticks) | Humedad +0.35, crecimiento ×1.5, propagación del fuego ×0.3, apaga llamas (30 % por tick) |
| **Incendio** | Foco natural (λ por estación: primavera 0.20, verano 1.00, otoño 0.10, invierno 0.05) o manual | Hasta que no queden llamas | Quema vegetación; mata a las criaturas sobre casillas en llamas |

No se puede provocar un evento del mismo tipo que uno ya activo. Sequía y lluvia pueden coincidir (sus efectos se combinan). Un evento manual pendiente o cancelado se aplica al inicio del tick siguiente.

## Vegetación y comida

- **Humedad base:** 1 sobre el agua, baja linealmente a 0 a 5 casillas (distancia de Chebyshev). La humedad real sigue a su objetivo con inercia 0.1 por tick.
- **Regeneración de comida:** pasto +0.5 u por tick hasta 30; árbol +1.0 u por tick hasta 60, multiplicado por el factor de crecimiento de la estación, el de los eventos y **nutrientes / 50**.
- **Nutrientes** (0 a 100): control global del usuario; con 50 el factor es 1.0.
- **Crecimiento:** tierra → pasto → árbol con probabilidades pequeñas favorecidas por la humedad `(0.5 + humedad)`.
- Una criatura que come en una casilla deja su alimento en 0 y la casilla vuelve a regenerarse.

## Orden del ciclo y determinismo

`CicloTick` ejecuta: reloj → eventos → pasos registrados por orden (4 fuego, 5 vegetación). Cada paso consume una cantidad **fija** de números aleatorios del mismo generador (NumPy), haya o no incendio:

- Eventos: 5 números por tick (inicio de sequía, inicio de lluvia, foco natural, duración de sequía y de lluvia).
- Fuego: 2·ancho·alto + 1 (propagación, lluvia y posición del foco).
- Vegetación: ancho·alto.

Cada pieza vuelca su estado con tipos básicos y se reconstruye (`aEstado` / `cargarEstado`).

## Límites conocidos

- La vegetación tiene solo dos niveles (pasto y árbol) y no retrocede por falta de humedad.
- La humedad depende solo de la distancia al agua, la estación y los eventos.
- Algunos parámetros de fuego y vegetación son valores de partida calibrados con pruebas, no medidas de un modelo real.
