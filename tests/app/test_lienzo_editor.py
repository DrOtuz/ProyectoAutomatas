"""Pruebas para el widget interactivo del editor de mapa (P-04, RF-08, RF-09)."""

import numpy as np
import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent

from simulador.app.editor.editor_mapa import HerramientaEditor
from simulador.app.interfaz.editor_mapa_widget import EditorMapaWidget
from simulador.contratos.instantanea import EstadoCasilla


@pytest.fixture
def widget_editor(qtbot):
    widget = EditorMapaWidget()
    qtbot.addWidget(widget)
    return widget


@pytest.mark.requisito("RF-08")
def test_lienzo_pinta_agua_al_hacer_click(widget_editor):
    lienzo = widget_editor.lienzo
    pos = QPointF(12.0, 12.0)  # Casilla (2, 2)
    evento_press = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        pos,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    lienzo.mousePressEvent(evento_press)

    terreno = widget_editor.editor.obtenerTerreno()
    assert terreno[2, 2] == EstadoCasilla.agua


@pytest.mark.requisito("RF-08")
def test_cambio_herramientas_y_tamano(widget_editor):
    widget_editor.btn_borrador.click()
    assert widget_editor.editor.herramienta == HerramientaEditor.borrador

    widget_editor.btn_rectangulo.click()
    assert widget_editor.editor.herramienta == HerramientaEditor.rectangulo

    widget_editor.slider.setValue(3)
    assert widget_editor.editor.tamano_pincel == 3
    assert "Tamaño: 3" in widget_editor.etiqueta_tamano.text()


@pytest.mark.requisito("RF-08")
def test_deshacer_rehacer_y_limpiar(widget_editor):
    widget_editor.editor.fijarHerramienta(HerramientaEditor.pincel_agua)
    widget_editor.editor.iniciarTrazo()
    widget_editor.editor.agregarPunto(5, 5)
    widget_editor.editor.finalizarTrazo()

    assert widget_editor.editor.tiene_agua

    widget_editor.btn_deshacer.click()
    assert not widget_editor.editor.tiene_agua

    widget_editor.btn_rehacer.click()
    assert widget_editor.editor.tiene_agua

    widget_editor.btn_limpiar.click()
    assert not widget_editor.editor.tiene_agua


@pytest.mark.requisito("RF-09")
def test_confirmar_mapa_emite_senal_si_tiene_agua(widget_editor, qtbot):
    widget_editor.editor.fijarHerramienta(HerramientaEditor.pincel_agua)
    widget_editor.editor.iniciarTrazo()
    widget_editor.editor.agregarPunto(10, 10)
    widget_editor.editor.finalizarTrazo()

    with qtbot.waitSignal(widget_editor.mapaConfirmado, timeout=1000) as bloqueador:
        widget_editor.btn_confirmar.click()

    terreno = bloqueador.args[0]
    assert isinstance(terreno, np.ndarray)
    assert terreno.shape == (100, 100)
    assert terreno[10, 10] == EstadoCasilla.agua
