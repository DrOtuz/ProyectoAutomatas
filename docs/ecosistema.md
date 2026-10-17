# Subgrupo Ecosistema

> **Fuente de verdad:** [Especificación](../docs/especificacion.md) (aprobada). Este documento no crea requisitos: reparte y aterriza los existentes. Todo lo que no está en la especificación aparece marcado como **(propuesta)** y se cierra en «Decisiones pendientes de este subgrupo».
> **Fecha:** 2026-10-17 · **Subgrupos hermanos:** [Vida](vida.md) · [App](app.md) 

## 1. Propósito y alcance

Ecosistema construye **el mundo y el reloj que lo mueve**: el ciclo de simulación de once pasos, el mapa como autómata celular (humedad, vegetación, alimento, regeneración), el clima (estaciones y temperatura), los eventos naturales (sequía, lluvia, incendio) y el fuego. Es también el dueño del **núcleo determinista del motor**: el generador aleatorio único, el doble buffer, el orden del tick, la huella del estado y la prueba de oro.

| Dentro del alcance | Fuera del alcance (lo hace otro subgrupo) |
| --- | --- |
| Pasos 1 a 5 y 11 del tick ([sección 5](../spec/especificacion.md#orden-del-tick)) | Pasos 6 a 10: percepción, acción, metabolismo, muertes, nacimientos → **Vida** |
| Casilla: estado, contador, vegetación previa, alimento | Criaturas, especies, genes, cupo → **Vida** |
| Humedad, temperatura, estaciones, nutrientes globales | Guardado en disco, biblioteca, esquema SQLite → **App** |
| Eventos naturales, cancelación, fuego | Pantallas, botones y dibujo del mapa → **App** |
| `Simulation`, snapshot, `to_state`, `state_hash`, oro | Hilo de ejecución (`Runner`) y autoguardado → **App** |

Fases que le tocan: **F1 Mundo vivo** (estaciones, vegetación, alimento) y **F3 Eventos** (eventos, fuego, regeneración). Puertas: **G1** y **G3**.

## 2. Responsabilidades principales y límites

**Responsabilidades**

1. Que el motor sea **reproducible**: un solo generador (`Simulation._rng`), sorteos en orden estable, doble buffer, nada de `set` en bucles (RNF-05).
2. Que el orden de los once pasos sea el de la especificación y que cada subgrupo se enchufe en su paso.
3. Las reglas del mapa: humedad (A.2), escalera tierra ↔ pasto ↔ árbol (D-42, A.3, A.4), alimento (A.5), regeneración.
4. Clima y eventos: calendario por estación (D-20, Q-09), sequía, lluvia, cancelación (Q-08).
5. Fuego: ignición, propagación, extinción y efectos sobre la vegetación (A.6).
6. El **estado del mundo** y su serialización autodescrita (sin `pickle`), y la prueba de oro a 5000 ticks.
7. El rendimiento del tick (RNF-02) y la separación motor/interfaz (RNF-04).

**Límites (lo que Ecosistema no hace)**

- No decide el comportamiento de las criaturas ni modifica la población. Los efectos del fuego sobre las criaturas (RF-36, RF-47) los resuelve **Vida** leyendo el mundo.
- No escribe en disco ni importa `PySide6`, `runtime`, `storage` ni `ui` (regla de importación).
- No escribe números a mano: todo parámetro sale de `config/ecosistema.py` (RNF-06).
- No cambia un contrato sin RFC aprobada por los tres líderes.
- **Única excepción de escritura ajena:** en el paso 7, Vida descuenta 1 unidad de `alimento` de la casilla que come. Ecosistema no lo hace ni lo impide **(propuesta; ver sección 5)**.

## 3. Requisitos funcionales asignados

R = responsable principal. Los criterios están resumidos: el texto completo, con Dado/Cuando/Entonces, está en la [sección 4](../spec/especificacion.md#4-requisitos-funcionales) de la especificación.

**3.1 Como responsable principal**

| ID | Requisito | Criterio de aceptación (resumen) | Fase | Depende de | Colabora |
| --- | --- | --- | --- | --- | --- |
| RF-21 | Estaciones | Cada L ticks cambia la estación en orden y la temperatura base la sigue | F1 | D-11, Q-09 | — |
| RF-22 | Tierra a pasto | Con humedad ≥ 0.25, probabilidad que crece con el exceso; más pasto cerca del agua | F1 | RF-21, RF-16, D-10, D-42 | — |
| RF-23 | Pasto a árbol | Con humedad ≥ 0.5 y nutrientes ≥ 40, probabilidad por exceso; si no, no pasa | F1 | RF-22, RF-16 | — |
| RF-24 | Alimento de la vegetación | p = P·(0.7 + 0.3·h); hasta 3 (árbol) y 1 (pasto) unidades | F1 | RF-22, A.5 | — |
| RF-25 | Agua fija | Una casilla de agua conserva su estado toda la simulación | F1 | — | — |
| RF-26 | Regeneración | Quemada vuelve a tierra a los 150 ticks y puede crecer pasto | F3 | RF-35, RF-22 | — |
| RF-56 | Retroceso de la vegetación | Árbol baja a pasto y pasto a tierra con humedad bajo el umbral; un nivel por tick | F1 | RF-22, RF-23, D-42 | — |
| RF-27 | Aparición natural | Cada tick se sortea cada evento con λ/L; más sequías en verano, más lluvias en otoño | F3 | RF-21, D-20 | — |
| RF-28 | Provocar un evento | El botón lo activa con su duración; el incendio pide foco en el mapa | F3 | RF-27, D-21 | App |
| RF-29 | Sequía | Humedad −0.35, crecimiento ×0.3, temperatura +3 °C | F3 | RF-28, RF-22 | — |
| RF-30 | Lluvia | Humedad +0.35, crecimiento ×1.5, apaga casillas en llamas con p = 0.30 | F3 | RF-28, RF-33 | — |
| RF-31 | Exclusión y repetición | Sequía y lluvia se excluyen; el incendio convive; mismo tipo se rechaza | F3 | RF-28 | App |
| RF-51 | Cancelar un evento | Termina al inicio del tick siguiente; el incendio deja sus llamas como quemada | F3 | RF-28 | App |
| RF-32 | Inicio del incendio | Natural en casilla inflamable al azar; manual con radio 0 a 3; sin inflamables, aviso | F3 | RF-27, RF-28 | App |
| RF-33 | Propagación | Probabilidad por vecina en llamas según vegetación, humedad, temperatura y estación | F3 | RF-32, RF-30 | — |
| RF-34 | Extinción | A los 3 ticks (pasto) u 8 (árbol) pasa a quemada; el evento acaba sin llamas | F3 | RF-33 | — |
| RF-35 | Efectos sobre la vegetación | La casilla pierde alimento y vegetación al incendiarse | F3 | RF-33, RF-24 | — |

**3.2 Como colaborador**

| ID | Requisito | Responsable | Qué aporta este subgrupo |
| --- | --- | --- | --- |
| RF-07 | Crear simulación | App | Constructor del motor: mapa de tierra 100×100, nutrientes 50, tick 0, primavera |
| RF-09 | Confirmar el editor | App | Crear el motor con el terreno confirmado y la semilla; arranca en tick 0 y en pausa |
| RF-10 | Cargar simulación | App | Reconstruir el motor desde el estado guardado (`from_state`), con el mismo estado del generador |
| RF-16 | Nutrientes del suelo | App | Guardar el nivel en el estado y usarlo desde el tick siguiente (`FijarNutrientes`) |
| RF-17 | Reloj y temperatura | App | Temperatura, tick y estación en el snapshot |
| RF-18 | Etiqueta de eventos | App | Lista de eventos activos con ticks restantes (casillas en llamas en el incendio) |
| RF-19 | Acciones en pausa | App | Aplicar `FijarNutrientes`, `ProvocarEvento` y `CancelarEvento` al inicio del tick siguiente |
| RF-20 | Zoom, desplazamiento e inspector | App | Datos de la casilla (estado, humedad, alimento, contador) con `inspeccionar_casilla` (propuesta) |
| RF-36 | Efectos sobre criaturas | Vida | Casillas en llamas visibles para Vida y fuego resuelto antes de la percepción |
| RF-39 | Comportamiento | Vida | Llamar a los pasos 6 a 10 en el orden fijo y pasar el generador |
| RF-47 | Muerte | Vida | Casillas en llamas del tick para decidir la muerte por fuego |
| RF-49 | Estado completo | App | Serializar mapa, clima, eventos y generador de forma autodescrita |

## 4. Requisitos no funcionales aplicables

Los criterios completos están en la [sección 6](../spec/especificacion.md#6-requisitos-no-funcionales).

| ID | Requisito | Rol del subgrupo | Reparto |
| --- | --- | --- | --- |
| RNF-01 | Plataforma: Python 3.12 en Windows, macOS y Ubuntu; instalación con un comando | Colaborador | A empaqueta y prueba en los tres sistemas; E y V no usan código ni rutas específicas de un sistema |
| RNF-02 | Rendimiento: ≥ 60 ticks/s sin criaturas y ≥ 30 con 1000 | Responsable | E mide y optimiza el tick y el mapa; V mantiene el presupuesto de los pasos 6 a 10 con el cupo lleno |
| RNF-04 | Motor separado de la interfaz (no importa PySide6) | Responsable | E mantiene limpio el paquete del motor; A mantiene la regla de importación en la CI |
| RNF-05 | Reproducibilidad: misma semilla y acciones, mismo estado a 5000 ticks | Responsable | E es dueño del generador único, del orden del tick y de la prueba de oro; V sortea en orden estable; A guarda el estado del generador |
| RNF-06 | Configuración única validada al arrancar | Colaborador | A es dueño del cargador, la validación y la prueba de igualdad con el archivo; E y V son dueños de sus secciones |
| RNF-10 | Pruebas: cobertura ≥ 80 % del motor y pruebas de propiedades | Responsable | E es dueño de la cobertura y de las propiedades del mundo (agua fija); V de las propiedades de criaturas (cupo, genes, casilla única, sin canibalismo); A integra todo en la CI |
| RNF-12 | Errores: registro local y mensaje sin perder el último guardado | Colaborador | A captura, registra y muestra; E y V levantan errores propios del contrato (`ErrorEcosim`) |

Además aplica a todos los RF del subgrupo: **RNF-05** (nada de azar fuera del generador único) y **RNF-06** (cero valores escritos a mano).

## 5. Interfaces y contratos con otros subgrupos

Los contratos viven en `src/ecosim/contracts/`. Cambiarlos exige una RFC (`docs/rfc/`), subir `CONTRACT_VERSION` y actualizar los motores falsos en la misma PR.

| Contrato | Con quién | Qué entrega Ecosistema | Qué recibe | Estado |
| --- | --- | --- | --- | --- |
| `Engine` (`contracts/engine.py`) | App | `Simulation` con `step`, `apply`, `snapshot`, `to_state`, `state_hash` | Llamadas desde el `Runner`, siempre en un hilo | Existe |
| `Snapshot` (`contracts/snapshot.py`) | App | Tick, estación, temperatura, nutrientes, terreno, eventos activos; **ensambla** el snapshot completo | De Vida: `criaturas`, `especies`, `cupo` | Existe |
| Comandos (`contracts/commands.py`) | App, Vida | Atiende `FijarNutrientes`, `ProvocarEvento`, `CancelarEvento`; valida y encola; efecto al inicio del tick siguiente | Los otros cinco comandos los atiende Vida; `apply` los enruta | Existe |
| Avisos del motor (`contracts/events.py`) | App | `EventoNaturalIniciado`, `EventoNaturalTerminado` | `CupoAlcanzado`, `EspecieExtinguida` de Vida | Existe |
| Ranura de los pasos 6 a 10 | Vida | Llama a los pasos de Vida en orden fijo y les pasa el generador | Funciones `paso_06` a `paso_10` de Vida | **Propuesta** (hoy son métodos vacíos con su dueño anotado) |
| Vista del mundo (`engine/estado/mundo.py`) | Vida | Solo lectura: `terreno`, `alimento`, `llamas`, `temperatura`, `estacion`; escritura única `tomar_alimento(x, y)` | — | **Propuesta** |
| Serialización | App, Vida | `to_state` ensambla mapa, clima, eventos y generador; pide a Vida su sección | De Vida: bytes de especies, criaturas e historial | **Propuesta** (hoy solo mapa y metadatos) |
| Inspección de casilla | App | `inspeccionar_casilla(x, y)`: estado, humedad, alimento, contador | — | **Propuesta** (RF-20 no cabe hoy en el snapshot) |
| Configuración | Todos | Sección `config/ecosistema.py` | Cargador y validación de App | Existe (hoy dentro de `schema.py`) |

**Acuerdos de uso**

- **Orden entre pasos 4 y 5.** El fuego (paso 4) se resuelve antes que la vegetación (paso 5), y la vegetación no toca casillas que el fuego tocó ese tick.
- **Sorteos.** Ecosistema sortea 5 números por tick para los eventos y 1 por casilla para la vegetación, siempre, aunque no haga falta. Un sorteo dentro de un `if` rompe la reproducibilidad.
- **Humedad.** Se recalcula en el paso 3 y **no se guarda** (glosario). Vida no la necesita; el inspector la pide por `inspeccionar_casilla`.

## 6. Modelos de datos

**Posee** (los define, los escribe y responde por su guardado)

| Modelo | Atributos (sección 2 de la especificación) | Notas |
| --- | --- | --- |
| Simulación (parte del mundo) | semilla y estado del generador, tick, nutrientes, temperatura, estación, eventos activos | `id`, nombre y velocidad de simulación los posee **App** |
| Casilla | estado (6 valores), contador de ticks (solo llamas y quemada), vegetación previa (si arde), unidades de alimento (pasto o árbol) | Arreglos NumPy de 100×100; doble buffer |
| Evento | tipo, origen, tick de inicio, duración, ticks restantes, focos | El incendio dura mientras haya llamas |
| Calendario | ticks por estación (L) y factores por estación | Único parámetro del calendario |

**Consume**

| Modelo | De quién | Para qué |
| --- | --- | --- |
| Configuración validada | App (cargador) | Todos los parámetros de la sección 5 |
| Comandos del usuario | App | Nutrientes y eventos |
| Terreno inicial del editor | App | Constructor del motor |
| Población (solo conteo y posiciones, a través del snapshot) | Vida | Ensamblar el snapshot |

## 7. Tareas iniciales recomendadas (primer sprint, semanas 1 y 2)

Objetivo del sprint: dejar F1 a punto para **G1** (fin de la semana 3). Cada tarea sigue la plantilla de tarea del plan y cita su requisito.

| # | Tarea | Requisito | Entregable | Depende de | Hecho cuando |
| --- | --- | --- | --- | --- | --- |
| E-1 | Reorganizar `engine/` en `nucleo/`, `ecosistema/` y `estado/` y agregar el contrato de importación entre subgrupos | RNF-04 | PR de solo movimiento, sin cambios de comportamiento | Acuerdo del comité sobre el monorepo | La huella de oro no cambia y `verificar.py` termina en verde |
| E-2 | Humedad del paso 3 como función pura, con distancia de Chebyshev al agua | RF-22 (A.2) | `ecosistema/humedad.py` y prueba con los valores del anexo (p. ej. d = 1 en primavera ≈ 0.91) | E-1 | La prueba reproduce los valores del anexo A.2 |
| E-3 | Escalera de vegetación: subida y retroceso con humedad, un nivel por tick, doble buffer | RF-22, RF-23, RF-56 | Paso 5 real que sustituye al de ejemplo | E-2 | Pruebas con humedad fijada a mano en los dos sentidos; se quita la marca `xfail` de la prueba de pasto cerca del agua |
| E-4 | Alimento de la vegetación | RF-24 | Generación con `P·(0.7 + 0.3·h)` y máximo por casilla | E-3 | Prueba estadística con semilla fija |
| E-5 | Propiedad «el agua nunca cambia» y estado de mapa sin agua | RF-25 | Prueba de propiedades (Hypothesis) | E-3 | Pasa con mapas aleatorios y con mapa sin agua |
| E-6 | Presupuesto de sorteos por tick documentado | RNF-05 | Tabla en `docs/ia/errores-comunes.md` con quién sortea qué y en qué orden | E-3 | La revisan Vida y App |
| E-7 | Regenerar la prueba de oro de forma intencional | RNF-05 | PR con la etiqueta `golden-change` y explicación | E-3, E-4 | Dos líderes aprueban |
| E-8 | Prueba de la puerta G1: 10 000 ticks, pasto y árboles cerca del agua, guardado y carga idénticos | F1 | `tests/gates/test_g1.py` completo | E-3, E-4, App: RF-49 | Pasa en la CI |
| E-9 | Propuesta de RFC: vista del mundo, ranura de pasos 6 a 10, inspección de casilla | RF-20, RF-47 | RFC en `docs/rfc/` | — | Los tres líderes la comentan |

## 8. Pruebas y criterios de salida

**Tipos de prueba**

- **Unitarias de funciones puras:** humedad, temperatura, probabilidades de subir y bajar, factores de estación.
- **Estadísticas con semilla fija:** pasto por franja de distancia al agua; más sequías en verano que en invierno; más lluvias en otoño que en verano (RF-27).
- **Escenarios con semilla fija:** foco de incendio, barrera de agua, lluvia que apaga, cancelación (RF-30, RF-32 a RF-35, RF-51).
- **Propiedades:** el agua nunca cambia; un nivel por tick; una casilla en llamas o quemada no cambia de nivel por humedad.
- **Determinismo y oro:** misma semilla y mismos comandos, misma huella; huella a 5000 ticks guardada.
- **Rendimiento:** al menos 60 ticks por segundo sin criaturas (equipo de referencia por definir).

**Criterios de salida**

| Puerta | Criterio (sección 7 de la especificación) | Quién valida |
| --- | --- | --- |
| F1 / G1 | Una simulación sin criaturas corre 10 000 ticks con semilla fija, produce pasto y árboles cerca del agua, y se guarda y carga idéntica | Ecosistema y App |
| F3 / G3 (parte de Ecosistema) | Un incendio manual se propaga, el agua lo frena y la lluvia lo apaga; cancelarlo apaga sus casillas en llamas | Ecosistema, con Vida y App |

**Valores de referencia para la calibración** (no son requisitos; vienen de la comprobación del anexo A.4): con 10 000 ticks, sin criaturas ni eventos y semilla fija, el pasto cubre todo hasta unas 12 casillas del agua y el árbol hasta unas 3. Si el motor real se aleja mucho, se revisa primero la configuración y después el código.

## 9. Riesgos, supuestos y puntos de coordinación

| Riesgo | Efecto | Qué hacer |
| --- | --- | --- |
| La sequía actúa dos veces sobre el pasto (baja la humedad y multiplica el crecimiento por 0.3) | El efecto total puede ser demasiado fuerte | Medir en las semanas 7 a 9 y decidir con la regla de la pregunta E-DP-02 |
| Cualquier cambio de regla cambia la huella de oro | Oro regenerado sin revisión pierde su valor | Regenerar solo con PR etiquetada y dos aprobaciones |
| Sorteos condicionales | Rompen la reproducibilidad | Revisión de PR con la lista de sorteos (E-6) |
| Los pasos 6 a 10 están vacíos hasta F2 | Ecosistema no puede probar fuego sobre criaturas hasta entonces | Pruebas de F3 con población falsa; G3 completa al integrar Vida |
| Rendimiento con 1000 criaturas depende de Vida | Ecosistema responde por RNF-02 sin controlar la parte más cara | Medición separada por paso y presupuesto por paso |
| Mapa sin agua permitido por RF-09 | La distancia al agua no está definida | Resolver E-DP-01 antes de E-2 |

**Supuestos:** el equipo de referencia es de 4 núcleos y 8 GB (propuesta de la especificación, sin confirmar); los valores de la tabla de parámetros son iniciales; `L = 500` ticks por estación.

**Puntos de coordinación**

| Con quién | Cuándo | Qué se acuerda |
| --- | --- | --- |
| Vida | Semana 1 y al abrir cada RFC | Vista del mundo, ranura de pasos, orden de sorteos |
| App | Semana 1 | Datos del inspector, aviso del evento ya activo, constructor del motor desde el editor |
| Los tres líderes | Cada semana | Cambios de contrato y de especificación |

## 10. Enlaces a la especificación v0.4

| Tema | Enlace |
| --- | --- |
| Glosario y entidades | [Sección 2](../spec/especificacion.md#2-glosario-y-modelo-de-dominio) |
| Decisiones D-09 a D-14, D-18 a D-22, D-42 | [Sección 3](../spec/especificacion.md#3-decisiones-y-resolución-de-puntos-abiertos) |
| Requisitos funcionales | [Sección 4](../spec/especificacion.md#4-requisitos-funcionales) |
| Orden del tick | [Sección 5](../spec/especificacion.md#orden-del-tick) |
| Calendario y clima | [Sección 5](../spec/especificacion.md#calendario-y-clima) |
| Humedad, vegetación y regeneración | [Sección 5](../spec/especificacion.md#mapa-humedad-vegetación-y-regeneración) |
| Eventos naturales e incendios | [Sección 5](../spec/especificacion.md#eventos-naturales-1) · [Incendios](../spec/especificacion.md#incendios-1) |
| Tabla de parámetros | [Sección 5](../spec/especificacion.md#tabla-de-parámetros) |
| Requisitos no funcionales | [Sección 6](../spec/especificacion.md#6-requisitos-no-funcionales) |
| Fases | [Sección 7](../spec/especificacion.md#7-fuera-de-alcance-y-fases) |
| Fórmulas y constantes | [Anexo, sección 10](../spec/especificacion.md#10-anexo-fórmulas-y-constantes) |

## Trazabilidad RF → módulo → prueba

Los módulos siguen la estructura de la [propuesta de monorepo](monorepo-y-codeowners.md). «Existe» significa que ya hay al menos una prueba marcada con `@pytest.mark.req` en el kit; no implica que cubra todo el criterio (por ejemplo, la prueba de RF-29 hoy solo comprueba la temperatura y una de RF-22 está marcada `xfail`).

| Requisito | Módulo (propuesto) | Prueba | Estado |
| --- | --- | --- | --- |
| RF-21 | `engine/ecosistema/reloj.py` | `tests/engine/test_reloj.py` | Existe |
| RF-22 | `engine/ecosistema/vegetacion.py` | `tests/engine/test_vegetacion.py`<br>`tests/gates/test_g1.py` | Existe |
| RF-23 | `engine/ecosistema/vegetacion.py` | `tests/ecosistema/test_vegetacion_arbol.py` | Por escribir |
| RF-24 | `engine/ecosistema/vegetacion.py` | `tests/ecosistema/test_alimento.py` | Por escribir |
| RF-25 | `engine/ecosistema/mapa.py` | `tests/ecosistema/test_propiedades_mundo.py` | Por escribir |
| RF-26 | `engine/ecosistema/vegetacion.py` | `tests/ecosistema/test_regeneracion.py` | Por escribir |
| RF-56 | `engine/ecosistema/vegetacion.py` | `tests/ecosistema/test_retroceso.py` | Por escribir |
| RF-27 | `engine/ecosistema/eventos.py` | `tests/engine/test_eventos.py` | Existe |
| RF-28 | `engine/ecosistema/eventos.py, ui/ventana/` | `tests/engine/test_eventos.py`<br>`tests/ui/test_ventana.py` | Existe |
| RF-29 | `engine/ecosistema/eventos.py` | `tests/engine/test_reloj.py` | Existe |
| RF-30 | `engine/ecosistema/eventos.py` | `tests/ecosistema/test_lluvia.py` | Por escribir |
| RF-31 | `engine/ecosistema/eventos.py, ui/ventana/` | `tests/engine/test_eventos.py` | Existe |
| RF-51 | `engine/ecosistema/eventos.py, ui/ventana/panel_eventos.py` | `tests/engine/test_eventos.py` | Existe |
| RF-32 | `engine/ecosistema/fuego.py, ui/mapa_widget.py` | `tests/ecosistema/test_fuego_inicio.py` | Por escribir |
| RF-33 | `engine/ecosistema/fuego.py` | `tests/ecosistema/test_fuego_propagacion.py` | Por escribir |
| RF-34 | `engine/ecosistema/fuego.py` | `tests/ecosistema/test_fuego_extincion.py` | Por escribir |
| RF-35 | `engine/ecosistema/fuego.py` | `tests/ecosistema/test_fuego_efectos.py` | Por escribir |
| RNF-02 | `engine/nucleo/, engine/vida/` | `tests/bench/test_rendimiento.py`<br>por escribir: tests/bench/test_rendimiento_1000.py | Parcial |
| RNF-04 | `engine/, pyproject.toml (import-linter)` | `tests/platform/test_reglas_de_codigo.py` | Existe |
| RNF-05 | `engine/nucleo/` | `tests/engine/test_determinismo.py`<br>`tests/platform/test_golden.py`<br>`tests/platform/test_reglas_de_codigo.py` | Existe |
| RNF-10 | `tests/` | por escribir: tests/ecosistema/test_propiedades_mundo.py, tests/vida/test_propiedades_vida.py | Por escribir |

## Decisiones pendientes de este subgrupo

Cada decisión trae una **propuesta por defecto** para no bloquear el trabajo. Mientras no se decida, se usa la propuesta y se anota en la PR.

| ID | Pregunta | Propuesta por defecto | Decide | Antes de |
| --- | --- | --- | --- | --- |
| E-DP-01 | ¿Qué distancia al agua se usa en un mapa sin agua (RF-09 lo permite con aviso)? La especificación no la define | Distancia infinita: el aporte del agua es 0 y h = H₀ + m_ev | Líder de Ecosistema, con aprobación de la especificación | E-2 |
| E-DP-02 | La sequía baja la humedad y además multiplica por 0.3 el crecimiento (doble efecto) | Mantener ambos hasta medir; si el pasto desaparece del mapa en una sequía normal, reducir primero el desplazamiento m_ev y luego revisar f_ev | Ecosistema y Vida, en la calibración | Semana 7 |
| E-DP-03 | ¿Quién regenera y custodia la prueba de oro? | Ecosistema la custodia; regenerar exige dos aprobaciones (uno de Ecosistema y uno de otro subgrupo) | Comité técnico | Semana 1 |
| E-DP-04 | ¿Se agrega al contrato una vista del mundo y `inspeccionar_casilla`? | Sí, por RFC, con `FakeEngine` actualizado | Los tres líderes | Semana 2 |
| E-DP-05 | El guardado automático aparece en el paso 11 del tick, pero el motor no puede escribir en disco | El motor solo informa el tick; el `Runner` de App decide y ejecuta el autoguardado | Líderes de Ecosistema y App | Semana 2 |
| E-DP-06 | ¿Quién es el dueño del reparto de sorteos por tick? | Ecosistema; Vida registra su presupuesto por criatura | Comité técnico | Semana 2 |
