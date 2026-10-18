# Subgrupo App

> **Fuente de verdad:** [Especificación](especificacion.md) (aprobada). Este documento no crea requisitos: reparte y aterriza los existentes. Todo lo que no está en la especificación aparece marcado como **(propuesta)** y se cierra en «Decisiones pendientes de este subgrupo».
> **Fecha:** 2026-10-18 · **Subgrupos hermanos:** [Ecosistema](ecosistema.md) · [Vida](vida.md) 

## Estado actual del repositorio (2026-10-18)

El proyecto apenas empieza: hay estructura, documentos y configuración, **pero ningún código ni pruebas**.

| Elemento | Estado |
| --- | --- |
| `docs/` | Los cinco documentos del proyecto (`app.md`, `contratos.md`, `ecosistema.md`, `especificacion.md`, `vida.md`) |
| `src/simulador/app/`, `ecosistema/`, `vida/` | Carpetas vacías |
| Pruebas | Carpeta vacía. `pyproject.toml` apunta a `tests/`; si la carpeta del repositorio se llama `test/`, hay que renombrarla (tarea A-11) |
| `README.md` | Ramas `main`, `develop` y `feature/subgrupo-tarea`; ciclo de git; guía de instalación (`pip install -r requirements.txt` y `pip install -e .`); prueba de humo `import simulador.app, simulador.ecosistema, simulador.vida` |
| `requirements.txt` | `numpy>=1.26`, `matplotlib>=3.8`, `pytest>=8.0`, `ruff>=0.5` |
| `pyproject.toml` | Paquete `simulador` 0.1.0, Python ≥ 3.11, pytest sobre `tests/`, ruff con línea de 100 |

**Todo lo demás que este documento nombra** (contratos en código, `MotorFalso`, `AlmacenamientoMemoria`, configuración, CI, scripts, etiquetas, `CODEOWNERS`, pruebas, prueba de oro) **es una propuesta por crear**. Versiones anteriores lo describían como existente; no lo está.

**Falta para App:** `PySide6`, `pyqtgraph` y `pytest-qt` (D-02 de la especificación) no están en `requirements.txt`, que hoy incluye `matplotlib`; tampoco hay `.github/` (CI), `CODEOWNERS`, etiquetas ni comando de arranque. Ver A-11.

## 1. Propósito y alcance

App construye **todo lo que el usuario ve y toca, y todo lo que se guarda**: las pantallas y diálogos (P-02 a P-11), el editor de mapa, la ventana de simulación con sus controles, el dibujo del mapa y de las criaturas, el inspector, las gráficas por especie, el ejecutor que corre el motor en segundo plano, el guardado en SQLite con su biblioteca de simulaciones, la configuración validada, el empaquetado y la integración continua.

| Dentro del alcance | Fuera del alcance (lo hace otro subgrupo) |
| --- | --- |
| Pantallas P-02 a P-11 y sistema visual | Reglas del mapa, clima, eventos y fuego → **Ecosistema** |
| Editor de mapa con deshacer de 50 pasos | Reglas de criaturas, especies, genes y cupo → **Vida** |
| `Ejecutor` (hilo del motor), velocidad, pausa, autoguardado | El orden del tick y el generador aleatorio → **Ecosistema** |
| SQLite, biblioteca, esquema, migraciones, escritura atómica | Cálculo de estadísticas por especie → **Vida** |
| Cargador y validación de la configuración | Valores de los parámetros de cada sección → su subgrupo |
| Empaquetado, CI, pruebas en tres sistemas | Cuentas, red, multijugador (fuera de la versión 1) |

Fases que le tocan: **F1** (simulaciones, editor, ventana, guardado), **F2** (acciones en pausa), **F3** (etiqueta de eventos) y **F4** (zoom, inspector, gráficas). Puertas: **G1** y **G4**, y colabora en G2 y G3.

## 2. Responsabilidades principales y límites

**Responsabilidades**

1. El **flujo completo** del menú principal a la ventana de simulación (crear, editar el mapa, confirmar, cargar, renombrar, eliminar).
2. La **ventana de simulación**: mapa, pausa, velocidad (1 a 60 ticks por segundo), nutrientes, temperatura, tick, estación, n/cupo, etiqueta de eventos con botón de cancelar, botones de eventos, acceso a especies.
3. El **ejecutor** (`app/ejecutor/`): corre el motor fuera del hilo de la ventana, entrega instantáneas de solo lectura, encola comandos y decide cuándo guardar.
4. El **guardado**: biblioteca local única sin cuentas, escritura atómica, versión de esquema, migraciones, guardado manual y automático cada 1000 ticks, al pausar y al cerrar.
5. El **sistema visual**: colores de casillas, figura de criatura, paleta de 12 colores, contraste mínimo de 4.5:1, textos en español.
6. La **configuración**: cargador, validación de rangos al arrancar y prueba de que el archivo coincide con los valores por defecto.
7. **Empaquetado, integración continua y pruebas en Windows, macOS y Ubuntu** (RNF-01).
8. **Errores**: registro local y mensaje al usuario sin perder el último guardado (RNF-12).

**Límites (lo que App no hace)**

- No calcula reglas de simulación ni toca el estado del motor: solo lee `Instantanea` y envía comandos.
- No importa los módulos internos de `ecosistema` ni de `vida` (solo usa los contratos), no usa `PySide6` dentro del motor y no bloquea el hilo de la ventana.
- No inventa valores: todo número viene de la configuración.
- No cambia un contrato sin RFC aprobada por los tres líderes.
- No agrega cuentas ni propietarios de simulaciones (D-05 a D-08).

## 3. Requisitos funcionales asignados

R = responsable principal. Los criterios están resumidos: el texto completo, con Dado/Cuando/Entonces, está en la [sección 4](especificacion.md#4-requisitos-funcionales) de la especificación.

**3.1 Como responsable principal**

| ID | Requisito | Criterio de aceptación (resumen) | Fase | Depende de | Colabora |
| --- | --- | --- | --- | --- | --- |
| RF-06 | Menú principal | Crear o cargar; sin guardados, estado vacío con acceso a crear | F1 | D-02 | — |
| RF-07 | Crear simulación | Nombre libre abre el editor con 100×100 de tierra, nutrientes 50, tick 0, primavera | F1 | RF-06, D-37 | Ecosistema |
| RF-08 | Editor de mapa | Pincel, borrador y deshacer hasta 50 pasos | F1 | RF-07, D-17 | — |
| RF-09 | Confirmar el editor | Abre la ventana en pausa con tick 0; sin agua avisa y pide confirmación | F1 | RF-08, RF-14 | Ecosistema |
| RF-10 | Cargar simulación | Abre en pausa con el estado exacto guardado | F1 | RF-06, RF-49 | Ecosistema |
| RF-11 | Renombrar simulación | Nombre libre actualiza el título y se guarda | F1 | RF-10 | — |
| RF-12 | Eliminar simulación | Con confirmación que muestra el nombre, se borra y se vuelve al menú | F1 | RF-10, D-36 | — |
| RF-13 | Visualizar el mapa | Casillas con el color de su estado y criaturas encima | F1 | Instantanea, RF-55 | Vida |
| RF-14 | Pausar y reanudar | El botón detiene o continúa el tick y cambia su etiqueta | F1 | RNF-03 | — |
| RF-15 | Velocidad de simulación | Deslizador de 1 a 60 ticks/s, sin perder estado; el valor se guarda | F1 | RF-14, RF-48 | — |
| RF-16 | Nutrientes del suelo | Deslizador de 0 a 100; el valor rige desde el tick siguiente | F1 | D-12, RF-22 | Ecosistema |
| RF-17 | Reloj y temperatura | Muestra temperatura, tick, estación y n/cupo | F1 | RF-21, RF-41 | Ecosistema, Vida |
| RF-18 | Etiqueta de eventos | Lista eventos con ticks restantes y botón de cancelar; vacío dice «Sin eventos» | F3 | RF-27, RF-28, RF-51 | Ecosistema |
| RF-19 | Acciones en pausa | Crear especies, agregar criaturas, nutrientes y eventos se registran al instante | F2 | RF-37, RF-42 a RF-45, RF-28, RF-51 | Ecosistema, Vida |
| RF-20 | Zoom, desplazamiento e inspector | Zoom 1× a 8×, arrastre e inspector de casilla o criatura (con edad) | F4 | RF-13, RF-38 | Ecosistema, Vida |
| RF-46 | Datos de la especie | Gráficas de población y de cada estadística (media, mínimo, máximo) | F4 | RF-38, RF-45, D-33 | Vida |
| RF-48 | Guardado manual y automático | Botón, cada 1000 ticks, al pausar y al cerrar | F1 | RF-49, D-34 | — |
| RF-49 | Estado completo | Guardar y cargar deja mapa, clima, eventos, especies, criaturas, historial y azar idénticos | F1 | RNF-05, RF-38 | Ecosistema, Vida |
| RF-50 | Integridad | Un cierre brusco deja válida la última versión completa | F1 | RF-48, RNF-08 | — |

**3.2 Como colaborador**

| ID | Requisito | Responsable | Qué aporta este subgrupo |
| --- | --- | --- | --- |
| RF-28 | Provocar un evento | Ecosistema | Botones de evento, aviso de evento repetido y elección del foco en el mapa |
| RF-31 | Exclusión y repetición | Ecosistema | Mensaje de aviso cuando el evento ya está activo |
| RF-51 | Cancelar un evento | Ecosistema | Botón de cancelar de cada evento en la etiqueta |
| RF-32 | Inicio del incendio | Ecosistema | Clic en el mapa, radio del foco y aviso si no hay casillas inflamables |
| RF-37 | Crear especie | Vida | Formulario P-09 (nombre, cantidad, modo avanzado) y color asignado |
| RF-38 | Estadísticas de la criatura | Vida | Mostrar los valores en el inspector y en el detalle de la especie |
| RF-41 | Límite de criaturas | Vida | Indicador n/cupo resaltado y avisos |
| RF-42 | Agregar criaturas | Vida | Aviso «Se agregaron X de N por el límite de criaturas (C)» |
| RF-43 | Eliminar criaturas | Vida | Botón y cantidad en el detalle de la especie (P-08) |
| RF-44 | Extinguir especie | Vida | Botón de extinguir y confirmación |
| RF-45 | Eliminar especie | Vida | Confirmación que muestra el nombre |
| RF-52 | Límite de especies activas | Vida | Aviso «Ya hay 12 especies activas. Extingue o elimina una para continuar.» |
| RF-55 | Color de la especie | Vida | Paleta de 12 colores como constante y dibujo de las criaturas |

## 4. Requisitos no funcionales aplicables

Los criterios completos están en la [sección 6](especificacion.md#6-requisitos-no-funcionales).

| ID | Requisito | Rol del subgrupo | Reparto |
| --- | --- | --- | --- |
| RNF-01 | Plataforma: Python 3.11 o superior en Windows, macOS y Ubuntu; instalación según el README | Responsable | A empaqueta y prueba en los tres sistemas; E y V no usan código ni rutas específicas de un sistema |
| RNF-03 | Fluidez: ≥ 30 FPS, el motor corre fuera del hilo de la ventana | Responsable | A mantiene el ejecutor en segundo plano y el dibujo desde la instantánea |
| RNF-04 | Motor separado de la interfaz (no importa PySide6) | Colaborador | E mantiene limpio el paquete del motor; A mantiene la regla de importación en la CI |
| RNF-05 | Reproducibilidad: misma semilla y acciones, mismo estado a 5000 ticks | Colaborador | E es dueño del generador único, del orden del tick y de la prueba de oro; V sortea en orden estable; A guarda el estado del generador |
| RNF-06 | Configuración única validada al arrancar | Responsable | A es dueño del cargador, la validación y la prueba de igualdad con el archivo; E y V son dueños de sus secciones |
| RNF-08 | Persistencia robusta: guardado atómico y versión de esquema | Responsable | A implementa la escritura atómica y las migraciones |
| RNF-09 | Tamaño del guardado < 20 MB con 1000 criaturas y 5000 muestras por especie | Responsable | A mide el archivo; V mantiene acotado el historial (D-33) |
| RNF-10 | Pruebas: cobertura ≥ 80 % del motor y pruebas de propiedades | Colaborador | E es dueño de la cobertura y de las propiedades del mundo (agua fija); V de las propiedades de criaturas (cupo, genes, casilla única, sin canibalismo); A integra todo en la CI |
| RNF-11 | Idioma (español) y accesibilidad (contraste 4.5:1; distancias de la paleta) | Responsable | A revisa textos y contrastes; V garantiza que la asignación de colores respete la paleta (RF-55) |
| RNF-12 | Errores: registro local y mensaje sin perder el último guardado | Responsable | A captura, registra y muestra; E y V levantan errores propios del contrato (`ErrorSimulador`) |

Además aplica a todos los RF del subgrupo: **RNF-03** (la ventana nunca se congela) y **RNF-06** (cero valores escritos a mano).

## 5. Interfaces y contratos con otros subgrupos

> **RFC** en este repositorio significa un pull request hacia `develop` que modifica `docs/contratos.md`, aprobado por los tres líderes. `docs/contratos.md` hoy solo tiene la plantilla y las seis secciones por pareja de subgrupos, vacías; ningún contrato está implementado en código.

| Contrato | Con quién | Qué entrega App | Qué recibe | Estado |
| --- | --- | --- | --- | --- |
| `Motor` (`contratos/motor.py`) | Ecosistema | Llamadas a `avanzar`, `aplicar`, `obtenerInstantanea`, `aEstado` desde un único hilo (el `Ejecutor`) | `Simulacion` y `MotorFalso` | Por crear |
| `Instantanea` (`contratos/instantanea.py`) | Ecosistema, Vida | Dibuja a partir de arreglos de solo lectura; nunca los modifica | Tick, estación, temperatura, nutrientes, terreno, criaturas, especies, eventos, cupo | Por crear |
| Comandos (`contratos/comandos.py`) | Ecosistema, Vida | Los ocho comandos, siempre por `Motor.aplicar` | Errores `ComandoInvalido` y `ComandoNoSoportado` | Por crear |
| Avisos del motor (`contratos/avisos.py`) | Ecosistema, Vida | Los traduce a mensajes (cupo alcanzado, especie extinguida, evento terminado) | Lista de avisos por tick | Por crear |
| `Almacenamiento` (`contratos/almacenamiento.py`) | Ecosistema, Vida | `AlmacenamientoSqlite` e `AlmacenamientoMemoria` | Bytes del estado (`aEstado`) | Por crear; ver A-DP-01 |
| Constructor del motor desde el editor | Ecosistema | Terreno confirmado, semilla y nombre | Motor en tick 0, pausa, primavera | **Propuesta** |
| Inspección de casilla y de criatura | Ecosistema, Vida | Pide los datos al hacer clic | `inspeccionarCasilla`, `inspeccionarCriatura` | **Propuesta** (RF-20) |
| Historial por especie | Vida | Lo guarda y lo grafica | Muestras por especie | **Propuesta** (RF-46) |
| Paleta (`contratos/paleta.py`) | Vida | Dibuja con los 12 colores | Índice de color de cada especie | **Propuesta** |
| Configuración | Todos | Cargador y validación; sección `configuracion/app.py` | Secciones de Ecosistema y Vida | Por crear |

**Acuerdos de uso**

- **La ventana solo lee.** Recibe una `Instantanea` del `Ejecutor`; leerlo nunca espera al motor aunque este vaya lento.
- **Los comandos llevan tick.** `aplicar` valida y encola; el efecto ocurre al inicio del tick siguiente, también en pausa (RF-19).
- **Se trabaja contra falsos.** `MotorFalso` e `AlmacenamientoMemoria` permiten construir y probar pantallas desde el primer día; cada cambio de contrato los actualiza en la misma PR.

## 6. Modelos de datos

**Posee**

| Modelo | Atributos | Notas |
| --- | --- | --- |
| Simulación (parte de biblioteca) | id, nombre, velocidad de simulación | Nombre único; la velocidad se guarda (RF-15). La semilla, el tick y el estado del generador los posee Ecosistema |
| Registro de guardado | nombre, tick, fecha de guardado, estado (bytes autodescritos) | Escritura atómica; versión de esquema en el archivo |
| Esquema SQLite | versión de esquema y migraciones | Abrir una versión anterior migra o muestra un error claro |
| Mapa del editor | terreno inicial, pila de deshacer y rehacer (50 pasos) | Solo existe antes de confirmar (D-15) |
| Ajustes de interfaz | figura de criatura, tamaño de casilla (6 px), zoom (1× a 8×) | La figura se elige en el archivo de configuración |
| Registro de errores | archivo de registro local | RNF-12 |

**Consume**

| Modelo | De quién | Para qué |
| --- | --- | --- |
| `Instantanea` | Ecosistema y Vida | Dibujar y mostrar la barra de estado |
| Estado del motor (bytes opacos) | Ecosistema y Vida | Guardar y cargar sin interpretarlos |
| Historial por especie | Vida | Gráficas (RF-46) y guardado |
| Secciones de configuración | Ecosistema y Vida | Validar rangos al arrancar |

## 7. Tareas iniciales recomendadas (primer sprint, semanas 1 y 2)

Objetivo del sprint: dejar F1 a punto para **G1** (fin de la semana 3), trabajando contra `MotorFalso` e `AlmacenamientoMemoria` mientras Ecosistema cierra las reglas.

| # | Tarea | Requisito | Entregable | Depende de | Hecho cuando |
| --- | --- | --- | --- | --- | --- |
| A-1 | Formalizar el formato de guardado (blob único; D-35 ya actualizado) | RF-49, RNF-08 | RFC que documenta el blob único, las columnas de metadatos y la tabla de historial (A-DP-01) | Ecosistema: E-9 | Los tres líderes aprueban |
| A-2 | Flujo de menú, nueva simulación y cargar, con estados vacíos | RF-06, RF-07, RF-10 | Pantallas P-02, P-03 y P-05 | `AlmacenamientoMemoria` | Prueba del flujo crear → editar → cargar con pytest-qt sin pantalla |
| A-3 | Lógica del editor de mapa sin Qt | RF-08 | Pincel de 1 a 5, borrador, rectángulo, limpiar, deshacer y rehacer de 50 pasos | — | Pruebas unitarias; el deshacer revierte el último trazo |
| A-4 | Confirmar el editor y avisar si no hay agua | RF-09 | Diálogo con Continuar o Volver al editor; motor en tick 0 y pausa | A-3, E-9 | Prueba de aceptación del criterio de RF-09 |
| A-5 | Ventana de simulación mínima | RF-13 a RF-17 | Mapa desde la instantánea, pausa, velocidad, nutrientes, barra de estado | `Ejecutor`, `MotorFalso` | La ventana se redibuja sin congelarse con un motor lento |
| A-6 | Política de autoguardado en el `Ejecutor` | RF-48 | Guardado manual, cada 1000 ticks, al pausar y al cerrar | A-DP-02, E-DP-05 | Pruebas de cada disparador |
| A-7 | Prueba de migración de esquema | RNF-08, RF-50 | Prueba que abre un archivo de versión anterior y migra o rechaza con error claro | — | Pasa en la CI |
| A-8 | Crear la CI y comprobar la instalación | RNF-01 | `.github/workflows/integracion_continua.yml` y `nocturna.yml` corriendo en Ubuntu, Windows y macOS; instalación con `pip install -r requirements.txt` y `pip install -e .` | A-DP-04 | Las dos corridas pasan, o cada fallo tiene su issue |
| A-9 | Crear `configuracion/` con `base.py` (cargador y validación), una sección por subgrupo (`app.py`, `ecosistema.py`, `vida.py`) y `por_defecto.toml` | RNF-06 | Los valores de la tabla de parámetros de la especificación | — | La prueba de igualdad entre el archivo y los valores por defecto pasa |
| A-10 | Crear etiquetas, plantillas de PR y `CODEOWNERS` | — | Etiquetas por subgrupo (y `cambio-de-oro`, `cambio-de-especificacion`) y reglas de revisión | Aprobación del comité | Una PR de prueba pide la revisión correcta |
| A-11 | Completar dependencias y configuración de pruebas | RNF-01, RNF-10 | `requirements.txt` y `pyproject.toml` con PySide6, pyqtgraph, pytest-qt, hypothesis, pytest-cov e import-linter; marca `requisito` de pytest registrada; carpeta de pruebas llamada `tests/`; matplotlib se queda solo para scripts de análisis (las gráficas usan pyqtgraph, D-02) | — | `pip install -r requirements.txt` funciona y `pytest` no avisa de marcas desconocidas |
| A-12 | Crear los contratos base en código y los falsos | RF-49, RNF-03 | `contratos/` con `Motor`, `Instantanea`, comandos, avisos y `Almacenamiento`; `MotorFalso` y `AlmacenamientoMemoria` | E-9, V-9, A-11 | Las pantallas se construyen y se prueban contra los falsos |
| A-13 | Crear el `Ejecutor` (hilo del motor) | RF-14, RF-15, RNF-03, RNF-12 | `app/ejecutor/ejecutor.py`: corre el motor fuera del hilo de la ventana, entrega instantáneas de solo lectura, encola comandos, pausa y velocidad | A-12 | Con un motor lento, la ventana no se congela |
| A-14 | Crear `AlmacenamientoSqlite` | RF-10 a RF-12, RF-48 a RF-50, RNF-08 | `app/almacenamiento/sqlite.py`: esquema con versión, escritura atómica y biblioteca de simulaciones (A-DP-01) | A-12, A-DP-03 | El contrato de `Almacenamiento` pasa contra `AlmacenamientoSqlite` y `AlmacenamientoMemoria`; un corte simulado deja válida la versión anterior |

## 8. Pruebas y criterios de salida

**Tipos de prueba**

- **Unitarias sin Qt:** editor (trazos y pila de deshacer), política de autoguardado, validación de nombres.
- **Contrato de `Almacenamiento`:** la misma batería corre contra `AlmacenamientoSqlite` e `AlmacenamientoMemoria`.
- **Integridad:** corte simulado a mitad de un guardado deja válida la versión anterior (RF-50).
- **Migración:** abrir una versión anterior del esquema (RNF-08).
- **Interfaz con `pytest-qt`** en modo sin pantalla; revisión manual de fluidez.
- **Rendimiento de la ventana:** 30 FPS o más; leer la instantánea no espera al motor (RNF-03).
- **Tamaño del guardado:** menos de 20 MB con el cupo inicial y 5000 muestras por especie (RNF-09).
- **Accesibilidad:** contraste de 4.5:1 y textos en español (RNF-11).

**Criterios de salida**

| Puerta | Criterio (sección 7 de la especificación) | Quién valida |
| --- | --- | --- |
| F1 / G1 | Una simulación sin criaturas corre 10 000 ticks con semilla fija, produce pasto y árboles cerca del agua, y se guarda y carga idéntica | Ecosistema y App |
| F4 / G4 | Las gráficas de una simulación de 20 000 ticks se abren sin congelar la ventana y el inspector muestra una casilla y una criatura, incluida su edad | App, con Vida y Ecosistema |
| Apoyo a G2 y G3 | Acciones en pausa, etiqueta de eventos y botones funcionan con el motor real | App |

## 9. Riesgos, supuestos y puntos de coordinación

| Riesgo | Efecto | Qué hacer |
| --- | --- | --- |
| Qt en la CI sin pantalla | Pruebas de interfaz que fallan solo en CI | `QT_QPA_PLATFORM=offscreen` y bibliotecas del sistema que se incluirán en `integracion_continua.yml` |
| Entregar la instantánea a 60 ticks por segundo | Copias costosas con muchas criaturas | Medir; los arreglos son pequeños (100×100 de `uint8` y n×3 de `int32`) |
| Archivos en Windows (bloqueos y rutas) | La escritura atómica se comporta distinto | Pruebas de guardado en los tres sistemas en la corrida nocturna |
| Cerrar con cambios sin guardar (sección 8) frente a guardar al cerrar (RF-48) | Dos comportamientos distintos | Resuelto en A-DP-02: se guarda al cerrar sin preguntar y el diálogo solo aparece si el guardado falla |
| Historial de 5000 muestras por especie y 12 especies | Guardado más grande que 20 MB | Medir en F4 y reducir con D-33 |
| Contratos que cambian a mitad del trabajo | Pantallas rotas | Trabajar contra falsos y exigir RFC |

**Supuestos:** una sola ventana de simulación abierta a la vez; no hay cuentas; la biblioteca es local; el equipo de referencia es de 4 núcleos y 8 GB (confirmado en A-DP-05).

**Puntos de coordinación**

| Con quién | Cuándo | Qué se acuerda |
| --- | --- | --- |
| Ecosistema | Semana 1 | Constructor del motor desde el editor, datos del inspector, aviso del evento ya activo |
| Vida | Semana 1 | Formularios de especie, historial, paleta, avisos de cupo y de límite |
| Los tres líderes | Cada semana | Cambios de contrato y de especificación |

## 10. Enlaces a la especificación v0.4

| Tema | Enlace |
| --- | --- |
| Glosario y entidades | [Sección 2](especificacion.md#2-glosario-y-modelo-de-dominio) |
| Decisiones D-02, D-05 a D-08, D-15, D-17, D-33 a D-41 | [Sección 3](especificacion.md#3-decisiones-y-resolución-de-puntos-abiertos) |
| Requisitos funcionales | [Sección 4](especificacion.md#4-requisitos-funcionales) |
| Tabla de parámetros (registro y autoguardado) | [Sección 5](especificacion.md#tabla-de-parámetros) |
| Requisitos no funcionales | [Sección 6](especificacion.md#6-requisitos-no-funcionales) |
| Fases | [Sección 7](especificacion.md#7-fuera-de-alcance-y-fases) |
| Diseño de interfaz | [Sección 8](especificacion.md#8-diseño-de-interfaz) |
| Inventario de pantallas | [Sección 8](especificacion.md#inventario-de-pantallas) |
| Estados vacíos, errores y confirmaciones | [Sección 8](especificacion.md#estados-vacíos-errores-y-confirmaciones) |
| Sistema visual y paleta | [Sección 8](especificacion.md#sistema-visual) |
| Trazabilidad | [Sección 9](especificacion.md#9-trazabilidad-y-registro-de-decisiones) |

## Trazabilidad RF → módulo → prueba

Los módulos y las pruebas son una **propuesta**: hoy el repositorio solo tiene las carpetas vacías `src/simulador/app/`, `ecosistema/` y `vida/` y una carpeta de pruebas vacía, así que **ninguna prueba existe todavía y todo está «Por escribir»**. Las rutas de módulos son relativas a `src/simulador/` y las de pruebas empiezan en `tests/`. Cada prueba lleva `@pytest.mark.requisito("RF-xx")`.

| Requisito | Módulo (propuesto) | Prueba | Estado |
| --- | --- | --- | --- |
| RF-06 | `app/interfaz/pantallas/menu_principal.py` | `tests/app/test_flujo_menu.py` | Por escribir |
| RF-07 | `app/interfaz/pantallas/nueva_simulacion.py` | `tests/app/test_flujo_crear.py` | Por escribir |
| RF-08 | `app/interfaz/editor/editor_mapa.py` | `tests/app/test_editor_mapa.py` | Por escribir |
| RF-09 | `app/interfaz/editor/editor_mapa.py, ecosistema/nucleo/simulacion.py` | `tests/app/test_flujo_crear.py` | Por escribir |
| RF-10 | `app/almacenamiento/sqlite.py, app/interfaz/pantallas/cargar.py` | `tests/app/test_contrato_almacenamiento.py` | Por escribir |
| RF-11 | `app/almacenamiento/sqlite.py, app/interfaz/ventana/` | `tests/app/test_contrato_almacenamiento.py` | Por escribir |
| RF-12 | `app/almacenamiento/sqlite.py, app/interfaz/ventana/` | `tests/app/test_contrato_almacenamiento.py` | Por escribir |
| RF-13 | `app/interfaz/visor_mapa.py` | `tests/app/test_visor_mapa.py` | Por escribir |
| RF-14 | `app/ejecutor/ejecutor.py, app/interfaz/ventana/` | `tests/app/test_ejecutor.py`<br>`tests/app/test_ventana.py` | Por escribir |
| RF-15 | `app/ejecutor/ejecutor.py, app/interfaz/ventana/` | `tests/app/test_velocidad.py` | Por escribir |
| RF-16 | `app/interfaz/ventana/, ecosistema/nucleo/simulacion.py` | `tests/ecosistema/test_eventos.py` | Por escribir |
| RF-17 | `app/interfaz/ventana/barra_estado.py` | `tests/ecosistema/test_reloj.py`<br>`tests/app/test_ventana.py` | Por escribir |
| RF-18 | `app/interfaz/ventana/panel_eventos.py` | `tests/app/test_panel_eventos.py` | Por escribir |
| RF-19 | `app/ejecutor/ejecutor.py, app/interfaz/ventana/` | `tests/ecosistema/test_eventos.py`<br>`tests/app/test_ejecutor.py` | Por escribir |
| RF-20 | `app/interfaz/visor_mapa.py, app/interfaz/inspector.py` | `tests/app/test_inspector.py` | Por escribir |
| RF-46 | `app/interfaz/especies/detalle_especie.py, app/almacenamiento/historial.py` | `tests/app/test_graficas.py` | Por escribir |
| RF-48 | `app/ejecutor/autoguardado.py, app/almacenamiento/sqlite.py` | `tests/app/test_autoguardado.py` | Por escribir |
| RF-49 | `app/almacenamiento/sqlite.py, ecosistema/nucleo/serializacion.py` | `tests/ecosistema/test_determinismo.py`<br>`tests/gates/test_g1.py` | Por escribir |
| RF-50 | `app/almacenamiento/sqlite.py` | `tests/app/test_sqlite.py` | Por escribir |
| RNF-01 | `pyproject.toml, .github/workflows/` | por escribir: tests/app/test_instalacion.py (CI en tres sistemas) | Por escribir |
| RNF-03 | `app/ejecutor/ejecutor.py, app/interfaz/` | `tests/app/test_ejecutor.py` | Por escribir |
| RNF-06 | `configuracion/` | `tests/app/test_configuracion.py`<br>`tests/app/test_reglas_de_codigo.py` | Por escribir |
| RNF-08 | `app/almacenamiento/` | `tests/app/test_sqlite.py` | Por escribir |
| RNF-09 | `app/almacenamiento/, vida/historial.py` | por escribir: tests/app/test_tamano_guardado.py | Por escribir |
| RNF-11 | `app/interfaz/, contratos/paleta.py` | por escribir: tests/app/test_contraste_y_paleta.py | Por escribir |
| RNF-12 | `app/ejecutor/ejecutor.py, app/interfaz/` | `tests/app/test_ejecutor.py` | Por escribir |