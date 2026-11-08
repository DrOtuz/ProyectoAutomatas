"""Comprueba que cada marca de requisito de las pruebas apunte a un requisito real.

Uso: python scripts/verificar_trazabilidad.py
Termina con codigo 0 si todas las marcas son validas y con 1 si alguna no lo es.
"""

import ast
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ESPECIFICACION = RAIZ / "docs" / "especificacion.md"
CARPETA_PRUEBAS = RAIZ / "tests"
PATRON_REQUISITO = re.compile(r"^\|\s*((?:RF|RNF)-\d+)\s*\|", re.MULTILINE)


def leerRequisitos(ruta: Path) -> set[str]:
    """Devuelve los identificadores que abren una fila de tabla de la especificacion.

    Los identificadores que solo aparecen en texto corrido (por ejemplo los requisitos
    retirados) no cuentan.
    """
    texto = ruta.read_text(encoding="utf-8")
    return set(PATRON_REQUISITO.findall(texto))


def _esMarcaRequisito(llamada: ast.Call) -> bool:
    funcion = llamada.func
    return (
        isinstance(funcion, ast.Attribute)
        and funcion.attr == "requisito"
        and isinstance(funcion.value, ast.Attribute)
        and funcion.value.attr == "mark"
    )


def leerMarcas(ruta: Path) -> list[tuple[str | None, int]]:
    """Devuelve (identificador, linea) de cada marca requisito de un archivo de pruebas.

    El identificador es None cuando la marca no trae un texto entre comillas.
    """
    arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
    marcas: list[tuple[str | None, int]] = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call) or not _esMarcaRequisito(nodo):
            continue
        primero = nodo.args[0] if nodo.args else None
        if isinstance(primero, ast.Constant) and isinstance(primero.value, str):
            marcas.append((primero.value, nodo.lineno))
        else:
            marcas.append((None, nodo.lineno))
    return sorted(marcas, key=lambda marca: marca[1])


def revisarPruebas(requisitos: set[str], carpeta: Path) -> tuple[list[str], set[str]]:
    """Revisa todas las marcas de la carpeta de pruebas.

    Devuelve los mensajes de error y los requisitos que tienen alguna prueba marcada.
    """
    errores: list[str] = []
    cubiertos: set[str] = set()
    for ruta in sorted(carpeta.rglob("test_*.py")):
        nombre = f"{carpeta.name}/{ruta.relative_to(carpeta).as_posix()}"
        for requisito, linea in leerMarcas(ruta):
            lugar = f"{nombre}:{linea}"
            if requisito is None:
                errores.append(f"{lugar}: la marca requisito necesita un identificador")
            elif requisito not in requisitos:
                errores.append(f"{lugar}: {requisito} no existe en la especificacion")
            else:
                cubiertos.add(requisito)
    return errores, cubiertos


def main() -> int:
    requisitos = leerRequisitos(ESPECIFICACION)
    if not requisitos:
        print("No se encontro ningun requisito en docs/especificacion.md")
        return 1
    errores, cubiertos = revisarPruebas(requisitos, CARPETA_PRUEBAS)
    for error in errores:
        print(error)
    print(f"Requisitos con alguna prueba marcada: {len(cubiertos)} de {len(requisitos)}")
    if errores:
        print(f"Marcas no validas: {len(errores)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())