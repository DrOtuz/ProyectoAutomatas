"""Pruebas del flujo de navegacion inicial: menu, creacion y carga (RF-06, RF-07, RF-10, RF-12)."""

from unittest.mock import patch

import pytest

from simulador.app.almacenamiento.memoria import AlmacenamientoMemoria
from simulador.app.interfaz.pantallas.cargar import CargarSimulacionWidget
from simulador.app.interfaz.pantallas.menu_principal import MenuPrincipalWidget
from simulador.app.interfaz.pantallas.nueva_simulacion import NuevaSimulacionWidget
from simulador.app.interfaz.ventana_inicio import VentanaInicio


@pytest.fixture
def almacenamiento():
    return AlmacenamientoMemoria()


@pytest.fixture
def ventana(qtbot, almacenamiento):
    v = VentanaInicio(almacenamiento)
    qtbot.addWidget(v)
    v.show()
    return v


@pytest.mark.requisito("RF-06")
def test_ventana_inicio_arranca_en_el_menu_principal(ventana):
    assert isinstance(ventana.pantalla_actual, MenuPrincipalWidget)


@pytest.mark.requisito("RF-06")
def test_menu_principal_navega_a_nueva_simulacion(ventana):
    ventana._menu.btn_crear.click()
    assert isinstance(ventana.pantalla_actual, NuevaSimulacionWidget)


@pytest.mark.requisito("RF-06")
def test_menu_principal_navega_a_cargar_simulacion(ventana):
    ventana._menu.btn_cargar.click()
    assert isinstance(ventana.pantalla_actual, CargarSimulacionWidget)


@pytest.mark.requisito("RF-06")
def test_cargar_simulacion_vacia_muestra_estado_vacio(ventana):
    ventana._menu.btn_cargar.click()
    cargar = ventana.pantalla_actual
    assert isinstance(cargar, CargarSimulacionWidget)
    assert cargar.pila_contenido.currentWidget() == cargar.vista_vacia
    assert not cargar.btn_abrir.isEnabled()

    # Clic en el boton de crear del estado vacio lleva a nueva simulacion
    cargar.btn_crear_vacio.click()
    assert isinstance(ventana.pantalla_actual, NuevaSimulacionWidget)


@pytest.mark.requisito("RF-07")
def test_nueva_simulacion_boton_cancelar_vuelve_al_menu(ventana):
    ventana.mostrarNuevaSimulacion()
    ventana._nueva.btn_cancelar.click()
    assert isinstance(ventana.pantalla_actual, MenuPrincipalWidget)


@pytest.mark.requisito("RF-07")
def test_nueva_simulacion_valida_nombre_invalido(ventana):
    ventana.mostrarNuevaSimulacion()
    # Nombre con espacios en extremos
    ventana._nueva.input_nombre.setText("  Mundo Invalido  ")
    ventana._nueva.btn_continuar.click()

    assert ventana._nueva.lbl_error_nombre.isVisible()
    assert "no puede empezar ni terminar con espacios" in ventana._nueva.lbl_error_nombre.text()


@pytest.mark.requisito("RF-07")
def test_nueva_simulacion_rechaza_nombre_repetido(almacenamiento, ventana):
    almacenamiento.crear("Laguna del sur", b"dummy", tick=0, velocidad=10)

    ventana.mostrarNuevaSimulacion()
    ventana._nueva.input_nombre.setText("laguna DEL SUR")
    ventana._nueva.btn_continuar.click()

    assert ventana._nueva.lbl_error_nombre.isVisible()
    assert "Ya existe una simulación con ese nombre." in ventana._nueva.lbl_error_nombre.text()


@pytest.mark.requisito("RF-07")
def test_nueva_simulacion_nombre_valido_emite_senales(ventana):
    eventos = []
    ventana.iniciarEditor.connect(lambda n, s: eventos.append((n, s)))

    ventana.mostrarNuevaSimulacion()
    ventana._nueva.input_nombre.setText("Bosque Nuevo")
    ventana._nueva.input_semilla.setText("2026")
    ventana._nueva.btn_continuar.click()

    assert len(eventos) == 1
    assert eventos[0] == ("Bosque Nuevo", 2026)


@pytest.mark.requisito("RF-10")
def test_cargar_simulacion_muestra_registros_guardados(almacenamiento, ventana):
    sim1 = almacenamiento.crear("Mundo Alpha", b"dummy1", tick=120, velocidad=15)
    sim2 = almacenamiento.crear("Mundo Beta", b"dummy2", tick=500, velocidad=30)

    ventana.mostrarCargarSimulacion()
    cargar = ventana.pantalla_actual
    assert cargar.pila_contenido.currentWidget() == cargar.vista_tabla
    assert cargar.tabla.rowCount() == 2
    assert cargar.tabla.item(0, 0).text() == sim1.nombre
    assert cargar.tabla.item(1, 0).text() == sim2.nombre


@pytest.mark.requisito("RF-10")
def test_cargar_simulacion_al_seleccionar_habilita_y_emite(almacenamiento, ventana):
    sim = almacenamiento.crear("Mundo Alpha", b"dummy", tick=120, velocidad=15)
    eventos = []
    ventana.cargarSimulacion.connect(lambda sim_id: eventos.append(sim_id))

    ventana.mostrarCargarSimulacion()
    cargar = ventana.pantalla_actual
    assert not cargar.btn_abrir.isEnabled()

    cargar.tabla.selectRow(0)
    assert cargar.btn_abrir.isEnabled()

    cargar.btn_abrir.click()
    assert len(eventos) == 1
    assert eventos[0] == sim.simulacion_id


@pytest.mark.requisito("RF-12")
def test_eliminar_simulacion_con_confirmacion(almacenamiento, ventana):
    sim = almacenamiento.crear("Para Borrar", b"dummy", tick=10, velocidad=10)
    ventana.mostrarCargarSimulacion()
    cargar = ventana.pantalla_actual
    assert cargar.tabla.rowCount() == 1

    # Simular que el usuario acepta el dialogo de confirmacion
    with patch(
        "simulador.app.interfaz.pantallas.cargar.confirmarEliminarSimulacion",
        return_value=True,
    ):
        cargar._confirmarYEliminar(sim)

    # El registro se elimino de almacenamiento y la tabla paso al estado vacio
    assert len(almacenamiento.listar()) == 0
    assert cargar.pila_contenido.currentWidget() == cargar.vista_vacia
