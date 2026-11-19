# ProyectoAutomatas

Descripción: Simulador de evolución de criaturas en un ecosistema.

---

## Sobre subgrupos
- **Subgrupo Ecosistema**
    - **Responsabilidades:**
    Desarrollo del ciclo de simulación, mapa, clima y eventos.
    - **Líder:**
    - **Integrantes:**
- **Subgrupo Vida**
    - **Responsabilidades:**
    Desarrollo del comportamiento y estadisticas de especies y criaturas.
    - **Líder:**
    - **Integrantes:**
- **Subgrupo App**
    - **Responsabilidades:**
    Persistencia de datos e interfaz de la app.
    - **Líder:**
    - **Integrantes:**

## Sobre acuerdos y documentación

En la carpeta `docs/` se encuentran la especificación, los acuerdos técnicos y los estándares del proyecto:
- **`docs/especificacion.md`:** especificación general del sistema, glosario, decisiones de diseño (D-01 a D-42) y requisitos (RF y RNF).
- **`docs/contratos.md`:** define formalmente las interfaces, funciones, métodos y atributos que cada subgrupo expone a los demás.
- **`docs/guia-de-calidad.md`:** estándares de código, reglas de arquitectura, convenciones de nombres y flujo de Git para todo el equipo.
- **`docs/pruebas-y-trazabilidad.md`:** metodología de pruebas, verificación de requisitos y matriz de trazabilidad.
- **`docs/app.md`:** arquitectura, diseño de interfaz y trazabilidad del Subgrupo App.
- **`docs/vida.md`:** diseño biológico, autómatas, genética y trazabilidad del Subgrupo Vida.
- **`docs/ecosistema.md`:** autómata celular, clima, eventos y trazabilidad del Subgrupo Ecosistema.

## Estructura del repositorio

```text
ProyectoAutomatas/
├── .github/                 # Workflows de CI (GitHub Actions) y CODEOWNERS
├── docs/                    # Especificación, contratos y guías de calidad
├── scripts/                 # Scripts de verificación y trazabilidad
├── src/simulador/
│   ├── app/                 # Persistencia (SQLite), ejecutor, editor e interfaz PySide6
│   ├── configuracion/       # Cargador y validación TOML de parámetros
│   ├── contratos/           # Protocolos, errores, comandos, instantánea y motor falso
│   ├── ecosistema/          # Autómata celular, mapa, clima y eventos
│   └── vida/                # Criaturas, especies, autómata, percepción y población
└── tests/                   # Batería de pruebas automatizadas (app y vida)
```

## Sobre las ramas de desarrollo
- **main**
    - **Proposito:**
    versiones estables, lo que se entrega.
- **develop**
    - **Proposito:**
    Donde se integra el trabajo de todos.
- **ramas de trabajo**
    - **Proposito:**
    Una tarea concreta de una persona.
    - **Nota:**
    Los nombres de las ramas de trabajo siguen el patrón `feature/subgrupo-tarea`

## Ciclo de git diario
1. Partir siempre desde develop actualizado
- `git checkout develop`
- `git pull`

2. Crear tu rama de trabajo
- `git checkout -b feature/subgrupo-tarea`

3. Programar, y guardar cambios en commits pequeños
- `git add <archivos>`
- `git commit -m "tipo(subgrupo): descripción"`

4. Subir tu rama
- `git push -u origin feature/subgrupo-tarea`

5. Abrir un `pull request` hacia `develop`

## Primeros pasos: clonar y configurar el proyecto

Esta guía es para quien clona el repositorio por primera vez. Todos los comandos se ejecutan desde la **raíz del proyecto** (la carpeta `ProyectoAutomatas`).

### Requisitos previos

- **Git** instalado (`git --version`).
- **Python 3.11 o superior** (`python --version`).
- Haber **aceptado la invitación** al repositorio que GitHub envía por correo.

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd ProyectoAutomatas
```

La URL está en GitHub, en el botón verde **Code**.

### 2. Cambiarse a `develop`

Al clonar, Git deja el repositorio en `main`. El trabajo diario parte de `develop`:

```bash
git checkout develop
git pull
```

### 3. Abrir el proyecto en VS Code

Usa **File → Open Folder** y elige la carpeta raíz (`ProyectoAutomatas`), **no** una subcarpeta como `src`. Luego abre la terminal en **Terminal → New Terminal**.

### 4. Crear el entorno virtual

```bash
python -m venv .venv
```

### 5. Activar el entorno virtual

**Windows (PowerShell)**

```powershell
.venv\Scripts\activate
```

**Mac / Linux**

```bash
source .venv/bin/activate
```

La línea de la terminal debe empezar con `(.venv)`. Si no lo ves, el entorno no está activo.

> **Windows:** si aparece el error de que *la ejecución de scripts está deshabilitada*, ejecuta este comando una sola vez y repite la activación:
>
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

### 6. Instalar las dependencias y el proyecto

Con el entorno activo:

```bash
pip install -r requirements.txt
pip install -e .
```

Escribe el punto final de `pip install -e .`, con un espacio antes: indica que se instala el proyecto de la carpeta actual.

### 7. Prueba de humo

```bash
python -c "import simulador.app, simulador.ecosistema, simulador.vida; print('ok')"
```

Si imprime `ok`, el entorno quedó listo.

### 8. Antes de programar: crear tu rama

Nadie trabaja directamente en `develop` ni en `main`. Cada tarea va en su propia rama:

```bash
git checkout develop
git pull
git checkout -b feature/<subgrupo>-<tarea>
```

Ejemplo: `feature/vida-reproduccion`.

### 9. Antes de subir tu trabajo: pruebas y revisión

Con el entorno activo, ejecuta estos comandos y confirma que pasan:

```bash
pytest
ruff check .
lint-imports
python scripts/verificar_trazabilidad.py
```

- `pytest` corre las pruebas automatizadas (468 pruebas en el repositorio).
- `ruff check .` revisa el estilo y formato del código.
- `lint-imports` comprueba la regla de arquitectura («El motor no importa la aplicación»).
- `python scripts/verificar_trazabilidad.py` comprueba que cada marca `@pytest.mark.requisito` apunte a un requisito válido de `docs/especificacion.md`.

### Qué se repite y qué no

| Cuándo | Qué hacer |
|---|---|
| Una sola vez | Pasos 1, 4, 6 y 7 |
| Cada vez que abres una terminal nueva | Paso 5 (activar el entorno) |
| Cada vez que empiezas una tarea | Paso 8 |
| Si alguien cambia `requirements.txt` | Repetir `pip install -r requirements.txt` |
| Antes de cada pull request | Paso 9 (`pytest`, `ruff check`, `lint-imports`, `verificar_trazabilidad`) |

### Errores comunes

| Error | Causa probable | Solución |
|---|---|---|
| `ModuleNotFoundError` | El entorno no está activo, la terminal no está en la raíz, o se omitió `pip install -e .` | Verifica que veas `(.venv)`, que estés en la raíz, y repite el paso 6 |
| `python` no se reconoce | Python no está instalado o no está en el PATH | Reinstala Python marcando *Add to PATH*; en Windows prueba con `py` |
| Versión de Python anterior a 3.11 | Python desactualizado | Instala una versión más reciente |
| `pip install -e` falla | Falta el punto final o no estás en la raíz | Ejecuta `pip install -e .` desde la raíz |
