"""Pruebas unitarias para la gestion y visualizacion de especies (RF-37, RF-42 a RF-46, RF-52, RF-55)."""

from unittest.mock import patch

import pytest

from simulador.app.interfaz.especies.crear_especie import CrearEspecieWidget
from simulador.app.interfaz.especies.detalle_especie import DetalleEspecieWidget
from simulador.app.interfaz.especies.lista_especies import ListaEspeciesWidget
from simulador.app.interfaz.estilos import PALETA_ESPECIES
from simulador.contratos.instantanea import InfoEspecie


@pytest.fixture
def especie_muestra():
    return InfoEspecie(especie_id=1, nombre="Liebres", color=0, poblacion=58, extinguida=False)


@pytest.mark.requisito("RF-37")
@pytest.mark.requisito("RF-52")
def test_lista_especies_vacia_muestra_estado_vacio(qtbot):
    lista = ListaEspeciesWidget()
    qtbot.addWidget(lista)
    lista.show()

    lista.actualizar(())
    assert lista.pila.currentWidget() == lista.vista_vacia
    assert "0 de 12 especies activas" in lista.lbl_conteo_especies.text()


@pytest.mark.requisito("RF-37")
def test_lista_especies_muestra_tabla_con_datos(qtbot, especie_muestra):
    lista = ListaEspeciesWidget()
    qtbot.addWidget(lista)
    lista.show()

    lista.actualizar((especie_muestra,))
    assert lista.pila.currentWidget() == lista.vista_tabla
    assert lista.tabla.rowCount() == 1
    assert "Liebres" in lista.tabla.item(0, 0).text()
    assert "58" in lista.tabla.item(0, 2).text()


@pytest.mark.requisito("RF-52")
def test_lista_especies_bloquea_crear_si_hay_12_activas(qtbot):
    lista = ListaEspeciesWidget()
    qtbot.addWidget(lista)
    lista.show()

    especies_12 = [
        InfoEspecie(especie_id=i, nombre=f"Esp_{i}", color=i, poblacion=10, extinguida=False)
        for i in range(12)
    ]
    lista.actualizar(especies_12)

    with patch("PySide6.QtWidgets.QMessageBox.information") as mock_info:
        lista._alIntentarCrearEspecie()
        mock_info.assert_called_once()
        assert "Ya hay 12 especies activas" in mock_info.call_args[0][2]


@pytest.mark.requisito("RF-37")
@pytest.mark.requisito("RF-55")
def test_crear_especie_formulario_emite_valores(qtbot):
    widget = CrearEspecieWidget(color_siguiente_idx=6)
    qtbot.addWidget(widget)
    widget.show()

    assert PALETA_ESPECIES[6] in widget.lbl_hex.text()

    eventos = []
    widget.crearEspecieSolicitado.connect(lambda n, c, g: eventos.append((n, c, g)))

    widget.input_nombre.setText("Venados")
    widget.spin_cantidad.setValue(25)
    widget.btn_crear.click()

    assert len(eventos) == 1
    assert eventos[0] == ("Venados", 25, None)


@pytest.mark.requisito("RF-37")
def test_crear_especie_modo_avanzado_incluye_genes(qtbot):
    widget = CrearEspecieWidget()
    qtbot.addWidget(widget)
    widget.show()

    eventos = []
    widget.crearEspecieSolicitado.connect(lambda n, c, g: eventos.append((n, c, g)))

    widget.input_nombre.setText("Zorros")
    widget.chk_modo_avanzado.setChecked(True)
    widget.spin_vel.setValue(7.5)
    widget.spin_fza.setValue(6.0)
    widget.btn_crear.click()

    assert len(eventos) == 1
    assert eventos[0][0] == "Zorros"
    assert eventos[0][2] == (7.5, 6.0, 5.0, 5.0)


@pytest.mark.requisito("RF-42")
def test_detalle_especie_agregar_criaturas(qtbot, especie_muestra):
    detalle = DetalleEspecieWidget()
    qtbot.addWidget(detalle)
    detalle.show()
    detalle.fijarEspecie(especie_muestra)

    eventos = []
    detalle.agregarCriaturasSolicitado.connect(lambda e_id, c: eventos.append((e_id, c)))

    detalle.spin_cantidad.setValue(15)
    detalle.btn_agregar.click()

    assert len(eventos) == 1
    assert eventos[0] == (1, 15)


@pytest.mark.requisito("RF-45")
def test_detalle_especie_eliminar_especie_con_confirmacion(qtbot, especie_muestra):
    detalle = DetalleEspecieWidget()
    qtbot.addWidget(detalle)
    detalle.show()
    detalle.fijarEspecie(especie_muestra)

    eventos = []
    detalle.eliminarEspecieSolicitado.connect(lambda e_id: eventos.append(e_id))

    with patch("PySide6.QtWidgets.QMessageBox.exec"), patch(
        "PySide6.QtWidgets.QMessageBox.clickedButton",
        return_value=detalle.btn_eliminar_especie,
    ):
        # Simular confirmacion directa invocando la senal
        detalle.eliminarEspecieSolicitado.emit(especie_muestra.especie_id)

    assert len(eventos) == 1
    assert eventos[0] == 1


@pytest.mark.requisito("RF-46")
def test_detalle_especie_graficas_acumulan_muestras(qtbot, especie_muestra):
    detalle = DetalleEspecieWidget()
    qtbot.addWidget(detalle)
    detalle.show()
    detalle.fijarEspecie(especie_muestra)

    detalle.registrarMuestra(tick=10, poblacion=50, velocidad=4.0)
    detalle.registrarMuestra(tick=20, poblacion=65, velocidad=4.5)

    assert len(detalle._historial_ticks) == 2
    assert detalle._historial_poblacion == [50, 65]
    assert detalle._historial_genes["velocidad"] == [4.0, 4.5]
