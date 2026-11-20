"""Punto de entrada del simulador: `python -m simulador` (o el comando `simulador`)."""

from __future__ import annotations

import sys

MENSAJE_FALTAN_DEPENDENCIAS = (
    "Faltan dependencias del simulador ({faltante}).\n"
    "Instálalas desde la carpeta del proyecto con:\n"
    "    python -m pip install -e .\n"
    "o ejecuta ejecutar.bat (Windows) / ejecutar.sh (Mac y Linux), que lo hacen por ti."
)


def main(argv: list[str] | None = None) -> int:
    """Abre la aplicación. Devuelve el código de salida del proceso."""
    try:
        import pyqtgraph  # noqa: F401
        import PySide6  # noqa: F401
    except ImportError as error:
        print(MENSAJE_FALTAN_DEPENDENCIAS.format(faltante=error.name), file=sys.stderr)
        return 1

    from simulador.app.aplicacion import ejecutar

    return ejecutar(argv)


if __name__ == "__main__":
    sys.exit(main())
