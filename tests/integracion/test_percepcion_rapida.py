"""La percepcion con numpy debe dar exactamente la misma simulacion que la de referencia."""

import pytest

from simulador.contratos import comandos as cmd
from simulador.integracion.mapa_vida import MapaVida
from simulador.integracion.simulador_ecosistema import SimuladorEcosistema


def _correr(rapido: bool, semilla: int, ticks: int, monkeypatch) -> str:
    if not rapido:
        monkeypatch.delattr(MapaVida, "plantas_en_radio")
    m = SimuladorEcosistema(semilla=semilla)
    m.aplicar(cmd.CrearEspecie("h", 80, "herbivoro"))
    m.aplicar(cmd.CrearEspecie("o", 40, "omnivoro"))
    m.aplicar(cmd.CrearEspecie("c", 30, "carnivoro"))
    for _ in range(ticks):
        m.avanzar()
    return m.huellaEstado()


@pytest.mark.parametrize("semilla", [1, 2, 3])
def test_percepcion_rapida_igual_a_la_de_referencia(semilla, monkeypatch):
    with monkeypatch.context() as mp:
        lenta = _correr(False, semilla, 150, mp)
    rapida = _correr(True, semilla, 150, monkeypatch)
    assert rapida == lenta
