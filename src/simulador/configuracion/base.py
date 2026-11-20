"""Cargador y validacion de la configuracion (RNF-06).

Cada seccion es una dataclass congelada. Sus campos se declaran con `campo`, que guarda
el valor por defecto y el rango valido. La validacion es comun a todas las secciones.
"""

from __future__ import annotations

import dataclasses
import typing
from collections.abc import Mapping
from typing import Any, TypeVar

from simulador.contratos.errores import ErrorSimulador

Seccion = TypeVar("Seccion")


class ErrorConfiguracion(ErrorSimulador):
    """La configuracion tiene una clave desconocida o un valor no permitido."""


def campo(
    valor: Any,
    *,
    minimo: float | None = None,
    maximo: float | None = None,
    opciones: tuple[Any, ...] | None = None,
) -> Any:
    """Declara un campo con su valor por defecto y lo que se permite."""
    reglas = {"minimo": minimo, "maximo": maximo, "opciones": opciones}
    return dataclasses.field(default=valor, metadata=reglas)


def construirSeccion(clase: type[Seccion], datos: Mapping[str, Any]) -> Seccion:
    """Crea una seccion con los datos de un archivo; rechaza claves desconocidas."""
    conocidas = {c.name for c in dataclasses.fields(clase)}  # type: ignore[arg-type]
    desconocidas = sorted(set(datos) - conocidas)
    if desconocidas:
        raise ErrorConfiguracion(
            f"{clase.__name__}: clave desconocida: {', '.join(desconocidas)}"
        )
    return clase(**datos)


def validarSeccion(seccion: object) -> None:
    """Comprueba tipo, rango y opciones de cada campo. Se llama desde `__post_init__`."""
    clase = type(seccion)
    tipos = typing.get_type_hints(clase)
    for definicion in dataclasses.fields(seccion):  # type: ignore[arg-type]
        valor = getattr(seccion, definicion.name)
        ruta = f"{clase.__name__}.{definicion.name}"
        _validarCampo(ruta, valor, tipos[definicion.name], definicion.metadata)


def _tipoCorrecto(valor: Any, tipo: type) -> bool:
    if isinstance(valor, bool):
        return tipo is bool
    if tipo is float:
        return isinstance(valor, int | float)
    return isinstance(valor, tipo)


def _validarCampo(ruta: str, valor: Any, tipo: type, reglas: Mapping[str, Any]) -> None:
    if not _tipoCorrecto(valor, tipo):
        raise ErrorConfiguracion(f"{ruta}: debe ser de tipo {tipo.__name__} (recibido {valor!r})")
    minimo = reglas.get("minimo")
    maximo = reglas.get("maximo")
    opciones = reglas.get("opciones")
    if minimo is not None and valor < minimo:
        raise ErrorConfiguracion(f"{ruta}: debe ser al menos {minimo} (recibido {valor!r})")
    if maximo is not None and valor > maximo:
        raise ErrorConfiguracion(f"{ruta}: debe ser como maximo {maximo} (recibido {valor!r})")
    if opciones is not None and valor not in opciones:
        raise ErrorConfiguracion(f"{ruta}: debe ser una de {list(opciones)} (recibido {valor!r})")