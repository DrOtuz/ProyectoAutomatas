# Especificación del simulador de ecosistema

Documento de **requisitos vigentes**: qué debe hacer el programa y cómo se comprueba. Describe el proyecto tal como está implementado. El *cómo funciona por dentro* está en [`ecosistema.md`](ecosistema.md), [`vida.md`](vida.md) y [`app.md`](app.md); las interfaces entre grupos, en [`contratos.md`](contratos.md).

Cada prueba se vincula con un requisito mediante `@pytest.mark.requisito("RF-xx")` y `scripts/verificar_trazabilidad.py` comprueba que todas las marcas apunten a un requisito de este documento (ver [`pruebas-y-trazabilidad.md`](pruebas-y-trazabilidad.md)). Los identificadores no se reutilizan.

## 1. Resumen

Aplicación de escritorio en Python que simula un ecosistema en un mapa de 100 × 100 casillas. El mapa evoluciona como **autómata celular** (terreno, vegetación y fuego) y sobre él viven criaturas que funcionan como **autómatas de estados finitos**, se reproducen, mutan y evolucionan. El usuario observa, interviene y analiza la simulación en tiempo real. Guarda y carga simulaciones en una biblioteca local, sin cuentas.

## 2. Glosario

| Término | Definición |
| --- | --- |
| Simulación | Mundo completo: mapa, reloj, clima, eventos, especies y criaturas. |
| Biblioteca | Conjunto de simulaciones guardadas en el equipo. No hay cuentas ni propietarios. |
| Tick | Unidad discreta de tiempo. Todo el mundo avanza un paso por tick. |
| Velocidad de simulación | Ticks por segundo (1 a 30), controlados con un deslizador. |
| Estación, año | Una estación dura 500 ticks y un año 4 estaciones (2000 ticks): primavera, verano, otoño, invierno. |
| Casilla | Celda del mapa. Estados: tierra, agua, pasto, árbol, en llamas o quemada. |
| Humedad | Valor de 0 a 1 por casilla, derivado de la cercanía al agua, la estación y los eventos. |
| Nutrientes | Nivel global del suelo de 0 a 100, controlado por el deslizador. |
| Evento natural | Sequía, lluvia o incendio, con origen natural o manual. |
| Foco | Casilla donde empieza un incendio. |
| Especie | Grupo de criaturas con nombre, dieta, color y plantilla de estadísticas. Solo se reproducen entre sí. |
| Dieta | Herbívoro, omnívoro o carnívoro. |
| Criatura | Individuo con estadísticas heredables, energía, edad y un autómata de estados finitos. |
| Estadísticas | Tamaño (S), velocidad (V) y visión (R): heredables y mutables; cada una tiene un rango permitido y un costo de energía. |
| Energía | De 0 a 100. Se gasta cada tick y se recupera comiendo; a 0 la criatura muere de hambre. |
| Cupo | Máximo global de criaturas (500). |

## 3. Requisitos funcionales

### Simulaciones y editor de mapa

| ID | Requisito | Criterio de aceptación |
| --- | --- | --- |
| RF-06 | Menú principal | Dado que se abre la aplicación, entonces se muestra el menú principal con crear o cargar simulación. Sin simulaciones guardadas, cargar muestra un estado vacío con acceso directo a crear. |
| RF-07 | Crear simulación | Dado el menú, cuando se elige crear y se indica un nombre que no usa otra simulación guardada, entonces se abre el editor con 100×100 casillas de tierra, nutrientes en 50, tick 0 y primavera. |
| RF-08 | Editor de mapa | Dado el editor, cuando se pinta con el pincel de agua, entonces esas casillas pasan a agua; el borrador las devuelve a tierra y deshacer revierte el último trazo (hasta 50 pasos). |
| RF-09 | Confirmar el editor | Dado el editor, cuando se confirma, entonces se abre la ventana de simulación en pausa con tick 0. Si no hay agua, se avisa y se pide confirmación. |
| RF-10 | Cargar simulación | Dada la lista de simulaciones guardadas, cuando se elige una, entonces se abre en pausa con el estado exacto guardado. |
| RF-11 | Renombrar simulación | Dada una simulación abierta, cuando se cambia el nombre a uno que no usa otra simulación guardada, entonces el título se actualiza y se guarda. |
| RF-12 | Eliminar simulación | Dada una simulación abierta, cuando se confirma el diálogo que muestra su nombre, entonces se borra de la biblioteca y se vuelve al menú principal. |

### Ventana de simulación

| ID | Requisito | Criterio de aceptación |
| --- | --- | --- |
| RF-13 | Visualizar el mapa | Dada la ventana abierta, cuando el tick avanza, entonces cada casilla se pinta con el color de su estado y las criaturas se dibujan encima, con el color de su especie. |
| RF-14 | Pausar y reanudar | Dada una simulación abierta, cuando se pulsa el botón, entonces el tick se detiene o continúa y la etiqueta del botón cambia. La simulación empieza en pausa. |
| RF-15 | Velocidad de simulación | Dado el deslizador de 1 a 30 ticks por segundo, cuando se mueve, entonces el ritmo cambia sin perder estado y el valor se guarda. |
| RF-16 | Nutrientes del suelo | Dado el deslizador de 0 a 100, cuando se mueve, entonces el valor global cambia y se usa desde el siguiente tick. |
| RF-17 | Reloj y temperatura | Dada la ventana abierta, entonces muestra la temperatura, el tick, la estación y el total de criaturas (n/cupo, con cupo 500). |
| RF-18 | Etiqueta de eventos | Dados eventos activos, entonces el panel los lista con sus ticks restantes (o casillas en llamas) y un botón para cancelar cada uno. Sin eventos dice “Sin eventos”. Los mensajes de error del panel se quitan solos a los 6 segundos. |
| RF-19 | Acciones en pausa | Dada la pausa, cuando se crean especies, se agregan criaturas, se mueven los nutrientes, se provoca o se cancela un evento, entonces el cambio se registra al instante; las órdenes sobre especies y criaturas se ven de inmediato y los eventos y nutrientes actúan al reanudar. |
| RF-20 | Zoom, desplazamiento e inspector | Dado el mapa, cuando se usa la rueda, se arrastra o se hace clic en una casilla, entonces hay zoom de 1× a 8×, desplazamiento y un inspector con el terreno de la casilla y, si hay una criatura, su especie y la población de la especie. |

### Mapa como autómata celular

| ID | Requisito | Criterio de aceptación |
| --- | --- | --- |
| RF-21 | Estaciones | Dado el reloj, cuando se cumplen los ticks de una estación (500), entonces cambia la estación en el orden primavera, verano, otoño, invierno y la temperatura base sigue a la estación. |
| RF-22 | Tierra a pasto | Dada una casilla de tierra, entonces pasa a pasto con una probabilidad por tick de 0.002 × crecimiento × (0.5 + humedad); con nutrientes en 0 no aparece pasto nuevo. |
| RF-23 | Pasto a árbol | Dado un pasto, entonces pasa a árbol con una probabilidad por tick de 0.0005 × crecimiento × (0.5 + humedad). |
| RF-24 | Alimento de la vegetación | Dado un pasto o un árbol, entonces su alimento regenera cada tick 0.5 u (pasto, máximo 30) o 1.0 u (árbol, máximo 60), multiplicado por el factor de crecimiento (estación × eventos × nutrientes / 50). Una criatura que come toma todo el alimento de su casilla. |
| RF-25 | Agua fija | Dada cualquier casilla de agua, entonces conserva su estado durante toda la simulación. |
| RF-26 | Regeneración | Dada una casilla quemada, cuando pasan 150 ticks, entonces vuelve a tierra y puede crecer pasto de nuevo. |

### Eventos naturales

| ID | Requisito | Criterio de aceptación |
| --- | --- | --- |
| RF-27 | Aparición natural | Dada una estación, entonces cada tick se sortea cada evento con probabilidad λ / L, con λ los eventos esperados por estación y L los ticks por estación (500). Hay más sequías en verano que en invierno y más lluvias en otoño que en verano. |
| RF-28 | Provocar un evento | Dada la ventana, cuando se pulsa el botón de sequía o lluvia, entonces se activa con su duración y aparece en el panel. El incendio pide elegir el foco con un clic en el mapa (Esc cancela). |
| RF-29 | Sequía | Dada una sequía activa, entonces la humedad baja 0.35 en todo el mapa, el crecimiento de la vegetación se multiplica por 0.3, la temperatura sube 3 °C y los focos naturales de incendio son 3 veces más probables. |
| RF-30 | Lluvia | Dada una lluvia activa, entonces la humedad sube 0.35, el crecimiento se multiplica por 1.5, la propagación del fuego se multiplica por 0.3 y cada casilla en llamas se apaga con probabilidad 0.30 por tick. |
| RF-31 | Repetición de eventos | Dado un evento activo, cuando se provoca otro del mismo tipo, entonces se rechaza con un aviso. Sequía, lluvia e incendio pueden coincidir. |
| RF-51 | Cancelar un evento | Dado un evento activo, cuando se pulsa su botón de cancelar, entonces termina al inicio del tick siguiente y desaparece del panel. Si es un incendio, sus casillas en llamas pasan a quemada. |

### Incendios

| ID | Requisito | Criterio de aceptación |
| --- | --- | --- |
| RF-32 | Inicio del incendio | Dado un incendio natural, entonces empieza en una casilla inflamable al azar. Dado uno manual, cuando se hace clic en una casilla, entonces se prende el foco (el comando admite radio de 0 a 3). Sin casillas inflamables en el área, o con otro incendio activo, se rechaza con un aviso. |
| RF-33 | Propagación | Dada una casilla de pasto o árbol vecina de una en llamas, entonces se incendia con la probabilidad por vecina descrita en `ecosistema.md` (según vegetación, humedad, temperatura, estación y lluvia). El árbol es menos inflamable que el pasto (0.08 frente a 0.12). Tierra y agua nunca arden. |
| RF-34 | Extinción | Dada una casilla en llamas, cuando pasan 3 ticks (pasto) u 8 (árbol), entonces pasa a quemada. El incendio termina cuando no queda ninguna casilla en llamas. |
| RF-35 | Efectos sobre la vegetación | Dada una casilla que se incendia, entonces pierde su alimento y su vegetación; al quemarse queda como quemada. |
| RF-36 | Efectos sobre criaturas | Dada una criatura que ve fuego en su radio de visión, entonces pasa al estado huir. Si está en una casilla en llamas, muere. |

### Especies y criaturas

| ID | Requisito | Criterio de aceptación |
| --- | --- | --- |
| RF-37 | Crear especie | Dado un nombre libre, una cantidad inicial y una dieta (y, en modo avanzado, tamaño, velocidad y visión base dentro de su rango), cuando se crea, entonces la especie recibe un color de la paleta (que se muestra en el formulario antes de crear) y sus criaturas se colocan en casillas transitables al azar, hasta el cupo. |
| RF-38 | Estadísticas de la criatura | Dada una criatura, entonces tiene tamaño, velocidad y visión como estadísticas heredables, y energía (0 a 100), edad y vida máxima como estado. |
| RF-39 | Comportamiento | Dado el autómata de la criatura, entonces solo transita entre los cinco estados definidos (explorar, buscar alimento, buscar pareja, huir y muerta) y respeta las prioridades de `vida.md`. |
| RF-40 | Reproducción y mutación | Dadas dos criaturas de la misma especie con energía suficiente, sin espera de reproducción, a distancia ≤ 1 y con una casilla libre cerca, cuando se reproducen, entonces cada una paga 25 de energía, la cría nace con 30 y cada estadística es la media geométrica de los padres por e^N(0, σ), con σ = 0.10. |
| RF-41 | Límite de criaturas | Dado el mapa con 500 criaturas, entonces no se crean criaturas nuevas ni nacimientos, y los padres no pagan el costo de reproducirse. |
| RF-42 | Agregar criaturas | Dada una especie activa o extinguida, cuando se agregan N criaturas, entonces se agregan min(N, cupo libre) y, si N supera el cupo, se informa. Nacen con la plantilla de la especie o, si se elige, con los promedios actuales. |
| RF-43 | Eliminar criaturas | Dada una especie, cuando se eliminan N criaturas, entonces se retiran N al azar (o todas si hay menos). Una especie sin criaturas pasa a extinguida. |
| RF-44 | Extinguir especie | Dada una especie, cuando se extingue, entonces se retiran todas sus criaturas y la especie sigue en la lista, marcada como extinguida, con opción de agregar criaturas. |
| RF-45 | Eliminar especie | Dada una especie, cuando se confirma, entonces desaparece de la lista, su nombre queda bloqueado en esa simulación y su historial se borra. |
| RF-46 | Datos de la especie | Dada una especie, cuando se abre su detalle, entonces hay gráficas de población y del promedio de tamaño, velocidad, visión y energía a lo largo de los ticks. |
| RF-47 | Muerte | Dada una criatura con energía 0, que llega a su vida máxima, en una casilla en llamas o comida por otra criatura, entonces muere y deja de contar en el cupo en ese mismo tick. |
| RF-52 | Límite de especies activas | Dado el máximo de 12 especies activas, cuando se intenta crear una con todas las plazas ocupadas, entonces se rechaza con un aviso que sugiere extinguir o eliminar una. |
| RF-53 | Depredación | Dadas dos criaturas de distinta especie, la primera con dieta que come carne y tamaño de al menos 1.2 veces el de la segunda, cuando la primera busca alimento y alcanza a la segunda, entonces se la come completa: la presa muere y la primera gana energía según los tamaños. Criaturas de la misma especie nunca se comen entre sí. |
| RF-54 | Una criatura por casilla | Dado cualquier tick, entonces no hay dos criaturas en la misma casilla ni criaturas en el agua. El orden de los turnos se baraja cada tick. Sin casilla libre cerca de los padres, no hay nacimiento. |
| RF-55 | Color de la especie | Dadas las especies activas, entonces cada una tiene un color de la paleta de 12 y se elige el primero que no usa otra especie. Al extinguirse una especie, su color queda libre. |

### Persistencia

| ID | Requisito | Criterio de aceptación |
| --- | --- | --- |
| RF-48 | Guardado manual y automático | Dada una simulación abierta, entonces se guarda con el botón (que muestra “Guardando…” y luego “Guardado (tick N)”), cada 1000 ticks, al pausar y al cerrar. |
| RF-49 | Estado completo | Dada una simulación guardada y cargada, entonces mapa, clima, eventos, especies, criaturas, historial y generadores aleatorios son idénticos. Misma semilla y mismas acciones dan el mismo resultado. |
| RF-50 | Integridad | Dado un cierre brusco durante un guardado, entonces la última versión guardada completa sigue siendo válida al reabrir (escritura en transacción). |

### Requisitos retirados

Sus números no se reutilizan, para conservar la trazabilidad.

| ID | Requisito retirado | Motivo |
| --- | --- | --- |
| RF-01 a RF-05 | Crear cuenta, validar nombre y contraseña, modificarlos, iniciar y cerrar sesión, eliminar cuenta | La versión 1 no tiene cuentas. |
| RF-56 | Retroceso de la vegetación por falta de humedad | No se implementó: la vegetación solo crece. |

## 4. Reglas y parámetros

Las reglas están descritas con sus fórmulas en [`ecosistema.md`](ecosistema.md) y [`vida.md`](vida.md). Los valores viven en los archivos de configuración (RNF-06) y son puntos de partida calibrados con la simulación en marcha.

| Grupo | Parámetro | Valor |
| --- | --- | --- |
| Reloj y clima | Ticks por estación / por día / amplitud diaria | 500 / 24 / 3 °C |
| Vegetación | Alimento máximo, pasto / árbol | 30 u / 60 u |
| Vegetación | Regeneración por tick, pasto / árbol | 0.5 u / 1.0 u |
| Vegetación | Crecimiento por tick, tierra a pasto / pasto a árbol | 0.002 / 0.0005 |
| Vegetación | Ticks de quemada a tierra | 150 |
| Eventos | Duración de sequía / lluvia | 150–300 ticks / 50–120 ticks |
| Fuego | Propagación base, pasto / árbol | 0.12 / 0.08 |
| Fuego | Ticks en llamas, pasto / árbol | 3 / 8 |
| Fuego | Radio máximo del foco manual | 3 |
| Criaturas | Energía máxima / de la cría / costo de reproducir | 100 / 30 / 25 |
| Criaturas | Umbral de buscar pareja / de dejarla | 70 % / 50 % de la energía máxima |
| Criaturas | Espera entre reproducciones | 60 ticks |
| Criaturas | Metabolismo A / C / K | 0.30 / 0.10 / 0.30 |
| Criaturas | Mutación σ | 0.10 |
| Criaturas | Razón mínima de tamaño para cazar | 1.2 |
| Criaturas | Vida máxima | 1500 · S^0.25 ticks (±15 %) |
| Especies | Cupo global de criaturas / máximo de especies activas | 500 / 12 |
| App | Velocidad de simulación | 1 a 30 ticks por segundo |
| App | Intervalo de autoguardado | 1000 ticks |

## 5. Requisitos no funcionales

| ID | Requisito | Criterio de aceptación |
| --- | --- | --- |
| RNF-01 | Plataforma | Corre con Python 3.11 o superior (probado en Windows). Se instala y abre con `ejecutar.bat` / `ejecutar.sh` o con `pip install -e .` y `python -m simulador`, sin configuración extra. |
| RNF-02 | Rendimiento del motor | Sin interfaz, el motor ejecuta unos 35 a 45 ticks por segundo con ~240 criaturas y unos 20 con el cupo de 500 (medido; ver `arquitectura.md`). Si no alcanza la velocidad pedida, la simulación corre a la que pueda. |
| RNF-03 | Fluidez de la interfaz | La ventana se redibuja a ~30 FPS y no se congela, porque el motor corre en un hilo aparte. |
| RNF-04 | Motor separado de la interfaz | Los paquetes `ecosistema` y `vida` no importan nada de la aplicación ni de PySide6 (regla de `lint-imports`). |
| RNF-05 | Reproducibilidad | Con la misma semilla y las mismas acciones en los mismos ticks, el estado es idéntico (misma huella). |
| RNF-06 | Configuración única | Ningún parámetro de simulación está escrito en la lógica: se leen de la configuración, que valida rangos al arrancar. |
| RNF-08 | Persistencia robusta | El guardado es transaccional y el estado lleva número de versión. Un estado de una versión no soportada muestra un error claro sin dañar la biblioteca. |
| RNF-09 | Tamaño del guardado | Una simulación con el cupo lleno ocupa menos de 20 MB (el estado se guarda comprimido). |
| RNF-10 | Pruebas | La suite automática (`pytest`) cubre los tres grupos; las pruebas de interfaz corren sin ventanas. |
| RNF-11 | Idioma y accesibilidad | Interfaz en español, con colores claros y de contraste legible. |
| RNF-12 | Errores | Un error de una orden se muestra al usuario sin perder el estado; un fallo inesperado del motor detiene el hilo y conserva el último guardado. |

RNF-07 se retiró con las cuentas y su número no se reutiliza.

## 6. Fuera de alcance

- Cuentas, contraseñas y propietarios de simulaciones; multijugador o red.
- Interfaces distintas de PySide6.
- Fuentes de alimento distintas del pasto y los árboles; sed y bebida.
- Viento, relieve, ríos o lagos dinámicos; eventos localizados por zona; nutrientes por casilla.
- Edición del mapa durante la simulación.
- Más de 12 especies activas a la vez.

## 7. Trabajo pendiente conocido

- Conectar `registro_errores` al hilo del motor para escribir `errores.log`.
- Que la instantánea incluya energía y edad por criatura para un inspector más completo.
- Calibrar la coexistencia de las tres dietas a largo plazo y la mortalidad en el tope de 500 criaturas (ver `vida.md`).
- Mejorar el rendimiento con el cupo lleno (acciones de las criaturas, paso de vegetación).
