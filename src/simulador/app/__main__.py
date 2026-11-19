"""Compatibilidad: `python -m simulador.app` hace lo mismo que `python -m simulador`."""

import sys

from simulador.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
