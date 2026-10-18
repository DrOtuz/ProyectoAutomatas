# Guía de pruebas y trazabilidad

> Explica en simple todo lo que los documentos de los subgrupos y la especificación dicen sobre pruebas y trazabilidad. No crea reglas nuevas: todo sale de `especificacion.md`, `app.md`, `ecosistema.md` y `vida.md`. Lo que es ejemplo ilustrativo está marcado como tal.
> **Fecha:** 2026-10-18

## 1. La idea en una frase

**Trazabilidad** es poder responder, para cualquier requisito, tres preguntas: *¿en qué código se cumple?* y *¿qué prueba demuestra que se cumple?* y *¿en qué estado está esa prueba?* Así ningún requisito queda sin código ni sin prueba, y ninguna prueba queda huérfana.

La cadena completa es:

```
Requisito (RF/RNF)  →  Módulo (archivo de código)  →  Prueba (archivo de test)  →  Estado
```

## 2. Qué es cada pieza

| Pieza | Qué es | Dónde se define |
| --- | --- | --- |
| **RF-xx** | Requisito funcional: lo que el programa debe hacer (p. ej. RF-25 «el agua nunca cambia») | Sección 4 de la especificación |
| **RNF-xx** | Requisito no funcional: cómo debe comportarse (rendimiento, reproducibilidad, guardado seguro…) | Sección 6 de la especificación |
| **Criterio de aceptación** | Frase «Dado… Cuando… Entonces…» que dice cómo comprobar el requisito | Dentro de cada RF |
| **Módulo** | Archivo de código que implementa el requisito (p. ej. `ecosistema/vegetacion.py`) | Tabla de trazabilidad de cada subgrupo |
| **Prueba** | Archivo de test que comprueba el requisito (p. ej. `tests/ecosistema/test_alimento.py`) | Misma tabla |
| **Marca `@pytest.mark.requisito("RF-xx")`** | Etiqueta que se pone sobre cada test para decir qué requisito comprueba | Sobre cada función de test |
| **Estado** | `Existe`, `Por escribir` o `Parcial` | Misma tabla |

### Cómo leer el Estado

- **Por escribir:** todavía no hay ninguna prueba para ese requisito.
- **Existe:** hay al menos una prueba con la marca `@pytest.mark.requisito`. **No significa que cubra todo el criterio** (por ejemplo, una prueba de sequía que solo revise la temperatura). Hoy no hay ninguna.
- **Parcial:** hay una parte de las pruebas y falta otra (p. ej. RNF-02 cuando exista el benchmark sin criaturas pero falte el de 1000).

Nota: versiones anteriores de las tablas marcaban varios requisitos como «Existe» por un kit de pruebas que no está en este repositorio. Hoy el repositorio no tiene código ni pruebas, así que todas las filas están «Por escribir».

## 3. Las dos tablas de trazabilidad

1. **En la especificación (sección 9):** vista general por área (simulaciones, ventana, mapa, eventos, criaturas, persistencia, no funcionales). Dice qué tipo de prueba aplica a cada área.
2. **En cada subgrupo (`app.md`, `ecosistema.md`, `vida.md`):** una fila por requisito con módulo, archivo de prueba y estado. Es la que se usa a diario.

Reglas acordadas (decisión A-DP-07): la matriz se **regenera en la integración continua (CI)** y **cada subgrupo responde por sus propias filas**. Hoy ningún requisito de ningún subgrupo tiene prueba: la carpeta de pruebas está vacía y todo está «Por escribir».

## 4. Tipos de prueba que se mencionan

| Tipo | Qué comprueba | Ejemplo en los documentos |
| --- | --- | --- |
| **Unitaria de función pura** | Una función aislada con entradas y salidas conocidas, sin necesidad del motor completo | Humedad con d = 1 en primavera ≈ 0.91; coste metabólico con genes base = 0.12 por tick; una prueba por fila de la tabla de prioridades del autómata |
| **Estadística con semilla fija** | Un comportamiento aleatorio, repetible porque la semilla es siempre la misma | Más pasto cerca del agua que lejos tras 10 000 ticks; más sequías en verano que en invierno; la mutación no tiene sesgo |
| **Escenario con semilla fija** | Una situación armada a propósito | Foco de incendio, barrera de agua, lluvia que apaga, presa que huye, cría sin casilla libre |
| **Propiedad (Hypothesis)** | Algo que debe ser cierto *siempre*, probado con muchas entradas generadas al azar | El agua nunca cambia; el cupo nunca se supera; los genes quedan entre su piso y su límite técnico; nunca hay dos criaturas en una casilla; nadie come a su misma especie |
| **Determinismo y «prueba de oro»** | Misma semilla y mismas acciones dan exactamente el mismo estado | Ver sección 5 |
| **Contrato de `Almacenamiento`** | La misma batería de pruebas corre contra `AlmacenamientoSqlite` e `AlmacenamientoMemoria` | Garantiza que el guardado real y el falso se comportan igual |
| **Integridad** | Un corte a mitad de un guardado deja válida la versión anterior | RF-50 |
| **Migración** | Abrir un archivo de una versión anterior del esquema migra o da un error claro | RNF-08 |
| **Interfaz con `pytest-qt`** | Pantallas y botones, sin mostrar ventana (modo `offscreen`) | Flujo crear → editar → cargar |
| **Rendimiento (benchmark)** | Velocidad medida | ≥ 60 ticks/s sin criaturas, ≥ 30 con 1000 (RNF-02); ≥ 30 FPS en la ventana (RNF-03) |
| **Tamaño del guardado** | Peso del archivo | Menos de 20 MB con 1000 criaturas y 5000 muestras por especie (RNF-09) |
| **Accesibilidad y paleta** | Contraste y distancias de color | Contraste 4.5:1; distancia CIE76 ≥ 35 contra casillas y ≥ 45 entre los 12 colores |
| **Cobertura** | Qué porcentaje del código del motor ejecutan las pruebas | ≥ 80 % (RNF-10) |
| **Reglas de código** | Que nadie rompa las reglas de arquitectura | El motor no importa PySide6 (RNF-04); no hay valores escritos a mano (RNF-06) |

### Palabras que se repiten

- **Semilla:** número inicial del generador aleatorio. Misma semilla + mismas acciones = mismo resultado (RNF-05). Por eso las pruebas con azar son repetibles.
- **Generador único:** todo el azar del motor sale de un solo generador y siempre en el mismo orden. Un sorteo dentro de un `if` o iterar sobre un `set` rompe la reproducibilidad.
- **Doble buffer:** cada casilla se calcula con el estado del tick anterior, no con el que se está escribiendo. Hace el resultado independiente del orden.
- **`MotorFalso` e `AlmacenamientoMemoria`:** motor y almacenamiento falsos para construir y probar pantallas sin esperar al motor real.
- **`xfail`:** marca de «se sabe que falla por ahora». Se quita cuando la funcionalidad se implementa.

## 5. Determinismo y «prueba de oro»

- **Huella del estado (`huellaEstado`):** un resumen numérico del estado completo del motor. Si dos corridas dan la misma huella, son idénticas.
- **Prueba de oro:** se corre el motor 5000 ticks con semilla fija y se guarda la huella esperada. Si algún cambio de código altera la huella, la prueba falla.
- **Por qué importa:** detecta cambios de comportamiento no intencionales. Pero cualquier cambio de regla *intencional* también la cambia.
- **Quién la custodia y cómo se regenera (E-DP-03):** Ecosistema la custodia. Regenerarla exige una PR con la etiqueta `cambio-de-oro`, una explicación y **dos aprobaciones** (una de Ecosistema y una de otro subgrupo). Si se regenera sin revisión, deja de servir.

## 6. Fases y puertas (G1 a G4)

Cada fase termina con una **puerta**: una prueba que debe pasar antes de empezar la siguiente.

| Puerta | Qué debe demostrar | Quién valida |
| --- | --- | --- |
| **G1** (F1 Mundo vivo) | Sin criaturas, 10 000 ticks con semilla fija producen pasto y árboles cerca del agua, y se guarda y carga idéntico (`tests/gates/test_g1.py`) | Ecosistema y App |
| **G2** (F2 Criaturas) | Una especie de 50 criaturas se reproduce y sus genes cambian durante 5000 ticks; el cupo nunca se supera, nunca hay dos en una casilla y ningún gen sale de su piso ni de su límite técnico | Vida y Ecosistema |
| **G3** (F3 Eventos) | Un incendio manual se propaga, el agua lo frena y la lluvia lo apaga; cancelarlo apaga sus casillas; las criaturas huyen y solo mueren en casillas en llamas | Ecosistema, Vida y App |
| **G4** (F4 Análisis) | Las gráficas de 20 000 ticks abren sin congelar la ventana; el inspector muestra una casilla y una criatura con su edad | App, con Vida y Ecosistema |

## 7. Cómo asignan los documentos las pruebas por equipo

| Equipo | Es dueño de | Tipos de prueba principales |
| --- | --- | --- |
| **Ecosistema** | Pasos 1 a 5 y 11 del tick, la prueba de oro, la cobertura del motor, propiedades del mundo | Funciones puras, estadísticas y escenarios con semilla, propiedades (agua fija), oro, rendimiento sin criaturas |
| **Vida** | Pasos 6 a 10, propiedades de criaturas, paleta | Funciones puras (autómata, coste, mutación), propiedades (cupo, genes, casilla única, sin canibalismo), escenarios, benchmark de percepción (V-8) |
| **App** | Interfaz, guardado, CI, empaquetado | Contrato de `Almacenamiento`, integridad, migración, `pytest-qt`, tamaño del guardado, accesibilidad, CI en los tres sistemas |

La CI todavía no existe: App la creará (`.github/workflows/integracion_continua.yml` y la corrida nocturna `nocturna.yml`, tarea A-8) para correr las pruebas en Windows, macOS y Ubuntu (RNF-01). Mientras tanto, cada PR debe pasar `ruff check` y `pytest` antes de pedir revisión.

## 8. Cómo agregar una prueba, paso a paso

1. **Elige el requisito** en la tabla de tu subgrupo cuyo estado sea «Por escribir» (o «Parcial»).
2. **Lee su criterio** «Dado / Cuando / Entonces» en la especificación: eso es lo que la prueba debe comprobar.
3. **Crea el archivo** en la ruta que indica la columna «Prueba» (p. ej. `tests/ecosistema/test_alimento.py`).
4. **Escribe la prueba** con la marca del requisito (la marca `requisito` debe registrarse en `pyproject.toml`; tarea A-11). Ejemplo ilustrativo (no es código del repositorio):

   ```python
   import pytest

   @pytest.mark.requisito("RF-25")
   def test_el_agua_nunca_cambia():
       # Dado un mapa con agua
       # Cuando corren N ticks con semilla fija
       # Entonces toda casilla de agua sigue siendo agua
       ...
   ```

5. **Si hay azar**, usa semilla fija. **Si algo debe cumplirse siempre**, hazla de propiedades.
6. **Corre `ruff check` y `pytest`** (y la CI, cuando exista).
7. **Actualiza la fila** de tu subgrupo: «Por escribir» pasa a «Existe» (o «Parcial» si solo cubre una parte del criterio).
8. **Si tu cambio altera la huella de oro**, abre una PR aparte con la etiqueta `cambio-de-oro` (sección 5).

## 9. Lista de comprobación antes de cerrar un requisito

- [ ] El criterio «Dado / Cuando / Entonces» completo está cubierto, no solo una parte.
- [ ] La prueba lleva `@pytest.mark.requisito("RF-xx")`.
- [ ] Usa semilla fija si hay azar.
- [ ] Ningún número está escrito a mano: sale de la configuración (RNF-06).
- [ ] La fila de trazabilidad está actualizada.
- [ ] El motor sigue sin importar PySide6 (RNF-04).

## 10. Mapa rápido de requisitos no funcionales y dónde se prueban

| RNF | Qué exige | Cómo se prueba | Dueño |
| --- | --- | --- | --- |
| RNF-01 | Funciona en Windows, macOS y Ubuntu con un comando | CI en tres sistemas (`tests/app/test_instalacion.py`) | App |
| RNF-02 | ≥ 60 ticks/s sin criaturas; ≥ 30 con 1000 | `tests/bench/` | Ecosistema (con Vida) |
| RNF-03 | ≥ 30 FPS, la ventana no se congela | `tests/app/test_ejecutor.py` | App |
| RNF-04 | El motor no importa PySide6 | `tests/app/test_reglas_de_codigo.py` (import-linter) | Ecosistema |
| RNF-05 | Misma semilla, mismo estado a 5000 ticks | `test_determinismo.py`, `test_oro.py` | Ecosistema |
| RNF-06 | Parámetros solo en la configuración validada | `tests/app/test_configuracion.py` | App |
| RNF-08 | Guardado atómico y versión de esquema | `tests/app/test_sqlite.py` | App |
| RNF-09 | Guardado < 20 MB | `tests/app/test_tamano_guardado.py` | App (Vida acota el historial) |
| RNF-10 | Cobertura ≥ 80 % y propiedades | `tests/ecosistema/`, `tests/vida/` | Ecosistema y Vida |
| RNF-11 | Español y contraste 4.5:1; distancias de la paleta | `tests/app/test_contraste_y_paleta.py`, `tests/vida/test_paleta.py` | App (Vida asigna colores) |
| RNF-12 | Error registrado sin perder el último guardado | `tests/app/test_ejecutor.py` | App |
