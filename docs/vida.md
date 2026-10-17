# Subgrupo Vida

> **Fuente de verdad:** [Especificación](../docs/especificacion.md) (aprobada). Este documento no crea requisitos: reparte y aterriza los existentes. Todo lo que no está en la especificación aparece marcado como **(propuesta)** y se cierra en «Decisiones pendientes de este subgrupo».
> **Fecha:** 2026-10-17 · **Subgrupos hermanos:** [Ecosistema](ecosistema.md) · [App](app.md) 

## 1. Propósito y alcance

Vida construye **todo lo que está vivo**: las especies y las criaturas, sus genes y su estado vital, el autómata de nueve estados, la percepción, el movimiento y la ocupación de casillas, la depredación, la reproducción con mutación, la muerte, el cupo y el ciclo de vida de las especies (activa, extinguida, eliminada). También produce las **estadísticas por especie** que después se grafican.

| Dentro del alcance | Fuera del alcance (lo hace otro subgrupo) |
| --- | --- |
| Pasos 6 a 10 del tick y el cálculo de la muestra del paso 11 | Pasos 1 a 5: reloj, eventos, humedad, fuego, vegetación → **Ecosistema** |
| Genes, coste metabólico, mutación, reproducción, cupo | Orden del tick, generador aleatorio, huella del estado → **Ecosistema** |
| Autómata, percepción, movimiento, depredación, muerte | Formularios, lista y detalle de especies, gráficas, inspector → **App** |
| Especies: crear, agregar, eliminar, extinguir, límite de 12, color | Guardado en disco y esquema → **App** |
| Asignación de colores de la paleta | Dibujo de las criaturas y paleta como constante visual → **App** |

Fases que le tocan: **F2 Criaturas** (casi todo) y la parte de criaturas de **F3** (RF-36). Puertas: **G2** y **G3**.

## 2. Responsabilidades principales y límites

**Responsabilidades**

1. El **estado de la población** (identificador, especie, posición, genes, saciedad, hidratación, espera de reproducción, edad, estado del autómata, tick de nacimiento) y su orden estable por `id`.
2. El **autómata** con las seis prioridades de la [sección 5](../spec/especificacion.md#criaturas-autómata-de-estados-finitos) y los nueve estados.
3. **Movimiento y ocupación**: orden de acción por fuerza descendente y, en empate, por `id`; una criatura por casilla; el agua es intransitable.
4. **Depredación** (tamaño ≥ 1.2 veces, distinta especie, con hambre, +8 de saciedad por unidad de tamaño) y **muerte** por hambre, sed, fuego o ser comida.
5. **Reproducción y mutación**: promedio de los padres × (1 + u), con u uniforme en ±0.10, entre el piso y el límite técnico del gen; espera inicial de 200 ticks para las crías.
6. **Cupo** (1000 al inicio, configurable) y **límite de especies activas** (12, configurable).
7. **Gestión de especies**: crear, agregar y eliminar criaturas, extinguir, eliminar, reactivar, bloqueo del nombre.
8. **Color de la especie**: elegir el primer color libre de la paleta; liberarlo al extinguirse.
9. **Muestras de historial**: población y media, mínimo y máximo de cada estadística cada 10 ticks, con tope de 5000 por especie (D-33).

**Límites (lo que Vida no hace)**

- No modifica el mundo, salvo descontar 1 unidad de alimento de la casilla de la que come **(propuesta; ver Ecosistema, sección 5)**.
- No crea generadores aleatorios: recibe el generador único y sortea siempre en el mismo orden (por `id`).
- No decide cuándo guardar ni escribe en disco.
- No dibuja nada ni importa `PySide6`.
- No escribe números a mano: todo sale de `config/vida.py`.
- No inventa genes, estados ni reglas de dieta (fuera de alcance de la versión 1).

## 3. Requisitos funcionales asignados

R = responsable principal. Los criterios están resumidos: el texto completo, con Dado/Cuando/Entonces, está en la [sección 4](../spec/especificacion.md#4-requisitos-funcionales) de la especificación.

**3.1 Como responsable principal**

| ID | Requisito | Criterio de aceptación (resumen) | Fase | Depende de | Colabora |
| --- | --- | --- | --- | --- | --- |
| RF-36 | Efectos sobre criaturas | Ve fuego en su radio: huye; termina el tick en llamas: muere | F3 | RF-33, RF-39, RF-47 | Ecosistema |
| RF-37 | Crear especie | Nombre libre y cantidad: color de la paleta y criaturas en casillas distintas, hasta el cupo | F2 | RF-52, RF-55, RF-54 | App |
| RF-38 | Estadísticas de la criatura | Genes V, F, W, T; saciedad, hidratación y espera; edad solo informativa | F2 | RF-37 | App |
| RF-39 | Comportamiento | Solo transita entre los nueve estados y respeta las prioridades | F2 | RF-38, RF-53 | Ecosistema |
| RF-40 | Reproducción y mutación | Cría = promedio × (1+u), u en ±0.10, con piso y límite técnico; espera inicial 200 | F2 | RF-38, RF-41, RF-54 | — |
| RF-41 | Límite de criaturas | Con el cupo lleno no hay creaciones ni nacimientos y los padres no pagan | F2 | RF-40, RF-42 | App |
| RF-42 | Agregar criaturas | Se agregan min(N, cupo) e informa cuántas | F2 | RF-37, RF-41 | App |
| RF-43 | Eliminar criaturas | Se retiran N al azar con la semilla; sin criaturas pasa a extinguida | F2 | RF-37 | App |
| RF-44 | Extinguir especie | Retira sus criaturas; sigue en la lista como extinguida y se puede reactivar | F2 | RF-37, RF-43 | App |
| RF-45 | Eliminar especie | Desaparece, su nombre queda bloqueado y su historial se borra | F2 | RF-44 | App |
| RF-47 | Muerte | Saciedad 0, hidratación 0, llamas o ser comida: muere y libera el cupo ese tick | F2 | RF-38, RF-36 | Ecosistema |
| RF-52 | Límite de especies activas | Con 12 activas se rechaza crear o reactivar, con aviso | F2 | RF-37, RF-44 | App |
| RF-53 | Depredación | Come a otra especie de tamaño ≥ 1.2×, con hambre y adyacente; +8 saciedad por unidad | F2 | RF-38, RF-39 | — |
| RF-54 | Una criatura por casilla | Nunca dos en una casilla ni en el agua; manda la de más fuerza (empates por id) | F2 | RF-39 | — |
| RF-55 | Color de la especie | Cada especie activa un color distinto de la paleta de 12; al extinguirse queda libre | F2 | RF-52 | App |

**3.2 Como colaborador**

| ID | Requisito | Responsable | Qué aporta este subgrupo |
| --- | --- | --- | --- |
| RF-13 | Visualizar el mapa | App | Posición y especie de cada criatura en el snapshot; el color sale del índice de la paleta |
| RF-17 | Reloj y temperatura | App | Total de criaturas y cupo en el snapshot |
| RF-19 | Acciones en pausa | App | Aplicar `CrearEspecie`, `AgregarCriaturas`, `EliminarCriaturas`, `ExtinguirEspecie` y `EliminarEspecie` |
| RF-20 | Zoom, desplazamiento e inspector | App | Datos de la criatura (genes, estado vital, estado del autómata, edad) con `inspeccionar_criatura` (propuesta) |
| RF-46 | Datos de la especie | App | Calcular la muestra (población, media, mínimo y máximo) y reducir el historial al pasar de 5000 muestras |
| RF-49 | Estado completo | App | Serializar especies, criaturas e historial |

## 4. Requisitos no funcionales aplicables

Los criterios completos están en la [sección 6](../spec/especificacion.md#6-requisitos-no-funcionales).

| ID | Requisito | Rol del subgrupo | Reparto |
| --- | --- | --- | --- |
| RNF-01 | Plataforma: Python 3.12 en Windows, macOS y Ubuntu; instalación con un comando | Colaborador | A empaqueta y prueba en los tres sistemas; E y V no usan código ni rutas específicas de un sistema |
| RNF-02 | Rendimiento: ≥ 60 ticks/s sin criaturas y ≥ 30 con 1000 | Colaborador | E mide y optimiza el tick y el mapa; V mantiene el presupuesto de los pasos 6 a 10 con el cupo lleno |
| RNF-05 | Reproducibilidad: misma semilla y acciones, mismo estado a 5000 ticks | Colaborador | E es dueño del generador único, del orden del tick y de la prueba de oro; V sortea en orden estable; A guarda el estado del generador |
| RNF-06 | Configuración única validada al arrancar | Colaborador | A es dueño del cargador, la validación y la prueba de igualdad con el archivo; E y V son dueños de sus secciones |
| RNF-09 | Tamaño del guardado < 20 MB con 1000 criaturas y 5000 muestras por especie | Colaborador | A mide el archivo; V mantiene acotado el historial (D-33) |
| RNF-10 | Pruebas: cobertura ≥ 80 % del motor y pruebas de propiedades | Colaborador | E es dueño de la cobertura y de las propiedades del mundo (agua fija); V de las propiedades de criaturas (cupo, genes, casilla única, sin canibalismo); A integra todo en la CI |
| RNF-11 | Idioma (español) y accesibilidad (contraste 4.5:1; distancias de la paleta) | Colaborador | A revisa textos y contrastes; V garantiza que la asignación de colores respete la paleta (RF-55) |
| RNF-12 | Errores: registro local y mensaje sin perder el último guardado | Colaborador | A captura, registra y muestra; E y V levantan errores propios del contrato (`ErrorEcosim`) |

Además aplica a todos los RF del subgrupo: **RNF-05** (sorteos en orden estable, sin iterar sobre conjuntos) y **RNF-06** (cero valores escritos a mano).

## 5. Interfaces y contratos con otros subgrupos

| Contrato | Con quién | Qué entrega Vida | Qué recibe | Estado |
| --- | --- | --- | --- | --- |
| Comandos (`contracts/commands.py`) | App, Ecosistema | Atiende `CrearEspecie`, `AgregarCriaturas`, `EliminarCriaturas`, `ExtinguirEspecie`, `EliminarEspecie`; valida y deja efecto al inicio del tick siguiente | De App, a través de `Engine.apply` | Existe |
| `Snapshot` (`contracts/snapshot.py`) | App | `criaturas` (x, y, especie), `especies` (id, nombre, color, población, extinguida), `cupo` | — | Existe |
| Avisos del motor (`contracts/events.py`) | App | `CupoAlcanzado`, `EspecieExtinguida` | — | Existe |
| Ranura de los pasos 6 a 10 | Ecosistema | Funciones `paso_06` a `paso_10` y el cálculo de la muestra del paso 11 | El generador, la vista del mundo y la configuración | **Propuesta** |
| Vista del mundo (`engine/estado/mundo.py`) | Ecosistema | Escribe solo con `tomar_alimento(x, y)` | `terreno`, `alimento`, `llamas`; nunca recibe arreglos modificables | **Propuesta** |
| Serialización | Ecosistema, App | Bytes de especies, criaturas e historial | — | **Propuesta** |
| Inspección de criatura | App | `inspeccionar_criatura(id)`: genes, estado vital, estado del autómata, edad | — | **Propuesta** (RF-20) |
| Historial por especie | App | Muestras (tick, población, media, mínimo y máximo por estadística) | — | **Propuesta** (RF-46) |
| Paleta (`contracts/paleta.py`) | App | Índice de color asignado a cada especie | Los 12 colores y los colores de casillas como constantes | **Propuesta** |
| Configuración | Todos | Sección `config/vida.py` | Cargador y validación de App | Existe (hoy dentro de `schema.py`) |

**Acuerdos de uso**

- **Una criatura comida muere en el paso 7**, deja libre su casilla y deja de contar en el cupo en ese instante; las demás muertes se retiran en el paso 9.
- **Sorteos.** Vida documenta cuántos números sortea por criatura y en qué orden, y los registra en la tabla de sorteos que mantiene Ecosistema.
- **Comandos inválidos.** Un comando con valores inválidos levanta `ComandoInvalido` y no cambia nada; uno que el motor aún no implementa levanta `ComandoNoSoportado`.

## 6. Modelos de datos

**Posee**

| Modelo | Atributos (sección 2 de la especificación) | Notas |
| --- | --- | --- |
| Especie | id, nombre, estado (activa, extinguida, eliminada), genes base, color (mientras está activa) | El nombre de una especie eliminada queda bloqueado en esa simulación |
| Criatura | id, especie, posición, genes (V, F, W, T), saciedad, hidratación, espera de reproducción, edad (informativa), estado del autómata, tick de nacimiento | Orden estable por `id`; **faltan dos campos** que la especificación no lista (V-DP-01) |
| Muestra de historial | tick, especie, población, media, mínimo y máximo de cada estadística | Máximo de 5000 por especie; al excederse se reduce a la mitad la parte antigua |
| Tabla de genes | valor base, piso (20 %) y límite técnico de V, F, W y T | Todo en la configuración |

**Consume**

| Modelo | De quién | Para qué |
| --- | --- | --- |
| Terreno, alimento y casillas en llamas | Ecosistema | Percibir, comer, huir y morir |
| Generador aleatorio único | Ecosistema | Colocación inicial, elección de casilla de la cría, eliminación al azar |
| Configuración validada | App (cargador) | Parámetros de criaturas y especies |
| Comandos del usuario | App | Gestión de especies |
| Paleta | App | Índices de color válidos |

## 7. Tareas iniciales recomendadas (primer sprint, semanas 1 y 2)

Objetivo del sprint: dejar lista la base de **F2** para empezar a integrar en la semana 4, sin depender de que el mundo esté terminado. Casi todo son **funciones puras** que se prueban sin motor.

| # | Tarea | Requisito | Entregable | Depende de | Hecho cuando |
| --- | --- | --- | --- | --- | --- |
| V-1 | Estado de la población como arreglos NumPy por campo, ordenados por `id` | RF-38 | `estado/poblacion.py` | E-1 (reorganización de `engine/`) | Prueba de ida y vuelta de serialización |
| V-2 | Revisar `config/vida.py` contra la tabla de parámetros de la sección 5 | RNF-06 | Todos los valores de los grupos «Criaturas» y «Especies», con rango | — | La prueba de la configuración compara cada valor con la tabla |
| V-3 | Coste metabólico como función pura | RF-38 (A.8) | `vida/genes.py` | V-2 | Genes base: 0.12 de saciedad por tick; los cuatro genes ×3: 0.44 (unas 3.7 veces); ×4: 0.72, es decir, 0.018 unidades de alimento por tick (Q-03) |
| V-4 | Autómata como función de decisión pura, con una prueba por fila de la tabla de prioridades | RF-39 | `vida/automata.py` | V-2 | Incluye el caso: sed baja y comida visible, bebe primero si la hidratación es la menor |
| V-5 | Mutación pura y pruebas de propiedades | RF-40, RNF-10 | `vida/reproduccion.py` | V-2 | El gen siempre queda entre el piso y el límite técnico; el promedio de muchas crías coincide con el promedio de los padres |
| V-6 | Prueba de la paleta | RF-55, RNF-11 | `tests/vida/test_paleta.py` | — | Distancia CIE76 ≥ 35 contra las casillas y ≥ 45 entre los 12 colores (comprobado a mano: mínimos 36.3 y 46.3) |
| V-7 | Orden de acción y ocupación de casillas | RF-54 | `vida/movimiento.py` | V-1 | Dos criaturas que quieren la misma casilla: entra la más fuerte; empate por `id`; nadie entra al agua |
| V-8 | Benchmark sintético de percepción con 1000 criaturas, con visión base y con visión 25 | RNF-02 | `tests/bench/test_percepcion.py` | V-1 | Resultado anotado en `docs/ia/errores-comunes.md` o en el issue de V-DP-06 |
| V-9 | RFC conjunta: ranura de pasos 6 a 10, serialización, inspección de criatura, historial | RF-20, RF-46, RF-49 | RFC en `docs/rfc/` | E-9 | Los tres líderes la comentan |

## 8. Pruebas y criterios de salida

**Tipos de prueba**

- **Unitarias de funciones puras:** tabla de prioridades, coste, mutación, razón de tamaño, umbrales de 40 y 70.
- **Propiedades (RNF-10):** el cupo nunca se supera; los genes siempre están entre su piso y su límite técnico; nunca hay dos criaturas en la misma casilla ni en el agua; ninguna criatura come a otra de su especie.
- **Escenarios con semilla fija:** una presa que huye; un incendio cerca de una criatura; una cría sin casilla libre (no hay nacimiento y los padres no pagan).
- **Estadísticas con semilla fija:** mutación sin sesgo; reproducción de una especie de 50 criaturas durante 5000 ticks.
- **Paleta:** distancias de color (RF-55).
- **Rendimiento:** al menos 30 ticks por segundo con el cupo lleno (RNF-02, junto con Ecosistema).

**Criterios de salida**

| Puerta | Criterio (sección 7 de la especificación) | Quién valida |
| --- | --- | --- |
| F2 / G2 | Una especie de 50 criaturas se reproduce y sus genes cambian durante 5000 ticks; el cupo nunca se supera, nunca hay dos criaturas en una casilla y ningún gen sale de su piso ni de su límite técnico | Vida y Ecosistema |
| F3 / G3 (parte de Vida) | Las criaturas huyen del fuego y solo mueren por fuego en casillas en llamas | Vida, con Ecosistema |

**Calibración (semanas 7 a 9):** Vida ajusta solo la configuración. Se vigila que la población no crezca hasta el cupo de forma explosiva (Q-12) y que ninguna especie desaparezca por depredación en pocos cientos de ticks.

## 9. Riesgos, supuestos y puntos de coordinación

| Riesgo | Efecto | Qué hacer |
| --- | --- | --- |
| Costo de la percepción: el área revisada crece con el cuadrado del radio y la visión llega a 25 | Con 1000 criaturas el tick puede no alcanzar los 30 por segundo | Rejilla de ocupación y búsqueda vectorizada; medir en V-8 antes de optimizar |
| Estado de la criatura no guardado (dirección previa, acumulador de velocidad) | Cargar una simulación cambia el futuro; falla RF-49 | Resolver V-DP-01 antes de F2 |
| Iterar sobre colecciones sin orden | Rompe la reproducibilidad | Arreglos ordenados por `id`; prohibido iterar sobre `set` |
| Población explosiva o extinciones tempranas | La demostración de G2 no es creíble | Calibrar con configuración; no tocar el código |
| El autómata oscila entre estados | Criaturas que no avanzan | Persistencia hasta alcanzar 70 (ya en la especificación) y una prueba por transición |
| Velocidad mayor que 1 con varios pasos por tick | Conflictos de casilla más complejos | Mismas reglas por paso y una prueba de ocupación con velocidad 3 |
| Dependencia de Ecosistema para el fuego y de App para los formularios | Retrasos cruzados | Trabajar contra motores y datos falsos; pedidos entre equipos con la plantilla del plan |

**Supuestos:** el alimento es genérico y no hay dietas por especie (D-13); no hay muerte por vejez (D-28); las crías nacen adultas (D-26); los valores de la tabla de parámetros son iniciales.

**Puntos de coordinación**

| Con quién | Cuándo | Qué se acuerda |
| --- | --- | --- |
| Ecosistema | Semana 1 y al abrir cada RFC | Ranura de pasos, vista del mundo, sorteos |
| App | Semana 1 | Formularios de especie, avisos de cupo y de límite, datos del inspector y de las gráficas |
| Los tres líderes | Cada semana | Cambios de contrato y de especificación |

## 10. Enlaces a la especificación v0.4

| Tema | Enlace |
| --- | --- |
| Glosario y entidades | [Sección 2](../spec/especificacion.md#2-glosario-y-modelo-de-dominio) |
| Decisiones D-03, D-04, D-16, D-23 a D-33 | [Sección 3](../spec/especificacion.md#3-decisiones-y-resolución-de-puntos-abiertos) |
| Q-03 a Q-06, Q-10 a Q-13 | [Resolución de los puntos abiertos](../spec/especificacion.md#resolución-de-los-puntos-abiertos) |
| Requisitos funcionales | [Sección 4](../spec/especificacion.md#4-requisitos-funcionales) |
| Orden del tick | [Sección 5](../spec/especificacion.md#orden-del-tick) |
| Genes y estado vital | [Sección 5](../spec/especificacion.md#criaturas-genes-y-estado-vital) |
| Autómata de estados finitos | [Sección 5](../spec/especificacion.md#criaturas-autómata-de-estados-finitos) |
| Movimiento, depredación, reproducción y muerte | [Movimiento](../spec/especificacion.md#criaturas-movimiento-y-ocupación-de-casillas) · [Depredación](../spec/especificacion.md#criaturas-depredación) · [Reproducción](../spec/especificacion.md#criaturas-reproducción-mutación-y-muerte) |
| Tabla de parámetros | [Sección 5](../spec/especificacion.md#tabla-de-parámetros) |
| Requisitos no funcionales | [Sección 6](../spec/especificacion.md#6-requisitos-no-funcionales) |
| Fases | [Sección 7](../spec/especificacion.md#7-fuera-de-alcance-y-fases) |
| Paleta y sistema visual | [Sección 8](../spec/especificacion.md#sistema-visual) |
| Fórmulas y constantes (A.8, A.9, A.11) | [Anexo, sección 10](../spec/especificacion.md#10-anexo-fórmulas-y-constantes) |

## Trazabilidad RF → módulo → prueba

Los módulos siguen la estructura de la [propuesta de monorepo](monorepo-y-codeowners.md). Hoy **ninguno de los RF de Vida tiene prueba**: todo está por escribir, y cada prueba lleva `@pytest.mark.req("RF-xx")`.

| Requisito | Módulo (propuesto) | Prueba | Estado |
| --- | --- | --- | --- |
| RF-36 | `engine/vida/automata.py, engine/vida/muerte.py` | `tests/vida/test_huida_fuego.py` | Por escribir |
| RF-37 | `engine/vida/especies.py` | `tests/vida/test_crear_especie.py` | Por escribir |
| RF-38 | `engine/vida/genes.py, engine/estado/poblacion.py` | `tests/vida/test_genes_y_estado.py` | Por escribir |
| RF-39 | `engine/vida/automata.py` | `tests/vida/test_automata.py` | Por escribir |
| RF-40 | `engine/vida/reproduccion.py` | `tests/vida/test_reproduccion.py` | Por escribir |
| RF-41 | `engine/vida/reproduccion.py, engine/vida/especies.py` | `tests/vida/test_cupo.py` | Por escribir |
| RF-42 | `engine/vida/especies.py` | `tests/vida/test_agregar_criaturas.py` | Por escribir |
| RF-43 | `engine/vida/especies.py` | `tests/vida/test_eliminar_criaturas.py` | Por escribir |
| RF-44 | `engine/vida/especies.py` | `tests/vida/test_extinguir.py` | Por escribir |
| RF-45 | `engine/vida/especies.py` | `tests/vida/test_eliminar_especie.py` | Por escribir |
| RF-47 | `engine/vida/muerte.py` | `tests/vida/test_muerte.py` | Por escribir |
| RF-52 | `engine/vida/especies.py` | `tests/vida/test_limite_especies.py` | Por escribir |
| RF-53 | `engine/vida/depredacion.py` | `tests/vida/test_depredacion.py` | Por escribir |
| RF-54 | `engine/vida/movimiento.py` | `tests/vida/test_ocupacion.py` | Por escribir |
| RF-55 | `engine/vida/especies.py, contracts/paleta.py` | `tests/vida/test_paleta.py` | Por escribir |

## Decisiones pendientes de este subgrupo

Cada decisión trae una **propuesta por defecto** para no bloquear el trabajo. Mientras no se decida, se usa la propuesta y se anota en la PR.

| ID | Pregunta | Propuesta por defecto | Decide | Antes de |
| --- | --- | --- | --- | --- |
| V-DP-01 | La criatura necesita dos datos que la especificación no lista y que afectan al futuro: la dirección previa al explorar (persistencia 0.7) y el acumulador de la parte decimal de la velocidad | Agregarlos a la entidad Criatura y a RF-49 con una PR `spec-change` | Tres líderes | Semana 3 |
| V-DP-02 | La especificación fija la espera inicial de 200 ticks solo para las crías. ¿Qué espera tienen las criaturas de una especie nueva? | 0, por lectura literal; si la población explota, se pasa a 200 en la calibración | Líder de Vida | Semana 4 |
| V-DP-03 | Con varias parejas aptas a distancia 1, ¿quién se empareja con quién? No está definido | La primera criatura en el orden de acción elige a la apta de menor `id`; cada criatura se empareja una vez por tick | Líder de Vida, con revisión de Ecosistema | Semana 4 |
| V-DP-04 | ¿Quién calcula y quién guarda el historial? | Vida calcula, mantiene y reduce (D-33) dentro del estado del motor; App lo guarda y lo grafica | Líderes de Vida y App | Semana 2 |
| V-DP-05 | ¿Dónde vive la paleta de 12 colores? | `contracts/paleta.py` como constante; App la dibuja y Vida asigna el índice | Los tres líderes | Semana 2 |
| V-DP-06 | ¿Cómo se acelera la percepción con visión alta? | Rejilla de ocupación 100×100 más búsqueda por ventana vectorizada; decidir con la medición de V-8 | Líder de Vida | Semana 4 |
| V-DP-07 | El orden de acción actúa por fuerza descendente; ¿se calcula una vez por tick o se reordena cuando mueren criaturas en el mismo tick? | Una vez al inicio del paso 7; las muertas se saltan | Líder de Vida | Semana 4 |
