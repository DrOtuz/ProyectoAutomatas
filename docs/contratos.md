# Contratos entre subgrupos

Definen qué ofrece cada grupo a los demás, para trabajar en paralelo sin esperarse. Este documento dice **cómo se usa** cada pieza, no cómo funciona por dentro. El código está en `src/simulador/contratos/` (y en `vida/puertos.py` para el mapa).

## Reglas de redacción y nomenclatura

- Nombres en español, sin tildes ni eñes en el código (en comentarios y documentos sí).
- Clases en `PascalCase`, funciones y métodos en `camelCase`, atributos y variables en `snake_case`, constantes en `MAYUSCULAS_CON_GUION_BAJO`, miembros de `Enum` en minúscula.
- Solo se documenta lo que **cruza fronteras** entre grupos.
- Un cambio de firma o de comportamiento de un contrato requiere discusión previa y la aprobación de los tres líderes (ver `.github/CODEOWNERS`).
- Todo error propio hereda de `ErrorSimulador`.

---

## Aplicación ⇄ motor

### `Motor` (clase abstracta, `contratos/motor.py`)

Lo que la aplicación puede pedirle a la simulación. La implementan `SimuladorEcosistema` (motor real) y `MotorFalso` (para probar la interfaz). Se usa siempre desde **un solo hilo** (el del Ejecutor).

| Método | Descripción |
|---|---|
| `avanzar() -> list[Aviso]` | Avanza un tick y devuelve los avisos ocurridos. |
| `aplicar(comando)` | Valida y ejecuta o encola un comando. Lanza `ComandoInvalido` si trae valores incorrectos (sin cambiar nada) y `ComandoNoSoportado` si el motor no lo implementa. |
| `obtenerInstantanea() -> Instantanea` | Estado visible actual, de solo lectura. |
| `aEstado() -> bytes` | Estado completo serializado (JSON canónico comprimido, con versión). |
| `huellaEstado() -> str` | SHA-256 del estado canónico. Mismo estado, misma huella. |
| `desdeEstado(estado: bytes) -> Motor` | Método de clase: reconstruye un motor desde `aEstado`. |

### Comandos (`contratos/comandos.py`)

Dataclasses inmutables.

| Comando | Campos | Efecto |
|---|---|---|
| `FijarNutrientes` | `nivel` (0–100) | Nivel global de nutrientes; actúa desde el tick siguiente. |
| `ProvocarEvento` | `tipo`, `foco_x`, `foco_y`, `radio` (0–3) | Provoca sequía, lluvia o incendio. El incendio usa el foco (si falta, el motor elige una casilla inflamable al azar). Rechaza un evento del mismo tipo que uno activo. |
| `CancelarEvento` | `tipo` | Termina el evento activo al inicio del tick siguiente. |
| `CrearEspecie` | `nombre`, `cantidad`, `dieta` (`herbivoro`/`omnivoro`/`carnivoro`), `genes` opcional `(tamano, velocidad, vision)` | Crea la especie y coloca sus criaturas. |
| `AgregarCriaturas` | `especie_id`, `cantidad`, `promedio_actual` | Suma individuos hasta el cupo. Con `promedio_actual=True` nacen con los promedios actuales de la especie; si no, con su plantilla original. |
| `EliminarCriaturas` | `especie_id`, `cantidad` | Retira criaturas al azar. |
| `ExtinguirEspecie` | `especie_id` | Retira todas; la especie sigue en la lista como extinguida. |
| `EliminarEspecie` | `especie_id` | Elimina la especie y su historial; su nombre queda bloqueado. |

`TipoEvento` es `sequia`, `lluvia` o `incendio`.

### `Instantanea` (`contratos/instantanea.py`)

Estado visible en un tick. Los arreglos de NumPy se marcan como no escribibles y el motor entrega copias.

| Campo | Contenido |
|---|---|
| `tick`, `estacion`, `temperatura`, `nutrientes`, `cupo` | Reloj y datos globales. |
| `terreno` | Arreglo 100 × 100 `uint8` con códigos de `EstadoCasilla`: tierra 0, agua 1, pasto 2, árbol 3, llamas 4, quemada 5. |
| `criaturas` | Arreglo n × 3 `int32`: x, y, `especie_id`. |
| `especies` | Tuple de `InfoEspecie`: `especie_id`, `nombre`, `color` (índice de la paleta de 12), `poblacion`, `extinguida` y, si el motor los da, promedios de `tamano`, `velocidad`, `vision` y `energia`. |
| `eventos` | Tuple de `InfoEvento`: `tipo`, `ticks_restantes` (sequía y lluvia) o `casillas_en_llamas` (incendio). |

### Avisos (`contratos/avisos.py`)

Devueltos por `avanzar()`: `EventoNaturalIniciado(tipo, origen, tick)`, `EventoNaturalTerminado(tipo, tick, cancelado)`, `CupoAlcanzado(tick, cupo)` y `EspecieExtinguida(especie_id, nombre, tick)`. `OrigenEvento` es `natural` o `manual`.

### Errores (`contratos/errores.py`)

`ErrorSimulador` (base), `ComandoInvalido`, `ComandoNoSoportado`, `NombreInvalido`, `SimulacionNoEncontrada`.

### `Almacenamiento` (`contratos/almacenamiento.py`)

Biblioteca de simulaciones guardadas. Implementaciones: `AlmacenamientoSqlite` y `AlmacenamientoMemoria` (pruebas); una misma batería de pruebas corre contra ambas.

| Método | Descripción |
|---|---|
| `crear(nombre, estado, tick, velocidad)` | Guarda una simulación nueva y devuelve su `ResumenSimulacion`. |
| `guardar(simulacion_id, estado, tick, velocidad)` | Reemplaza el estado guardado. |
| `cargar(simulacion_id) -> bytes` | Devuelve el estado guardado. |
| `listar() -> list[ResumenSimulacion]` | Simulaciones guardadas. |
| `renombrar(simulacion_id, nombre)` / `eliminar(simulacion_id)` | Gestión de la biblioteca. |

`validarNombre(nombre, largo_maximo)`: de 1 a 60 caracteres y sin espacios en los extremos; no puede repetirse otro nombre sin distinguir mayúsculas. `ResumenSimulacion`: `simulacion_id`, `nombre`, `tick`, `fecha_guardado`, `velocidad`.

---

## Vida ⇄ Ecosistema

### `MapaPuerto` (`vida/puertos.py`)

Lo único que Vida necesita del mapa. Cualquier objeto que lo cumpla sirve (el adaptador real es `integracion/mapa_vida.py::MapaVida`; para pruebas, `vida/adaptadores/mapa_falso.py`). Coordenadas `(x, y)`: x es la columna, y la fila.

| Miembro | Descripción |
|---|---|
| `ancho`, `alto` | Dimensiones. |
| `en_limites(x, y)` | ¿Está dentro del mapa? |
| `es_transitable(x, y)` | ¿Puede pisarla una criatura? (el agua no) |
| `biomasa_en(x, y)` | Comida disponible en unidades u (0 si no hay). |
| `consumir_biomasa(x, y)` | Quita toda la comida y devuelve cuánta había. |
| `hay_fuego(x, y)` | ¿Está en llamas? |
| `buscar_en_radio(x, y, radio, tipo)` | Casillas a distancia de Chebyshev ≤ `radio` con comida (`TIPO_COMIDA`) o fuego (`TIPO_FUEGO`). |
| `plantas_en_radio(x, y, radio)` | **Opcional.** Devuelve arreglos `(xs, ys, biomasa)` de las casillas con comida, en orden fila a fila; Vida lo usa si existe (vía rápida con NumPy) y si no, recorre con `buscar_en_radio`. |

### `Poblacion` (`vida/poblacion.py`)

| Método | Descripción |
|---|---|
| `actualizar(mapa, temperatura)` | Un tick de Vida. |
| `crear_especie(...)`, `agregar_individuos(...)`, `eliminar_criaturas(...)`, `extinguir_especie(...)`, `eliminar_especie(...)` | Operaciones sobre especies y criaturas. |
| `eliminar_en(x, y)` | Mata a las criaturas de una casilla (la usa el fuego). |
| `snapshot()` | Resumen por especie: población y promedios de S, V, R y energía. |
| `a_dict()` / `desde_dict()` | Guardado y carga. |

### `Historial` (`vida/historial.py`)

Series por especie (población y promedios) para las gráficas; máximo 2000 puntos por especie, después se reduce.
