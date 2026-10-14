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

## Sobre acuerdos entre subgrupos

En la carpeta docs hay un documento llamado 'contratos.md' en el que se definirá qué funciones y atributos ofrece cada subgrupo a los demás.

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
- `git add .`
- `git commit -m "descripción"`

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

### Qué se repite y qué no

| Cuándo | Qué hacer |
|---|---|
| Una sola vez | Pasos 1, 4, 6 y 7 |
| Cada vez que abres una terminal nueva | Paso 5 (activar el entorno) |
| Cada vez que empiezas una tarea | Paso 8 |
| Si alguien cambia `requirements.txt` | Repetir `pip install -r requirements.txt` |

### Errores comunes

| Error | Causa probable | Solución |
|---|---|---|
| `ModuleNotFoundError` | El entorno no está activo, la terminal no está en la raíz, o se omitió `pip install -e .` | Verifica que veas `(.venv)`, que estés en la raíz, y repite el paso 6 |
| `python` no se reconoce | Python no está instalado o no está en el PATH | Reinstala Python marcando *Add to PATH*; en Windows prueba con `py` |
| Versión de Python anterior a 3.11 | Python desactualizado | Instala una versión más reciente |
| `pip install -e` falla | Falta el punto final o no estás en la raíz | Ejecuta `pip install -e .` desde la raíz |
