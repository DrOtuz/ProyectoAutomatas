# Guía de Calidad Técnica — ProyectoAutomatas

Esta guía recopila los estándares de diseño, arquitectura, pruebas y flujo de trabajo acordados para el desarrollo de `ProyectoAutomatas`. Aplica a los tres subgrupos (**Ecosistema**, **Vida** y **App**).

---

## 1. Reglas de nomenclatura y redacción

Definidas en `docs/contratos.md`:
* **Idioma:** Español neutro, sin tildes ni eñes en identificadores de código (en comentarios y documentación sí se admiten).
* **Clases y tipos:** `PascalCase` (ej. `MotorFalso`, `ResumenSimulacion`, `ConfiguracionApp`).
* **Funciones y métodos:** `camelCase` (ej. `obtenerInstantanea`, `validarNombre`, `crearEspecie`).
* **Variables, atributos y módulos:** `snake_case` (ej. `tick_actual`, `largo_maximo`, `sqlite.py`).
* **Constantes:** `UPPER_SNAKE_CASE` (ej. `VERSION_ESQUEMA`).
* **Miembros de Enum:** En minúscula (ej. `TipoEvento.sequia`, `OrigenEvento.natural`).
* **Pruebas:** Los archivos y funciones de prueba deben conservar el prefijo `test_` (ej. `test_crear_simulacion`).

---

## 2. Cero números mágicos (RNF-06)

* Ningún límite numérico, dimensión, tiempo, probabilidad o umbral debe escribirse a mano directamente en el código de simulación ni en la interfaz.
* Todos los valores parametrizables deben definirse en el paquete `simulador.configuracion` (`por_defecto.toml`, `app.py`, `ecosistema.py` o `vida.py`) y ser consumidos por los constructores correspondientes.

---

## 3. Arquitectura e importaciones limpias

* **Regla de oro:** *El motor no importa la aplicación*.
  - `simulador.ecosistema` y `simulador.vida` **jamás** deben importar nada de `simulador.app`, `PySide6` ni `pyqtgraph`.
* **Contratos puros:**
  - `simulador.contratos` define las interfaces y estructuras de datos comunes que cruzan fronteras. No debe depender de `simulador.configuracion` ni de `simulador.app`.
* **Verificación estricta:** Antes de subir cualquier cambio, se valida con:
  ```bash
  lint-imports
  ```
  El resultado debe ser: `Contracts: 1 kept, 0 broken.`

---

## 4. Contratos entre subgrupos (`docs/contratos.md`)

* **Solo lo que cruza fronteras:** Los detalles de implementación internos de cada subgrupo viven en su propio paquete y no se documentan en `contratos.md`.
* **Plantilla obligatoria:** Toda función o atributo público en `contratos.md` debe seguir la estructura estándar (`### Clase.metodo`, `Firma:`, `Descripción:`, `Parámetros:`, `Retorno:`, `Errores:`).
* **Orden alfabético:** Las clases se ordenan alfabéticamente dentro de cada sección, con los atributos primero y luego los métodos.
* **Cambios de contrato:** Cualquier modificación a una firma o comportamiento de contrato requiere una discusión previa (o RFC) y aprobación de los líderes de subgrupo.

---

## 5. Manejo de excepciones

* Todas las excepciones específicas del dominio deben heredar de `simulador.contratos.errores.ErrorSimulador`.
* Los errores deben lanzar mensajes claros y explicativos para el usuario o desarrollador, evitando fallos silenciosos o excepciones genéricas no controladas.

---

## 6. Pruebas y trazabilidad (`pytest`)

* **Trazabilidad 1 a 1:** Cada prueba unitaria o de integración debe vincularse explícitamente a un requisito de `docs/especificacion.md` mediante el decorador:
  ```python
  @pytest.mark.requisito("RF-xx")  # o "RNF-xx"
  ```
* **Cálculo exacto:** El total de pruebas debe ser calculado matemáticamente y verificado tras cada cambio (nunca estimado).
* **Ejecución limpia:** Todas las pruebas deben pasar en verde sin advertencias no controladas:
  ```bash
  pytest
  ```

---

## 7. Flujo de Git y calidad de commits

* **Ramas limpias:** Las ramas de trabajo (`feature/<subgrupo>-<tarea>`) se crean **siempre desde `develop` actualizado**.
* **Protección de ramas:** `main` y `develop` están protegidas; toda integración se realiza mediante Pull Request aprobado con **«Create a merge commit»**.
* **Commits atómicos:** Los cambios deben agruparse en commits pequeños con mensajes en formato convencional:
  ```text
  tipo(subgrupo): descripción breve en infinitivo (A-nn)
  ```
  *(ej. `feat(app): agregar script de trazabilidad (A-15)` o `fix(app): corregir limite en ejecutor (A-9b)`).*
* **Archivos específicos:** **Nunca usar `git add .`**. Agregar siempre los archivos modificados por nombre explícito.
* **Sin atribuciones externas:** No incluir firmas automáticas ni líneas de atribución (`Co-Authored-By`, `Claude-Session`, etc.) en mensajes de commit ni en la descripción de Pull Requests.
* **Comprobación previa al push:**
  ```powershell
  ruff check .
  pytest
  lint-imports
  ```
