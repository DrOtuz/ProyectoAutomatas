"""Pruebas de los errores del contrato."""

import pytest

from simulador.contratos.errores import ComandoInvalido, ComandoNoSoportado, ErrorSimulador


@pytest.mark.requisito("RNF-12")
@pytest.mark.parametrize("clase_error", [ComandoInvalido, ComandoNoSoportado])
def test_los_errores_de_comando_son_errores_del_simulador(clase_error):
    with pytest.raises(ErrorSimulador):
        raise clase_error("mensaje")


@pytest.mark.requisito("RNF-12")
def test_el_mensaje_del_error_se_conserva():
    error = ComandoInvalido("nutrientes fuera de rango")
    assert str(error) == "nutrientes fuera de rango"