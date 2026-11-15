import importlib.util
from pathlib import Path

RUTA_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "verificar_trazabilidad.py"

ESPECIFICACION = """# Especificacion

RF-01 a RF-05 se retiraron con las cuentas.

| RF-06 | Crear simulacion | Dada una simulacion... | F1 |
| RF-14 | Pausar y reanudar | Dada una simulacion... | F1 |
| RNF-01 | Plataforma | Corre con Python 3.11. |
"""

PRUEBAS = """import pytest


@pytest.mark.requisito("RF-14")
def test_uno():
    pass


@pytest.mark.requisito("RF-99")
def test_dos():
    pass
"""


def _cargarScript():
    especificacion = importlib.util.spec_from_file_location("verificar_trazabilidad", RUTA_SCRIPT)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


verificador = _cargarScript()


def test_leer_requisitos_solo_toma_filas_de_tabla(tmp_path):
    ruta = tmp_path / "especificacion.md"
    ruta.write_text(ESPECIFICACION, encoding="utf-8")

    assert verificador.leerRequisitos(ruta) == {"RF-06", "RF-14", "RNF-01"}


def test_leer_marcas_devuelve_identificador_y_linea(tmp_path):
    ruta = tmp_path / "test_ejemplo.py"
    ruta.write_text(PRUEBAS, encoding="utf-8")

    assert verificador.leerMarcas(ruta) == [("RF-14", 4), ("RF-99", 9)]


def test_leer_marcas_avisa_cuando_falta_el_identificador(tmp_path):
    ruta = tmp_path / "test_ejemplo.py"
    ruta.write_text("import pytest\n\n\n@pytest.mark.requisito()\ndef test_uno():\n    pass\n")

    assert verificador.leerMarcas(ruta) == [(None, 4)]


def test_revisar_pruebas_reporta_los_requisitos_que_no_existen(tmp_path):
    carpeta = tmp_path / "tests"
    (carpeta / "app").mkdir(parents=True)
    (carpeta / "app" / "test_ejemplo.py").write_text(PRUEBAS, encoding="utf-8")

    errores, cubiertos = verificador.revisarPruebas({"RF-06", "RF-14"}, carpeta)

    assert cubiertos == {"RF-14"}
    assert errores == ["tests/app/test_ejemplo.py:9: RF-99 no existe en la especificacion"]


def test_las_marcas_del_repositorio_son_validas():
    assert verificador.main() == 0