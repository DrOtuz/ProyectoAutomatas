import dataclasses
import json

import pytest

from simulador.vida.config import ConfigVida
from simulador.vida.tipos import Dieta


def test_valores_por_defecto_son_los_del_documento():
    cfg = ConfigVida()
    assert cfg.E_MAX == 100
    assert cfg.umbral_reproduccion == 70
    assert cfg.umbral_salida_pareja == 50
    assert cfg.COSTO_REPRODUCCION == 25
    assert cfg.ENERGIA_CRIA == 30
    assert (cfg.A, cfg.C, cfg.K) == (0.30, 0.05, 0.15)
    assert (cfg.T_OPT, cfg.ALFA) == (22, 0.15)
    assert cfg.SIGMA == 0.05
    assert cfg.MAX_CRIATURAS == 1000
    assert cfg.MAX_POR_CASILLA == 1
    # eficiencias y plantillas: valores calibrados por el equipo (no los del v0.1)
    assert cfg.ETA_PLANTA[Dieta.HERBIVORO] == 0.60
    assert cfg.ETA_PLANTA[Dieta.OMNIVORO] == 0.20
    assert cfg.ETA_CARNE[Dieta.CARNIVORO] == 0.70
    assert cfg.ETA_CARNE[Dieta.OMNIVORO] == 0.40
    assert cfg.PLANTILLAS[Dieta.HERBIVORO] == (1.0, 2.0, 7.0)
    assert cfg.PLANTILLAS[Dieta.OMNIVORO] == (1.3, 1.5, 5.0)
    assert cfg.PLANTILLAS[Dieta.CARNIVORO] == (1.6, 1.0, 4.0)
    assert cfg.VEJEZ_ACTIVA is True and cfg.VIDA_BASE == 1500


def test_validar_acepta_los_valores_por_defecto():
    cfg = ConfigVida()
    assert cfg.validar() is cfg


def test_es_inmutable_y_con_crea_copias():
    cfg = ConfigVida()
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.SIGMA = 0.5  # type: ignore[misc]
    otra = cfg.con(SIGMA=0.08)
    assert otra.SIGMA == 0.08 and cfg.SIGMA == 0.05


def test_los_defaults_no_se_comparten_entre_instancias():
    a, b = ConfigVida(), ConfigVida()
    assert a.ETA_PLANTA is not b.ETA_PLANTA


def test_el_umbral_se_expresa_como_porcentaje_de_e_max():
    cfg = ConfigVida(E_MAX=200.0)
    assert cfg.umbral_reproduccion == 140
    assert cfg.umbral_salida_pareja == 100


@pytest.mark.parametrize(
    "cambios",
    [
        {"E_MAX": 0},
        {"UMBRAL_SALIDA_PAREJA_PCT": 0.8},  # salida >= reproduccion
        {"UMBRAL_REPRODUCCION_PCT": 1.5},
        {"COSTO_REPRODUCCION": 0},
        {"COSTO_REPRODUCCION": 80},  # mayor que el umbral
        {"ENERGIA_CRIA": 60},  # crea energia de la nada
        {"ENERGIA_CRIA": 0},
        {"RATIO_DEPREDACION": 0.5},
        {"SIGMA": -0.1},
        {"MAX_CRIATURAS": 0},
        {"MAX_POR_CASILLA": 0},
        {"INERCIA_EXPLORAR": 1.5},
        {"VARIACION_VIDA": 1.0},
        {"FACTOR_BIOMASA": 0},
        {"A": 0, "C": 0, "K": 0},
    ],
)
def test_validar_rechaza_valores_incoherentes(cambios):
    with pytest.raises(ValueError):
        ConfigVida(**cambios).validar()


def test_validar_rechaza_dietas_incoherentes():
    # un herbivoro que "come carne" contradice la dieta
    mala = ConfigVida().ETA_CARNE | {Dieta.HERBIVORO: 0.3}
    with pytest.raises(ValueError, match="ETA_CARNE"):
        ConfigVida(ETA_CARNE=mala).validar()
    # falta una plantilla
    incompleta = {Dieta.HERBIVORO: (1.0, 1.0, 4.0)}
    with pytest.raises(ValueError, match="PLANTILLAS"):
        ConfigVida(PLANTILLAS=incompleta).validar()
    # rasgo no positivo
    con_cero = ConfigVida().PLANTILLAS | {Dieta.OMNIVORO: (1.5, 0.0, 5.0)}
    with pytest.raises(ValueError, match="PLANTILLAS"):
        ConfigVida(PLANTILLAS=con_cero).validar()


def test_validar_lista_todos_los_problemas_juntos():
    with pytest.raises(ValueError) as e:
        ConfigVida(E_MAX=0, SIGMA=-1).validar()
    assert "E_MAX" in str(e.value) and "SIGMA" in str(e.value)


def test_a_dict_desde_dict_son_inversos():
    cfg = ConfigVida().con(SIGMA=0.08, VEJEZ_ACTIVA=False)
    assert ConfigVida.desde_dict(cfg.a_dict()) == cfg


def test_a_dict_es_serializable_como_json():
    texto = json.dumps(ConfigVida().a_dict())
    assert ConfigVida.desde_dict(json.loads(texto)) == ConfigVida()


def test_desde_dict_ignora_claves_desconocidas_y_usa_defaults():
    cfg = ConfigVida.desde_dict({"SIGMA": 0.1, "CLAVE_DE_UNA_VERSION_NUEVA": 7})
    assert cfg.SIGMA == 0.1
    assert cfg.E_MAX == 100


def test_desde_dict_completa_dietas_faltantes_con_los_defaults():
    cfg = ConfigVida.desde_dict({"ETA_PLANTA": {"herbivoro": 0.4}})
    assert cfg.ETA_PLANTA[Dieta.HERBIVORO] == 0.4
    assert cfg.ETA_PLANTA[Dieta.OMNIVORO] == 0.20
    cfg.validar()
