# Proyecto unificado (A + B + C)

Ejecutar la app (Windows, con PySide6, pyqtgraph y numpy instalados):
    python -m simulador.app

Pruebas (sin ventanas):  python -m pytest tests --ignore=tests/app/test_especies_interfaz.py --ignore=tests/app/test_flujo_inicio.py --ignore=tests/app/test_ventana_simulacion.py
(pytest.ini ya pone pythonpath = src .)

Sin probar (no habia PySide6): app/aplicacion.py (ventanas, incluido el editor de mapa conectado), formulario crear_especie, detalle_especie
y sus pruebas en tests/app. Probar en Windows.
