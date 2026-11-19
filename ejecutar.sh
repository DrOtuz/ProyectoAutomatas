#!/usr/bin/env sh
# Abre el simulador. La primera vez crea el entorno e instala lo necesario (necesita internet).
cd "$(dirname "$0")" || exit 1

PY=""
for candidato in python3 python; do
    if command -v "$candidato" >/dev/null 2>&1; then PY="$candidato"; break; fi
done
if [ -z "$PY" ]; then
    echo "No se encontró Python. Instala Python 3.11 o superior desde https://www.python.org/downloads/" >&2
    exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
    echo "Creando el entorno virtual..."
    "$PY" -m venv .venv || { echo "No se pudo crear el entorno virtual (¿Python 3.11 o superior?)." >&2; exit 1; }
fi

echo "Comprobando dependencias..."
.venv/bin/python -m pip install --quiet -e . || {
    echo "No se pudieron instalar las dependencias. Revisa tu conexión a internet y que Python sea 3.11 o superior." >&2
    exit 1
}

exec .venv/bin/python -m simulador
