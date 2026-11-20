"""Configuracion comun de las pruebas."""

import os

# Las pruebas de interfaz corren sin abrir ventanas.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")