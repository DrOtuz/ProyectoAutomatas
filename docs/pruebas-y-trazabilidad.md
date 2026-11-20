# Pruebas y trazabilidad

Cómo se prueba el proyecto y cómo se vincula cada prueba con un requisito de [`especificacion.md`](especificacion.md).

## Ejecutar las pruebas

```bash
pip install -e ".[dev]"     # o: pip install -r requirements-dev.txt
pytest                      # toda la suite
pytest tests/vida           # solo un grupo
ruff check .                # estilo
lint-imports                # el motor no importa la aplicación
python scripts/verificar_trazabilidad.py
```

Las pruebas de interfaz usan `pytest-qt` y corren sin mostrar ventanas. Sin instalar el paquete (`pip install -e .`), `pytest` falla con `ModuleNotFoundError: No module named 'simulador'`.

## Qué se prueba y dónde

| Carpeta | Qué cubre |
| --- | --- |
| `tests/ecosistema/` | Mapa, reloj y clima, eventos naturales y autómata del fuego. |
| `tests/vida/` | Autómata de la criatura, estadísticas, mutación, especies, población, percepción e historial. Usa un mapa falso (`mapa_falso`). |
| `tests/integracion/` | `SimuladorEcosistema` completo: determinismo, comandos, estado guardado, percepción rápida frente a la lenta y registro de series. |
| `tests/app/` | Contratos, configuración, ejecutor, almacenamiento SQLite, ventanas (menú, editor, simulación, especies), motor falso y la propia trazabilidad. |

Tipos de prueba usados: unitarias de funciones puras, propiedades (cupo, casilla única, rangos), escenarios completos con semilla fija y de humo para la interfaz.

## Trazabilidad requisito ↔ prueba

Cada prueba que verifica un requisito lo declara con una marca:

```python
import pytest

@pytest.mark.requisito("RF-25")
def test_agua_no_cambia():
    ...
```

- Las marcas se validan con `python scripts/verificar_trazabilidad.py`, que termina con error si una marca no apunta a una fila de las tablas de `especificacion.md`.
- Los requisitos retirados solo aparecen en texto, no en tabla, y por eso no admiten marcas.
- No todos los requisitos tienen aún una prueba marcada: el script informa cuántos están cubiertos. Cuando agregues una prueba, márcala.
- La marca está registrada en `pyproject.toml` (`--strict-markers`): una marca con otro nombre falla.

## Cómo agregar una prueba

1. Elige el requisito en `especificacion.md` (o agrégalo, con un ID nuevo, si el comportamiento es nuevo).
2. Escribe la prueba en la carpeta de tu grupo, con la marca `requisito`.
3. Usa semillas fijas: el motor es determinista.
4. Corre `pytest`, `ruff check .`, `lint-imports` y el script de trazabilidad antes de abrir el Pull Request.

## Integración continua

`.github/workflows/integracion_continua.yml` corre en Windows (Python 3.11) la instalación de `requirements-dev.txt`, `ruff check`, `lint-imports`, `pytest` y el script de trazabilidad. Cada Pull Request debe pasarla antes de pedir revisión. Las normas de commits y ramas están en [`guia-de-calidad.md`](guia-de-calidad.md).
