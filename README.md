# Simulador de ecosistema

Aplicación de escritorio en Python que simula un ecosistema en un mapa de 100 × 100 casillas. El mapa funciona como un **autómata celular** (vegetación, fuego, clima y estaciones) y sobre él viven **criaturas** que son **autómatas de estados finitos**: buscan comida, huyen, se reproducen, mutan y evolucionan. Es el proyecto de la materia *Autómatas y Lenguajes Formales*.

Puedes dibujar el mapa, crear especies (herbívoras, omnívoras o carnívoras), provocar sequías, lluvias e incendios, ver gráficas por especie y guardar la simulación para continuarla después.

---

## Cómo ejecutarlo

### Requisitos

- **Python 3.11 o superior** ([descargar](https://www.python.org/downloads/); en Windows marca *Add python.exe to PATH*).
- Conexión a internet **solo la primera vez**, para instalar las dependencias (NumPy, PySide6 y pyqtgraph).

### La forma fácil

| Sistema | Qué hacer |
|---|---|
| **Windows** | Doble clic en `ejecutar.bat` |
| **Mac / Linux** | En una terminal: `./ejecutar.sh` |

El script crea el entorno virtual `.venv` la primera vez, instala lo necesario y abre el simulador. Las siguientes veces solo lo abre.

### A mano

Desde la carpeta del proyecto:

```bash
python -m venv .venv

# Windows (PowerShell):  .venv\Scripts\activate
# Mac / Linux:           source .venv/bin/activate

pip install -e .
python -m simulador
```

Si no activas el entorno, también puedes escribir `.venv\Scripts\python -m simulador` (Windows) o `.venv/bin/python -m simulador` (Mac / Linux).

> **Windows:** si PowerShell dice que *la ejecución de scripts está deshabilitada*, ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` o usa `ejecutar.bat`.

### Dónde se guardan las simulaciones

En un archivo SQLite llamado `biblioteca.db`:

- Windows: `%LOCALAPPDATA%\Simulador\`
- Otros sistemas: `~/AppData/Local/Simulador/`
- O la carpeta que indiques en la variable de entorno `SIMULADOR_CARPETA_DATOS`.

---

## Cómo se usa

1. **Menú principal → Nueva simulación.** Escribe un nombre y dibuja el mapa en el editor (agua y tierra, con pincel, deshacer y rehacer). Al confirmar, la vegetación se siembra sola, más densa cerca del agua.
2. **Ventana de simulación.** Empieza en pausa. Pulsa **Reanudar**, ajusta la **velocidad** (1 a 30 ticks por segundo) y los **nutrientes** del suelo. La rueda del ratón hace zoom y arrastrar mueve el mapa; un clic en una casilla muestra su información.
3. **Especies.** Desde el botón de especies puedes crear una (nombre, cantidad, dieta y, en modo avanzado, tamaño, velocidad y visión), agregar o quitar criaturas, extinguirla o eliminarla, y ver sus gráficas de población y promedios. Hay un máximo de 500 criaturas y 12 especies activas.
4. **Eventos.** El panel lateral permite provocar **sequía** o **lluvia**, o un **incendio**: pulsa el botón y haz clic en el mapa donde quieres que empiece (Esc cancela). Cada evento activo se puede cancelar.
5. **Guardar.** El botón *Guardar* escribe la simulación; además se guarda sola cada 1000 ticks, al pausar y al cerrar. Desde el menú principal se puede cargar, renombrar o eliminar.

---

## Cómo está organizado

```
ProyectoAutomatas/
├── ejecutar.bat · ejecutar.sh     Abren el simulador (instalan lo necesario la primera vez)
├── pyproject.toml                 Paquete, dependencias y configuración de pytest, ruff e import-linter
├── requirements.txt               Instala el proyecto          (pip install -r requirements.txt)
├── requirements-dev.txt           Instala además las herramientas de desarrollo
├── src/simulador/
│   ├── ecosistema/                Grupo A: mapa, reloj, eventos, fuego, vegetación, ciclo del tick
│   ├── vida/                      Grupo B: criaturas, autómata de estados, población, evolución
│   ├── app/                       Grupo C: ventanas, ejecutor en hilo, guardado SQLite, editor de mapa
│   ├── contratos/                 Interfaces comunes entre grupos (Motor, comandos, instantánea…)
│   ├── integracion/               Une A + B + C en un solo motor (SimuladorEcosistema)
│   └── configuracion/             Parámetros de cada grupo (valores y rangos validados)
├── tests/                         Pruebas automáticas, una carpeta por grupo
├── docs/                          Documentación (ver abajo)
├── scripts/                       Herramientas del repositorio (verificación de trazabilidad)
└── .github/                       Integración continua, revisores y plantilla de Pull Request
```

La idea central: **cada grupo trabaja contra contratos, no contra el código de los demás**. Vida no conoce el mapa de Ecosistema (solo un puerto `MapaPuerto`) y la aplicación no conoce el motor real (solo la clase abstracta `Motor`). Detalles en [`docs/arquitectura.md`](docs/arquitectura.md).

## Documentación

| Documento | Para qué sirve |
|---|---|
| [`docs/arquitectura.md`](docs/arquitectura.md) | Visión general: orden del tick, hilos, guardado, determinismo |
| [`docs/ecosistema.md`](docs/ecosistema.md) | Grupo A: mapa, fuego (autómata celular), clima, eventos, vegetación |
| [`docs/vida.md`](docs/vida.md) | Grupo B: autómata de la criatura, energía, reproducción, evolución |
| [`docs/app.md`](docs/app.md) | Grupo C: interfaz, ejecutor, guardado, configuración |
| [`docs/contratos.md`](docs/contratos.md) | Interfaces que cruzan fronteras entre grupos |
| [`docs/especificacion.md`](docs/especificacion.md) | Requisitos funcionales y no funcionales vigentes (RF / RNF) |
| [`docs/pruebas-y-trazabilidad.md`](docs/pruebas-y-trazabilidad.md) | Cómo se prueba y cómo se vincula cada prueba con un requisito |
| [`docs/guia-de-calidad.md`](docs/guia-de-calidad.md) | Estándares de código, revisión y Git |

---

## Para quien desarrolla

```bash
pip install -r requirements-dev.txt     # proyecto + pytest, pytest-qt, ruff, import-linter

pytest                                  # pruebas (las de interfaz corren sin abrir ventanas)
ruff check .                            # estilo
lint-imports                            # reglas de arquitectura: el motor no importa la interfaz
python scripts/verificar_trazabilidad.py    # cada marca @pytest.mark.requisito apunta a un requisito real
```

La integración continua (`.github/workflows/integracion_continua.yml`) corre estos mismos comandos en Windows con Python 3.11 en cada push y Pull Request hacia `develop` y `main`.

### Ramas

- `main`: versiones estables, lo que se entrega.
- `develop`: donde se integra el trabajo de todos.
- `feature/<subgrupo>-<tarea>`: una tarea concreta, creada siempre desde `develop` actualizado y fusionada por Pull Request con *Create a merge commit*.

Más reglas (nombres, commits, contratos, revisión) en [`docs/guia-de-calidad.md`](docs/guia-de-calidad.md).

### Subgrupos y responsables

| Subgrupo | Responsabilidad | Líder |
|---|---|---|
| **Ecosistema** | Ciclo del tick, mapa, clima, eventos, fuego y vegetación | @MrMishaelysium |
| **Vida** | Criaturas, autómata de decisión, población y evolución | @DrOtuz |
| **App** | Interfaz, ejecutor, guardado, configuración, CI | @Juan-var-camp |

---

## Problemas frecuentes

| Problema | Causa probable | Solución |
|---|---|---|
| `No module named 'simulador'` | El proyecto no está instalado en el entorno activo | Ejecuta `pip install -e .` desde la raíz con el entorno activo, o usa `ejecutar.bat` / `ejecutar.sh` |
| `python` no se reconoce | Python no está instalado o no está en el PATH | Instálalo marcando *Add to PATH*; en Windows prueba `py -3` |
| Error de versión de Python | Tienes una versión anterior a 3.11 | Instala Python 3.11 o superior |
| `Faltan dependencias del simulador` | PySide6 o pyqtgraph no están instalados | `pip install -e .` |
| La ventana se ve lenta con muchas criaturas | La simulación es más pesada que el refresco | Baja la velocidad en el deslizador o reduce la población |
