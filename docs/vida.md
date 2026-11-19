# Vida (Grupo B)

Todo lo relativo a **los seres vivos**: cómo es una criatura, cómo decide qué hacer, cómo gasta energía, come, se reproduce, hereda rasgos, envejece y muere; y cómo se administra la población. Código en `src/simulador/vida/`; configuración en `vida/config.py` (`ConfigVida`); pruebas en `tests/vida/`.

## Archivos

| Archivo | Contenido |
|---|---|
| `tipos.py` | Dieta, `Estado` (los estados del autómata), causas de muerte, tipos de objetivo. |
| `config.py` | `ConfigVida`: todas las constantes en un solo lugar, inmutable y validada. |
| `estadisticas.py` | Rasgos S, V, R de una criatura; herencia con mutación (`cruzar`). |
| `criatura.py` | Un individuo: energía, metabolismo, comer, edad, reproducción, muerte. No decide nada. |
| `automata_criatura.py` | **El autómata**: percibir → elegir estado → actuar. |
| `percepcion.py` | Funciones puras de distancia y movimiento en la cuadrícula. |
| `poblacion.py` | Todas las criaturas y especies; ejecuta el tick; nacimientos, muertes, extinciones. |
| `especie.py`, `historial.py` | Especies y series de población y promedios (alimentan las gráficas). |
| `puertos.py` | El contrato `MapaPuerto` que Vida exige al mapa. |
| `adaptadores/` | Mapa y contexto falsos para pruebas. |
| `simulacion_vida.py` | Simulador de Vida sin interfaz ni Ecosistema (CLI). |

## El autómata de estados finitos de cada criatura

Cada criatura es una máquina **M = (Q, Σ, δ, q₀, F)**:

- **Q** = {EXPLORAR, BUSCAR_ALIMENTO, BUSCAR_PAREJA, HUIR, MUERTA}
- **q₀** = EXPLORAR · **F** = {MUERTA} (final y absorbente)
- **Σ** = lo que percibe en su radio de visión (¿amenaza o fuego?, ¿comida?, ¿pareja elegible?) más su **intención** (alimento o pareja), que depende de su energía.
- **δ** determinista con **prioridades** (tabla siguiente). Es una máquina tipo **Moore**: en cada estado ejecuta una acción distinta.

No es un AFD “puro”: la entrada es un conjunto de percepciones y hay variables auxiliares (energía, edad, intención), así que formalmente es un autómata finito con variables. La parte aleatoria (explorar) está en la *acción*, no en δ.

| Condición (en orden de prioridad) | Estado | Acción |
|---|---|---|
| 1. Hay una amenaza o fuego visible | **HUIR** | Da hasta V pasos, cada uno el que más la aleja. |
| 2. Intención = pareja y hay pareja elegible a la vista | **BUSCAR_PAREJA** | Se acerca; a distancia ≤ 1 intenta reproducirse. |
| 3. Intención = pareja y no ve pareja | **EXPLORAR** | Camina al azar con inercia. |
| 4. Intención = alimento y ve comida | **BUSCAR_ALIMENTO** | Va hacia la mejor comida; si le alcanza el paso, come. |
| 5. Nada de lo anterior | **EXPLORAR** | Camina al azar: 70 % sigue recto (`INERCIA_EXPLORAR`). |
| Energía ≤ 0, edad ≥ vida máxima, capturada, en llamas o eliminada | **MUERTA** | Sale del juego al final del tick. |

**Segundo autómata, la intención** (2 estados con histéresis, para evitar oscilar):

| Desde | Hacia | Condición |
|---|---|---|
| ALIMENTO | PAREJA | energía ≥ 70 % de E_MAX y sin cooldown de reproducción |
| PAREJA | ALIMENTO | energía < 50 % de E_MAX **o** en cooldown (60 ticks tras reproducirse) |

### Un turno

`Poblacion.actualizar()` prepara el tick de cada criatura (acumula velocidad), baraja el orden y cada una hace:

1. **Percibir:** fuegos, otras criaturas (amenazas, presas, parejas) y plantas con comida dentro de su radio.
2. **Decidir:** aplica la tabla. Para comida elige el objetivo de mayor puntaje `ganancia / (distancia + 1)`.
3. **Actuar:** huir, ir a comer, ir hacia la pareja o explorar.
4. **Cobrar metabolismo:** resta energía; si llega a 0, muere de hambre. Se cobra al final porque el costo depende de si se movió.
5. **Envejecer:** +1 de edad; si llega a su vida máxima, muere de vejez.

Al final del tick se retiran las muertas, entran las crías y se declaran las especies extintas.

## Rasgos, energía y reglas

| Rasgo | Significado | Efecto |
|---|---|---|
| **S** tamaño | Masa relativa (1.0 = referencia) | Gasta menos por unidad de masa, puede cazar a los pequeños, vive algo más y da más comida como presa. |
| **V** velocidad | Casillas por tick (admite decimales; se acumula) | Llega antes a la comida o huye mejor, pero gasta mucho (crece con V²). |
| **R** visión | Radio de percepción (se redondea a casillas) | Ve más lejos, pero cuesta energía cada tick. |

| Dieta | Plantilla (S, V, R) | η plantas | η carne |
|---|---|---|---|
| Herbívoro | (1.0, 2.0, 7.0) | 0.60 | — |
| Omnívoro | (1.3, 1.5, 5.0) | 0.20 | 0.40 |
| Carnívoro | (1.6, 1.0, 4.0) | — | 0.70 |

- **Energía:** máxima 100; la cría nace con 30.
- **Gasto por tick** = f_T · S^−0.25 · (A + C·R + K·V²·m), con A = 0.30, C = 0.10, K = 0.30 y m = 1 solo si se movió. El exponente −0.25 viene de la ley de Kleiber. **f_T** = 1 + 0.15·((T − 22)/10)²: mínimo a 22 °C.
- **Ganancia al comer** (% de energía): planta = η · biomasa / S; presa = η · 100 · S_presa / S_depredador.
- **Depredación:** solo a otra especie con S_depredador ≥ 1.2 · S_presa y dieta que coma carne; la presa se come completa.
- **Reproducción:** ambos padres con energía ≥ 70, a distancia ≤ 1, sin cooldown (60 ticks), cada uno paga 25; hace falta cupo y una casilla libre a ≤ 2. Los padres pagan 50 en total y la cría nace con 30 (no se crea energía).
- **Herencia:** cada rasgo de la cría = √(rasgo_madre · rasgo_padre) · e^N(0, σ), con σ = 0.10: media geométrica con mutación proporcional.
- **Vejez:** vida máxima = 1500 · S^0.25 ticks, ±15 % al nacer.
- **Mundo:** máximo 500 criaturas y 1 por casilla; distancia de Chebyshev y 8 direcciones.

## Evolución

No hay función de aptitud: la **selección natural emerge** de tres ingredientes: variación (mutación), compromisos (más V y R ayudan a encontrar comida pero gastan más; más S ahorra por unidad pero necesita más comida) y supervivencia diferencial (el que no come muere; el que sí, se reproduce).

Observación medida durante el desarrollo: con la población en el tope de 500 y comida de sobra, **nadie nace ni muere** y la evolución se detiene. Con σ = 0.10 la variación se duplica y con costos de V y R mayores aparece deriva real (velocidad media de 2.0 a 1.7 y visión de 7.0 a 6.2 en una semilla). Posibles palancas: `VIDA_BASE` (más mortalidad) o menos comida.

## Población, especies e historial

- `Poblacion` guarda las criaturas, un **índice por casilla** y las especies (ACTIVA / EXTINTA / ELIMINADA). Una especie se extingue al llegar a 0 individuos y se puede repoblar; al eliminarla, su nombre queda bloqueado.
- Al agregar criaturas se puede elegir que nazcan con los **promedios actuales** de la especie (`promedio_actual`) o con su plantilla original.
- `Historial` registra cada tick población y promedios de S, V, R y energía (máximo 2000 puntos por especie; si se pasa, se reduce).
- Todo se convierte a diccionario y vuelve (`a_dict` / `desde_dict`) para guardar y cargar.

## Rendimiento

El costo principal es percibir. La búsqueda de plantas usa NumPy a través del método opcional `MapaPuerto.plantas_en_radio` y solo conserva la mejor planta libre; existe una versión de referencia más lenta y una prueba (`tests/integracion/test_percepcion_rapida.py`) que comprueba que ambas dan exactamente el mismo estado.

## Límites conocidos

- Las tres dietas no siempre coexisten a largo plazo sin ajustar parámetros (con las plantillas actuales, 3 dietas vivas a 10 000 ticks en unas 8 de cada 10 semillas).
- Con muchas criaturas la percepción sigue siendo lo más costoso.
- La instantánea solo expone posición y especie de cada criatura; la energía y la edad individuales no llegan a la interfaz.
