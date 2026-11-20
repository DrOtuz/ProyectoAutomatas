from dataclasses import dataclass

import pytest

from simulador.configuracion.base import (
    ErrorConfiguracion,
    campo,
    construirSeccion,
    validarSeccion,
)
from simulador.contratos.errores import ErrorSimulador


@dataclass(frozen=True)
class SeccionPrueba:
    cantidad: int = campo(10, minimo=1, maximo=100)
    factor: float = campo(0.5, minimo=0.0, maximo=1.0)
    figura: str = campo("circulo", opciones=("circulo", "cuadrado"))

    def __post_init__(self):
        validarSeccion(self)


@pytest.mark.requisito("RNF-06")
def test_los_valores_por_defecto_son_validos():
    seccion = SeccionPrueba()
    assert seccion.cantidad == 10
    assert seccion.figura == "circulo"


@pytest.mark.requisito("RNF-06")
def test_acepta_los_limites_del_rango():
    assert SeccionPrueba(cantidad=1).cantidad == 1
    assert SeccionPrueba(cantidad=100).cantidad == 100


@pytest.mark.requisito("RNF-06")
@pytest.mark.parametrize("cantidad", [0, 101, -5])
def test_rechaza_valores_fuera_de_rango(cantidad):
    with pytest.raises(ErrorConfiguracion, match="cantidad"):
        SeccionPrueba(cantidad=cantidad)


@pytest.mark.requisito("RNF-06")
def test_rechaza_tipo_incorrecto():
    with pytest.raises(ErrorConfiguracion, match="tipo int"):
        SeccionPrueba(cantidad="diez")


@pytest.mark.requisito("RNF-06")
def test_un_booleano_no_cuenta_como_entero():
    with pytest.raises(ErrorConfiguracion):
        SeccionPrueba(cantidad=True)


@pytest.mark.requisito("RNF-06")
def test_un_entero_vale_como_decimal():
    assert SeccionPrueba(factor=1).factor == 1


@pytest.mark.requisito("RNF-06")
def test_rechaza_una_opcion_no_permitida():
    with pytest.raises(ErrorConfiguracion, match="figura"):
        SeccionPrueba(figura="estrella")


@pytest.mark.requisito("RNF-06")
def test_construirSeccion_usa_los_datos_y_completa_con_los_por_defecto():
    seccion = construirSeccion(SeccionPrueba, {"cantidad": 7})
    assert seccion.cantidad == 7
    assert seccion.figura == "circulo"


@pytest.mark.requisito("RNF-06")
def test_construirSeccion_rechaza_claves_desconocidas():
    with pytest.raises(ErrorConfiguracion, match="cantidd"):
        construirSeccion(SeccionPrueba, {"cantidd": 7})


@pytest.mark.requisito("RNF-06")
def test_el_error_es_un_error_del_simulador():
    assert issubclass(ErrorConfiguracion, ErrorSimulador)