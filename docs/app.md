# App (Grupo C)

La **aplicación**: lo que ve y usa la persona, más lo necesario para que funcione sin congelarse y sin perder el trabajo: el hilo que corre el motor, el guardado, la configuración y los contratos. Código en `src/simulador/app/`, `src/simulador/contratos/` y `src/simulador/configuracion/app.py`; pruebas en `tests/app/`.

## Piezas

| Pieza | Dónde | Qué hace |
|---|---|---|
| Contratos | `contratos/` | `Motor` (clase abstracta), comandos, instantánea, avisos, errores, contrato de almacenamiento y `MotorFalso`. Ver [`contratos.md`](contratos.md). |
| Ejecutor | `app/ejecutor/` | Hilo que avanza el motor a la velocidad elegida y entrega instantáneas. |
| Almacenamiento | `app/almacenamiento/` | Guardado en SQLite (`AlmacenamientoSqlite`), versión en memoria para pruebas y rutas de datos. |
| Editor de mapa | `app/editor/` | Lógica del editor: pincel, deshacer y rehacer. |
| Interfaz | `app/interfaz/` | Pantallas, ventana de simulación, visor del mapa, inspector, panel de eventos, especies. |
| Aplicación | `app/aplicacion.py` | Arma las ventanas y conecta Ejecutor, almacenamiento y motor. |
| Series | `app/registro_series.py` | Series completas por especie para las gráficas (se alimenta tick a tick desde el ejecutor). |
| Errores | `app/registro_errores.py` | Módulo para escribir errores inesperados en `errores.log` y armar el mensaje al usuario. Aún no está conectado al hilo del motor. |
| Configuración | `configuracion/app.py` | Parámetros de la app con rangos validados. |

## El Ejecutor

El motor corre en un **hilo propio**; solo ese hilo lo llama.

1. Toma los comandos de una cola y los aplica, **incluso en pausa**.
2. Si no está en pausa: `motor.avanzar()` → instantánea → la deja disponible bajo un candado y acumula los avisos.
3. Duerme lo que falta para cumplir la velocidad (1 a 30 ticks por segundo); si el motor no alcanza, no acumula atraso.
4. Guarda cada **1000 ticks**, al pausar, al cerrar y cuando el usuario pulsa *Guardar*.

La ventana lee la última instantánea con un temporizador de ~30 FPS, sin esperar al motor. Si el motor rechaza una orden, el error se guarda y la ventana lo muestra; una excepción inesperada detiene el hilo y el ejecutor la conserva (`fallo`). Estados del Ejecutor: **pausado** (inicial) ⇄ **ejecutando** → **detenido**.

`alAvanzar(escucha)` permite registrar funciones que reciben la instantánea de *cada* tick (la usa `RegistroSeries`).

## Guardado y carga

- El motor entrega su estado como JSON canónico comprimido con zlib y versionado.
- `AlmacenamientoSqlite` lo guarda como BLOB en la tabla `simulaciones` (`id`, `nombre`, `nombre_clave` único sin distinguir mayúsculas, `tick`, `velocidad`, `fecha_guardado`, `estado`) con transacciones, y usa un candado para que el hilo del ejecutor y la interfaz compartan la conexión.
- Ruta: `%LOCALAPPDATA%\Simulador\biblioteca.db` o la carpeta de la variable `SIMULADOR_CARPETA_DATOS`.
- Nombre de una simulación: de 1 a 60 caracteres, sin espacios en los extremos.

## Interfaz

**Flujo:** menú principal → nueva simulación (nombre + editor de mapa) o cargar → ventana de simulación; la ventana de especies se abre aparte.

**Ventana de simulación:**

- **Visor del mapa** (pyqtgraph): terreno como imagen con tabla de colores y criaturas como puntos coloreados por especie; zoom 1× a 8× con la rueda y desplazamiento arrastrando.
- **Barra de estado:** tick, estación, temperatura, población y cupo.
- **Controles:** pausar y reanudar, velocidad (1–30), nutrientes, guardar (muestra “Guardando…” y luego “Guardado (tick N)”), renombrar y eliminar.
- **Panel de eventos:** botones de sequía, lluvia e incendio (para el incendio se elige la casilla en el mapa; Esc cancela), eventos activos con botón de cancelar y mensajes de error que se quitan solos.
- **Inspector:** al hacer clic en una casilla muestra su terreno y, si hay una criatura, su especie y la población de la especie.

**Editor de mapa:** pincel de 1 a 5 casillas, deshacer y rehacer (50 pasos); al confirmar se crea el motor con ese terreno.

**Especies:** lista (máximo 12 activas), formulario de creación (dieta y, en modo avanzado, S, V y R con rangos validados; el color se asigna solo y se muestra antes de crear) y detalle con gráficas de población y promedios, y botones para agregar (con opción de promedios actuales), quitar, extinguir o eliminar.

## Integración

`integracion/simulador_ecosistema.py` implementa `Motor`: junta el ciclo de Ecosistema, la población de Vida y el adaptador de mapa, recibe los comandos, avanza el tick en el orden de [`arquitectura.md`](arquitectura.md) y fabrica la instantánea. `integracion/mapa_vida.py` adapta el mapa real al puerto `MapaPuerto` (con una copia NumPy del alimento para la percepción rápida).

## Configuración

`ConfiguracionApp` define cada parámetro con valor y rango (`campo(...)`) y se valida al crearse (por ejemplo, velocidad mínima ≤ inicial ≤ máxima). `configuracion/por_defecto.toml` debe coincidir con el código; una prueba lo comprueba.

| Parámetro | Valor |
|---|---|
| Velocidad mínima / inicial / máxima | 1 / 10 / 30 ticks por segundo |
| Autoguardado | cada 1000 ticks |
| Zoom del mapa | 1× a 8× |
| Pincel / pasos de deshacer | 1 a 5 / 50 |
| Largo máximo del nombre | 60 |

## Pruebas

Contratos, ejecutor, almacenamiento (SQLite y memoria con la misma batería), editor de mapa, configuración, registro de errores y ventanas. Las pruebas de interfaz usan `pytest-qt` en modo `offscreen` (sin abrir ventanas). `MotorFalso` permite construir y probar la interfaz sin el motor real.

## Límites conocidos

- El registro de errores en archivo existe pero falta conectarlo al hilo del motor.
- Con muchas criaturas, la velocidad real puede quedar por debajo del tope de 30 ticks por segundo.
- La instantánea no trae energía ni edad por criatura, por eso el inspector muestra poco de cada individuo.
