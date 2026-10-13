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