"""Bateria de pruebas que debe pasar cualquier implementacion de Almacenamiento."""

import pytest

from simulador.app.almacenamiento.memoria import AlmacenamientoMemoria
from simulador.app.almacenamiento.sqlite import AlmacenamientoSqlite
from simulador.contratos.errores import NombreInvalido, SimulacionNoEncontrada


@pytest.fixture(params=["memoria", "sqlite"])
def almacenamiento(request, tmp_path):
    """Cada implementacion se agrega aqui para pasar las mismas pruebas."""
    if request.param == "memoria":
        yield AlmacenamientoMemoria()
    else:
        sqlite = AlmacenamientoSqlite(tmp_path / "biblioteca.db")
        yield sqlite
        sqlite.cerrar()


@pytest.mark.requisito("RF-49")
def test_lo_guardado_se_carga_identico(almacenamiento):
    resumen = almacenamiento.crear("Isla", b"estado", tick=5, velocidad=10)
    assert almacenamiento.cargar(resumen.simulacion_id) == b"estado"


@pytest.mark.requisito("RF-06")
def test_listar_devuelve_todas_las_simulaciones(almacenamiento):
    almacenamiento.crear("Isla", b"a", tick=0, velocidad=1)
    almacenamiento.crear("Bosque", b"b", tick=0, velocidad=1)
    nombres = [resumen.nombre for resumen in almacenamiento.listar()]
    assert nombres == ["Isla", "Bosque"]


@pytest.mark.requisito("RF-07")
def test_no_se_repite_un_nombre_aunque_cambien_las_mayusculas(almacenamiento):
    almacenamiento.crear("Isla", b"a", tick=0, velocidad=1)
    with pytest.raises(NombreInvalido):
        almacenamiento.crear("ISLA", b"b", tick=0, velocidad=1)


@pytest.mark.requisito("RF-48")
def test_guardar_reemplaza_el_estado_el_tick_y_la_velocidad(almacenamiento):
    resumen = almacenamiento.crear("Isla", b"viejo", tick=0, velocidad=1)
    nuevo = almacenamiento.guardar(resumen.simulacion_id, b"nuevo", tick=1000, velocidad=30)
    assert almacenamiento.cargar(resumen.simulacion_id) == b"nuevo"
    assert nuevo.tick == 1000
    assert nuevo.velocidad == 30


@pytest.mark.requisito("RF-11")
def test_renombrar_cambia_el_nombre(almacenamiento):
    resumen = almacenamiento.crear("Isla", b"a", tick=0, velocidad=1)
    almacenamiento.renombrar(resumen.simulacion_id, "Archipielago")
    assert almacenamiento.listar()[0].nombre == "Archipielago"


@pytest.mark.requisito("RF-11")
def test_renombrar_a_un_nombre_existente_se_rechaza(almacenamiento):
    almacenamiento.crear("Isla", b"a", tick=0, velocidad=1)
    bosque = almacenamiento.crear("Bosque", b"b", tick=0, velocidad=1)
    with pytest.raises(NombreInvalido):
        almacenamiento.renombrar(bosque.simulacion_id, "isla")


@pytest.mark.requisito("RF-12")
def test_eliminar_borra_la_simulacion(almacenamiento):
    resumen = almacenamiento.crear("Isla", b"a", tick=0, velocidad=1)
    almacenamiento.eliminar(resumen.simulacion_id)
    assert almacenamiento.listar() == []
    with pytest.raises(SimulacionNoEncontrada):
        almacenamiento.cargar(resumen.simulacion_id)


@pytest.mark.requisito("RF-10")
def test_cargar_una_simulacion_inexistente_falla(almacenamiento):
    with pytest.raises(SimulacionNoEncontrada):
        almacenamiento.cargar(999)