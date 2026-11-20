"""Prueba de humo: los tres paquetes del proyecto se pueden importar."""

import importlib

import pytest


@pytest.mark.requisito("RNF-01")
def test_se_importan_los_tres_paquetes():
    for nombre in ("simulador.app", "simulador.ecosistema", "simulador.vida"):
        importlib.import_module(nombre)