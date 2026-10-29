# CONTRATOS ENTRE SUBGRUPOS

# Proposito
definir qué funciones y atributos ofrece cada subgrupo a los demás, para trabajar en paralelo sin esperarnos. Este documento dice cómo se usa cada función, no cómo funciona por dentro.

---

# Plantilla

### Clase.funcion
- **Firma:** `funcion(parametro: tipo) -> tipo`
- **Descripción:** pocas lineas.
- **Parámetros:** significado de cada uno.
- **Retorno:** qué devuelve.
- **Errores:** qué pasa si se usa mal.

---

### Clase.atributo
- **Firma:** `nombre_atributo: tipo`
- **Descripción:** pocas lineas.

---

# Reglas de redacción
 - Nombres en español, sin tildes ni eñes.
 - Clases en `PascalCase`.
 - Funciones/métodos en `camelCase`.
 - Atributos/variables en `snake_case`.
 - Solo se documenta lo que cruza fronteras.
 - Escribir todas los métodos y atributos pertenecientes a una clase juntos (primero atributos y luego métodos).
 - Organizar alfabéticamente las clases a lo largo de cada sección de este documento.

 ---

# Grupo Ecosistema -> Grupo Vida
# Clase: `Casilla`

Representa una unidad espacial dentro del ecosistema simulado. Maneja su propio estado ecológico, humedad, cantidad de alimento y su transición temporal entre diferentes estados (ej. quemada, tierra, pasto, árbol).

## Atributos

| Atributo | Tipo | Descripción |
| :--- | :--- | :--- |
| `tipo` | `EstadoCasilla` | Estado actual del terreno en la casilla. |
| `coordenada` | `tuple` | Posición (x, y) de la casilla dentro de la matriz del ecosistema. |
| `humedad` | `float` | Nivel de humedad presente en la casilla. |
| `alimento` | `int` / `float` | Cantidad de alimento disponible en esta coordenada. |
| `tick_quemada` | `int` | Registro del instante de tiempo (`tick`) en el que la casilla fue quemada. |

## Métodos

### Getters
* **`getTipo() -> EstadoCasilla`**
  Obtiene el tipo actual de la casilla.
* **`getHumedad() -> float`**
  Retorna el valor de la humedad actual.

### Modificadores de Estado
* **`quemar() -> None`**
  Registra el `tick_actual` en `tick_quemada` y cambia el estado de la casilla a `quemada`.
* **`regenerar() -> None`**
  Si la casilla está quemada y ha pasado el tiempo necesario (`ticks_para_regenerar`), su estado vuelve a ser `tierra`.
* **`evolucionar() -> None`**
  Avanza el estado ecológico de la casilla: de `tierra` pasa a `pasto`, y de `pasto` pasa a `arbol`.
* **`involucionar() -> None`**
  Retrocede el estado ecológico de la casilla: de `arbol` pasa a `pasto`, y de `pasto` pasa a `tierra`.
# Grupo Ecosistema -> Grupo App

# Grupo Vida -> Grupo Ecosistema

# Grupo Vida -> Grupo App

# Grupo App -> Grupo Ecosistema

Estos contratos viven en `src/simulador/contratos/`. Los define App y los cumple el motor (Ecosistema y Vida). Las clases de datos son `dataclass(frozen=True)`: no se modifican después de crearlas. El motor no importa nada de `simulador.app`.

**Convenciones generales**
- La aplicación habla con el motor solo mediante `Motor`: manda comandos con `aplicar`, avanza con `avanzar` y lee el estado con `obtenerInstantanea`.
- Un comando se aplica al inicio del siguiente `avanzar`, nunca a mitad de un tick.
- Las excepciones heredan de `ErrorSimulador`.
- El estado guardado es un `bytes` opaco: solo el motor sabe interpretarlo.


**Formato de guardado** (RFC A-1)
- La biblioteca es un archivo SQLite (`biblioteca.db`) con una tabla `simulaciones`: `id`, `nombre`, `nombre_clave` (nombre en minúsculas, único), `tick`, `velocidad`, `fecha_guardado` y `estado`.
- El estado es **un único bloque de bytes** (D-35): el resultado de `Motor.aEstado()`. App lo guarda y lo devuelve sin leerlo ni modificarlo.
- Debe contener todo lo necesario para dejar la simulación idéntica (RF-49): mapa, clima, eventos activos, especies, criaturas, historial por especie y estado del generador aleatorio. La prueba es que `huellaEstado()` antes de guardar y después de cargar coincide.
- Debe ser **autodescrito**: lleva al principio su propia versión de formato, para que el motor pueda leer guardados antiguos o rechazar uno desconocido. `desdeEstado` lanza `ErrorSimulador` si no puede leerlo. **(Propuesta: Ecosistema define la cabecera.)**
- Hay **dos versiones independientes**: la del esquema de SQLite, que cuida App (hoy es la 1; un archivo de una versión más nueva se rechaza sin dañarlo), y la del formato del estado, que cuida el motor.
- La escritura es atómica (RF-50): un guardado se aplica entero o no se aplica, y un corte a mitad deja válida la versión anterior.
- El guardado ocupa menos de 20 MB con 1000 criaturas y 5000 muestras por especie (RNF-09).
- **Pregunta abierta, historial por especie:** D-35 lo pone en una tabla aparte (sería el esquema 2), pero eso exige que Vida lo entregue por un método del contrato que todavía no existe (RF-46, propuesta). **Propuesta mientras tanto:** el motor incluye el historial dentro del estado, y se migra a la tabla cuando exista el método.
---

### Almacenamiento
- **Firma:** `Almacenamiento(ABC)`
- **Descripción:** biblioteca de simulaciones guardadas en el equipo, sin cuentas ni propietarios. La aplicación la usa para guardar y cargar; el estado del motor viaja como `bytes` sin que el almacenamiento lo interprete. Implementaciones: `AlmacenamientoSqlite` (archivo) y `AlmacenamientoMemoria` (pruebas).
- **Métodos:**

#### Almacenamiento.cargar
- **Firma:** `cargar(simulacion_id: int) -> bytes`
- **Descripción:** devuelve el estado guardado, tal como se guardó.
- **Errores:** `SimulacionNoEncontrada` si no existe.

#### Almacenamiento.crear
- **Firma:** `crear(nombre: str, estado: bytes, tick: int, velocidad: int) -> ResumenSimulacion`
- **Descripción:** guarda una simulación nueva.
- **Parámetros:** `nombre` de 1 al largo máximo configurado (60 por defecto), sin espacios al inicio ni al final y único sin distinguir mayúsculas; `estado` son los bytes de `Motor.aEstado()`; `tick` y `velocidad` son los de la simulación.
- **Retorno:** el resumen de la simulación creada.
- **Errores:** `NombreInvalido` si el nombre no vale o ya existe.

#### Almacenamiento.eliminar
- **Firma:** `eliminar(simulacion_id: int) -> None`
- **Descripción:** borra la simulación. Es irreversible (D-36).
- **Errores:** `SimulacionNoEncontrada` si no existe.

#### Almacenamiento.guardar
- **Firma:** `guardar(simulacion_id: int, estado: bytes, tick: int, velocidad: int) -> ResumenSimulacion`
- **Descripción:** reemplaza el estado guardado. Si el guardado se interrumpe, la versión anterior sigue válida (RF-50).
- **Retorno:** el resumen actualizado.
- **Errores:** `SimulacionNoEncontrada` si no existe.

#### Almacenamiento.listar
- **Firma:** `listar() -> list[ResumenSimulacion]`
- **Descripción:** devuelve las simulaciones guardadas, sin su estado, en el orden en que se crearon.

#### Almacenamiento.renombrar
- **Firma:** `renombrar(simulacion_id: int, nombre: str) -> ResumenSimulacion`
- **Descripción:** cambia el nombre, con las mismas reglas que `crear`.
- **Errores:** `SimulacionNoEncontrada` si no existe; `NombreInvalido` si el nombre no vale o ya existe.

### AgregarCriaturas
- **Firma:** `AgregarCriaturas(especie_id: int, cantidad: int)`
- **Descripción:** comando para añadir criaturas a una especie existente.
- **Parámetros:** `especie_id` identifica la especie; `cantidad` es cuántas se añaden (mayor que 0).
- **Errores:** `ComandoInvalido` si la especie no existe o la cantidad no es válida.

### CancelarEvento
- **Firma:** `CancelarEvento(tipo: TipoEvento)`
- **Descripción:** comando para terminar antes de tiempo un evento natural activo.
- **Parámetros:** `tipo` es el evento a cancelar.
- **Errores:** `ComandoInvalido` si ese evento no está activo.

### ComandoInvalido
- **Firma:** `ComandoInvalido(ErrorSimulador)`
- **Descripción:** el comando es de un tipo conocido, pero no se puede aplicar con el estado o los valores actuales (por ejemplo nutrientes fuera de rango o un evento ya activo).

### ComandoNoSoportado
- **Firma:** `ComandoNoSoportado(ErrorSimulador)`
- **Descripción:** el motor no implementa ese tipo de comando. `MotorFalso` lo lanza con los comandos de especies y criaturas.

### CrearEspecie
- **Firma:** `CrearEspecie(nombre: str, cantidad: int, genes: tuple[float, float, float, float] | None = None)`
- **Descripción:** comando para crear una especie nueva con una población inicial.
- **Parámetros:** `nombre` de la especie; `cantidad` de criaturas iniciales; `genes` opcional con los cuatro genes iniciales (si es `None`, el motor elige).
- **Errores:** `ComandoInvalido` si los valores no son válidos o se supera el cupo.

### CupoAlcanzado
- **Firma:** `CupoAlcanzado(tick: int, cupo: int)`
- **Descripción:** aviso de que el total de criaturas llegó al cupo máximo.
- **Parámetros:** `tick` en que ocurrió; `cupo` es el máximo vigente.

### EliminarCriaturas
- **Firma:** `EliminarCriaturas(especie_id: int, cantidad: int)`
- **Descripción:** comando para quitar criaturas de una especie.
- **Parámetros:** `especie_id` identifica la especie; `cantidad` es cuántas se quitan.
- **Errores:** `ComandoInvalido` si la especie no existe o la cantidad no es válida.

### EliminarEspecie
- **Firma:** `EliminarEspecie(especie_id: int)`
- **Descripción:** comando para borrar una especie y todas sus criaturas.
- **Parámetros:** `especie_id` identifica la especie.
- **Errores:** `ComandoInvalido` si la especie no existe.

### ErrorSimulador
- **Firma:** `ErrorSimulador(Exception)`
- **Descripción:** clase base de todos los errores del simulador. Permite capturarlos juntos.

### EspecieExtinguida
- **Firma:** `EspecieExtinguida(especie_id: int, nombre: str, tick: int)`
- **Descripción:** aviso de que una especie se quedó sin criaturas.
- **Parámetros:** `especie_id` y `nombre` de la especie; `tick` en que ocurrió.

### Estacion
- **Firma:** `Estacion(Enum)`
- **Descripción:** estación del año. Valores: `primavera`, `verano`, `otono`, `invierno`.

### EstadoCasilla
- **Firma:** `EstadoCasilla(IntEnum)`
- **Descripción:** código de cada casilla en `Instantanea.terreno`. Valores: `tierra`=0, `agua`=1, `pasto`=2, `arbol`=3, `llamas`=4, `quemada`=5. (Propuesta: Ecosistema debe confirmarla.)

### EventoNaturalIniciado
- **Firma:** `EventoNaturalIniciado(tipo: TipoEvento, origen: OrigenEvento, tick: int)`
- **Descripción:** aviso de que empezó un evento natural.
- **Parámetros:** `tipo` del evento; `origen` natural o manual; `tick` en que empezó.

### EventoNaturalTerminado
- **Firma:** `EventoNaturalTerminado(tipo: TipoEvento, tick: int, cancelado: bool = False)`
- **Descripción:** aviso de que terminó un evento natural.
- **Parámetros:** `tipo` del evento; `tick` en que terminó; `cancelado` es `True` si se terminó con `CancelarEvento`.

### ExtinguirEspecie
- **Firma:** `ExtinguirEspecie(especie_id: int)`
- **Descripción:** comando para dejar una especie sin criaturas, conservándola en la lista (queda marcada como extinguida).
- **Parámetros:** `especie_id` identifica la especie.
- **Errores:** `ComandoInvalido` si la especie no existe.

### FijarNutrientes
- **Firma:** `FijarNutrientes(nivel: int)`
- **Descripción:** comando para fijar el nivel de nutrientes del terreno.
- **Parámetros:** `nivel` entre 0 y 100.
- **Errores:** `ComandoInvalido` si `nivel` está fuera de rango.

### InfoEspecie
- **Firma:** `InfoEspecie(especie_id: int, nombre: str, color: str, poblacion: int, extinguida: bool)`
- **Descripción:** resumen de una especie dentro de la instantánea.
- **Parámetros:** `color` es el color con que la app dibuja la especie; `poblacion` es el número actual de criaturas; `extinguida` indica si ya no tiene criaturas.

### InfoEvento
- **Firma:** `InfoEvento(tipo: TipoEvento, ticks_restantes: int | None = None, casillas_en_llamas: int | None = None)`
- **Descripción:** evento natural activo dentro de la instantánea.
- **Parámetros:** `ticks_restantes` hasta que termine (`None` si no aplica); `casillas_en_llamas` solo para incendios (`None` si no aplica).

### Instantanea
- **Firma:** `Instantanea(tick, estacion, temperatura, nutrientes, terreno, criaturas, especies, eventos, cupo)`
- **Descripción:** foto inmutable del mundo en un tick. Es lo único que la app lee para dibujar. Los arreglos `terreno` y `criaturas` son de solo lectura.
- **Atributos:**
  - `tick: int` número de tick.
  - `estacion: Estacion` estación actual.
  - `temperatura: float` temperatura actual.
  - `nutrientes: int` nivel de nutrientes (0–100).
  - `terreno: numpy.ndarray` matriz de códigos `EstadoCasilla`.
  - `criaturas: numpy.ndarray` datos de las criaturas vivas.
  - `especies: tuple[InfoEspecie, ...]` resumen por especie.
  - `eventos: tuple[InfoEvento, ...]` eventos activos.
  - `cupo: int` máximo de criaturas permitido.
- **Propiedad:** `total_criaturas: int` número total de criaturas vivas.
- **Errores:** intentar escribir en `terreno` o `criaturas` lanza `ValueError` (numpy).

### Motor
- **Firma:** `Motor(ABC)`
- **Descripción:** interfaz que debe cumplir el motor de simulación. La app solo conoce esta clase, no la implementación.
- **Métodos:**

#### Motor.aEstado
- **Firma:** `aEstado() -> bytes`
- **Descripción:** serializa el estado completo para guardarlo.
- **Retorno:** bytes opacos; con `desdeEstado` deben reconstruir el mismo mundo.

#### Motor.aplicar
- **Firma:** `aplicar(comando: Comando) -> None`
- **Descripción:** entrega un comando al motor. Surte efecto al inicio del siguiente `avanzar`.
- **Parámetros:** `comando` es cualquiera de los comandos de esta sección.
- **Errores:** `ComandoInvalido` si no se puede aplicar; `ComandoNoSoportado` si el motor no lo implementa.

#### Motor.avanzar
- **Firma:** `avanzar() -> list[Aviso]`
- **Descripción:** avanza la simulación un tick.
- **Retorno:** avisos generados en ese tick (`CupoAlcanzado`, `EspecieExtinguida`, `EventoNaturalIniciado`, `EventoNaturalTerminado`), posiblemente vacía.

#### Motor.desdeEstado
- **Firma:** `desdeEstado(estado: bytes) -> Motor` (método de clase)
- **Descripción:** reconstruye un motor a partir de bytes producidos por `aEstado`.
- **Errores:** `ErrorSimulador` si los bytes no son válidos.

#### Motor.huellaEstado
- **Firma:** `huellaEstado() -> str`
- **Descripción:** huella (hash) del estado. Dos motores con la misma semilla y los mismos comandos deben dar la misma huella; se usa para probar determinismo.

#### Motor.obtenerInstantanea
- **Firma:** `obtenerInstantanea() -> Instantanea`
- **Descripción:** devuelve la foto actual del mundo sin modificarlo.

### MotorFalso
- **Firma:** `MotorFalso(tamano: int = 100, retardo: float = 0.0)`
- **Descripción:** motor de pruebas de App (`simulador.contratos.motor_falso`). Cumple `Motor` sin ecosistema ni criaturas, para probar la interfaz sin esperar al motor real. Soporta `FijarNutrientes`, `ProvocarEvento` y `CancelarEvento`; el resto de comandos lanzan `ComandoNoSoportado`.
- **Parámetros:** `tamano` lado del terreno; `retardo` segundos que tarda cada `avanzar` (para simular un motor lento).

### OrigenEvento
- **Firma:** `OrigenEvento(Enum)`
- **Descripción:** quién inició un evento. Valores: `natural`, `manual`.

### ProvocarEvento
- **Firma:** `ProvocarEvento(tipo: TipoEvento, foco_x: int | None = None, foco_y: int | None = None, radio: int = 0)`
- **Descripción:** comando para iniciar un evento natural a petición del usuario.
- **Parámetros:** `tipo` del evento; `foco_x`, `foco_y` casilla de origen (solo eventos localizados, como el incendio); `radio` alcance inicial.
- **Errores:** `ComandoInvalido` si ese evento ya está activo.

### ResumenSimulacion
- **Firma:** `ResumenSimulacion(simulacion_id: int, nombre: str, tick: int, fecha_guardado: datetime, velocidad: int)`
- **Descripción:** datos de una simulación guardada, sin su estado. Es inmutable.
- **Atributos:**
  - `simulacion_id: int` identificador; no se reutiliza al borrar.
  - `nombre: str` nombre único en la biblioteca.
  - `tick: int` tick del último guardado.
  - `fecha_guardado: datetime` fecha y hora del último guardado.
  - `velocidad: int` velocidad de simulación (ticks por segundo) del último guardado.

### TipoEvento
- **Firma:** `TipoEvento(Enum)`
- **Descripción:** tipos de evento natural. Valores: `sequia`, `lluvia`, `incendio`.

---

# Grupo App -> Grupo Vida

Vida usa los mismos contratos descritos en **Grupo App -> Grupo Ecosistema**; no hay contratos adicionales. En particular, `CrearEspecie`, `AgregarCriaturas`, `EliminarCriaturas`, `ExtinguirEspecie`, `EliminarEspecie`, `InfoEspecie` y `EspecieExtinguida` son los que tocan a Vida.
