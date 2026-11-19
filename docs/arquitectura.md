# Arquitectura

Visión general de cómo encajan las piezas. Los detalles de cada grupo están en [`ecosistema.md`](ecosistema.md), [`vida.md`](vida.md) y [`app.md`](app.md); las interfaces entre grupos, en [`contratos.md`](contratos.md).

## 1. Capas y dependencias

```
        ┌──────────────────────────── app/ (Grupo C) ────────────────────────────┐
        │  ventanas (PySide6 + pyqtgraph) · Ejecutor (hilo) · guardado SQLite    │
        └───────────────┬────────────────────────────────────────────────────────┘
                        │ usa solo la clase abstracta Motor, comandos e instantáneas
                 ┌──────▼──────┐
                 │  contratos/ │  Motor · comandos · Instantanea · avisos · errores · Almacenamiento
                 └──────▲──────┘
                        │ implementa Motor
              ┌─────────┴──────────┐
              │   integracion/     │  SimuladorEcosistema + adaptador MapaVida
              └───┬────────────┬───┘
                  │            │
        ┌─────────▼───┐   ┌────▼────────┐
        │ ecosistema/ │   │    vida/    │  Vida solo conoce el puerto MapaPuerto
        │ (Grupo A)   │   │  (Grupo B)  │
        └─────────────┘   └─────────────┘
```

Reglas que se verifican automáticamente (`lint-imports`):

- `ecosistema/` y `vida/` **no importan** `app/`, PySide6 ni pyqtgraph: el motor corre sin interfaz.
- `vida/` no importa el mapa de Ecosistema: recibe cualquier objeto que cumpla `MapaPuerto`. El adaptador `integracion/mapa_vida.py` (`MapaVida`) traduce el mapa real a ese contrato.

## 2. Qué ocurre en un tick

`SimuladorEcosistema.avanzar()` ejecuta siempre el mismo orden:

| Paso | Quién | Qué ocurre |
|---|---|---|
| 0 | Integración | Se aplican las órdenes pendientes (fijar nutrientes). |
| 1 | Ecosistema · Reloj | Avanza el tick; de él salen la estación y la temperatura. |
| 2 | Ecosistema · Eventos | Empiezan o terminan sequía y lluvia; se sortea el foco natural de incendio. |
| 4 | Ecosistema · Fuego | Autómata celular: se propagan y se apagan las llamas. |
| 5 | Ecosistema · Vegetación | Humedad, regeneración de comida y crecimiento. |
| 6 | Integración | Las criaturas sobre casillas en llamas mueren. |
| 7 | Vida | Cada criatura juega su turno: percibe, decide, actúa, gasta energía, envejece. |
| 8 | Integración | Se generan los avisos para la interfaz. |

(`CicloTick` ejecuta los pasos 1 y 2 y luego los pasos registrados por número: fuego = 4, vegetación = 5.)

## 3. Órdenes del usuario

La interfaz nunca modifica el motor: envía **comandos** inmutables (`CrearEspecie`, `AgregarCriaturas`, `ProvocarEvento`, `FijarNutrientes`…).

- Las órdenes sobre **especies y criaturas** se aplican al instante, también con la simulación en pausa.
- Los **eventos e incendios** se encolan en sus gestores y actúan al inicio del tick siguiente.
- Un comando inválido lanza `ComandoInvalido` y no cambia nada; la interfaz muestra el motivo.

## 4. Hilos

El **Ejecutor** (`app/ejecutor/`) corre el motor en un hilo propio para que la ventana no se congele:

1. toma los comandos de una cola y los aplica (incluso en pausa);
2. si no está en pausa, avanza un tick, toma la instantánea y la deja disponible bajo un candado;
3. duerme lo necesario para cumplir la velocidad elegida (1 a 30 ticks por segundo) sin acumular atraso;
4. guarda cada 1000 ticks, al pausar, al cerrar y cuando el usuario lo pide.

La ventana lee la última instantánea con un temporizador de unos 30 FPS: el dibujo y la simulación van desacoplados. Solo el hilo del ejecutor llama al motor.

## 5. Guardado

- El motor serializa su estado completo (mapa, reloj, eventos, fuego, vegetación, especies, criaturas y generadores aleatorios) a **JSON canónico**, lo comprime con **zlib** y le pone un número de versión.
- `AlmacenamientoSqlite` guarda ese contenido como BLOB en la tabla `simulaciones`; las escrituras van en transacción (se aplican todas o ninguna).
- La **huella** (`huellaEstado`) es el SHA-256 del JSON canónico: dos motores con el mismo estado dan la misma huella.

## 6. Determinismo

Con la misma semilla y las mismas órdenes en los mismos ticks, la simulación da exactamente el mismo resultado:

- Ecosistema usa un generador de NumPy y Vida uno de `random.Random`, ambos con la semilla de la simulación.
- Cada paso consume una cantidad **fija** de números aleatorios por tick, haya fuego o no (eventos: 5; fuego: 2·ancho·alto + 1; vegetación: ancho·alto).
- El orden de los turnos de las criaturas se baraja con el generador de Vida.

## 7. Configuración

Ningún parámetro está escrito a mano en la lógica:

| Archivo | Contenido |
|---|---|
| `configuracion/ecosistema.py` | Calendario, eventos, fuego, vegetación |
| `vida/config.py` (`ConfigVida`) | Energía, metabolismo, herencia, vejez, cupo |
| `configuracion/app.py` | Velocidad, zoom, editor, guardado |
| `configuracion/por_defecto.toml` | Valores por defecto de la sección de App (una prueba comprueba que coincida con el código) |

## 8. Rendimiento

El costo dominante es la **percepción** de las criaturas. La búsqueda de plantas usa NumPy (`MapaPuerto.plantas_en_radio`, opcional) y existe una versión de referencia más lenta; una prueba comprueba que ambas dan exactamente el mismo estado. Orden de magnitud medido: unos 21–29 ms por tick con ~240 criaturas y ~48 ms con 500, es decir, unos 20 ticks por segundo con el cupo lleno.
