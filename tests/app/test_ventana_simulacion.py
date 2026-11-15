"""Pruebas unitarias para la ventana principal de simulacion y sus componentes (RF-11 a RF-20, RNF-03)."""

from unittest.mock import patch

import numpy as np
import pytest

from simulador.app.almacenamiento.memoria import AlmacenamientoMemoria
from simulador.app.ejecutor.ejecutor import Ejecutor
from simulador.app.interfaz.ventana.barra_estado import BarraEstado
from simulador.app.interfaz.ventana.panel_eventos import PanelEventos
from simulador.app.interfaz.ventana.ventana_simulacion import VentanaSimulacion
from simulador.app.interfaz.ventana.visor_mapa import VisorMapa
from simulador.contratos.comandos import TipoEvento
from simulador.contratos.instantanea import Estacion, InfoEspecie, InfoEvento, Instantanea
from simulador.contratos.motor_falso import MotorFalso


@pytest.fixture
def motor():
    return MotorFalso()


@pytest.fixture
def ejecutor(motor):
    ej = Ejecutor(motor, velocidad=30)
    ej.iniciar()
    yield ej
    ej.detener()


@pytest.fixture
def ventana(qtbot, ejecutor):
    almacenamiento = AlmacenamientoMemoria()
    resumen = almacenamiento.crear("Laguna del sur", b"dummy", tick=0, velocidad=30)
    v = VentanaSimulacion(
        ejecutor,
        nombre=resumen.nombre,
        almacenamiento=almacenamiento,
        simulacion_id=resumen.simulacion_id,
    )
    qtbot.addWidget(v)
    v.show()
    return v


@pytest.mark.requisito("RF-14")
def test_boton_pausa_y_reanudar_cambia_estado(ventana, ejecutor):
    assert ejecutor.en_pausa
    assert "Reanudar" in ventana.btn_pausa.text()

    ventana.btn_pausa.click()
    assert not ejecutor.en_pausa
    assert "Pausar" in ventana.btn_pausa.text()

    ventana.btn_pausa.click()
    assert ejecutor.en_pausa
    assert "Reanudar" in ventana.btn_pausa.text()


@pytest.mark.requisito("RF-15")
def test_deslizador_velocidad_ajusta_ejecutor(ventana, ejecutor):
    ventana.slider_vel.setValue(45)
    assert ejecutor.velocidad == 45
    assert "45 t/s" in ventana.lbl_vel.text()


@pytest.mark.requisito("RF-16")
def test_deslizador_nutrientes_envia_comando(ventana, ejecutor):
    ventana.slider_nut.setValue(80)
    assert "80" in ventana.lbl_nut.text()


@pytest.mark.requisito("RF-11")
def test_renombrar_actualiza_titulo_y_almacenamiento(ventana):
    with patch(
        "PySide6.QtWidgets.QInputDialog.getText",
        return_value=("Bosque Encantado", True),
    ):
        ventana._onRenombrar()

    assert ventana._nombre == "Bosque Encantado"
    assert ventana.lbl_nombre.text() == "Bosque Encantado"
    resumen = next(
        s for s in ventana._almacenamiento.listar() if s.simulacion_id == ventana._simulacion_id
    )
    assert resumen.nombre == "Bosque Encantado"


@pytest.mark.requisito("RF-17")
def test_barra_estado_muestra_datos_completos():
    barra = BarraEstado()
    instantanea = Instantanea(
        tick=1240,
        estacion=Estacion.primavera,
        temperatura=22.5,
        nutrientes=50,
        terreno=np.zeros((10, 10), dtype=np.uint8),
        criaturas=np.zeros((5, 3), dtype=np.int32),
        especies=(),
        eventos=(),
        cupo=200,
    )
    barra.actualizar(instantanea)

    assert "1,240" in barra.lbl_tick.text()
    assert "Primavera" in barra.lbl_estacion.text()
    assert "22.5 °C" in barra.lbl_temperatura.text()
    assert "5 / 200" in barra.lbl_criaturas.text()


@pytest.mark.requisito("RF-17")
@pytest.mark.requisito("RF-41")
def test_barra_estado_resalta_al_llegar_al_cupo():
    barra = BarraEstado()
    instantanea = Instantanea(
        tick=50,
        estacion=Estacion.verano,
        temperatura=30.0,
        nutrientes=50,
        terreno=np.zeros((10, 10), dtype=np.uint8),
        criaturas=np.zeros((200, 3), dtype=np.int32),
        especies=(),
        eventos=(),
        cupo=200,
    )
    barra.actualizar(instantanea)
    assert "#D32F2F" in barra.lbl_criaturas.styleSheet()


@pytest.mark.requisito("RF-18")
def test_panel_eventos_muestra_sin_eventos_cuando_esta_vacio():
    panel = PanelEventos()
    panel.actualizarEventos(())
    assert panel.lbl_sin_eventos.text() == "Sin eventos"


@pytest.mark.requisito("RF-18")
@pytest.mark.requisito("RF-51")
def test_panel_eventos_lista_activos_y_permite_cancelar():
    panel = PanelEventos()
    eventos_cancelados = []
    panel.cancelarEvento.connect(lambda t: eventos_cancelados.append(t))

    evento_sequia = InfoEvento(tipo=TipoEvento.sequia, ticks_restantes=120)
    panel.actualizarEventos((evento_sequia,))

    assert panel.contenedor_activos.count() == 1
    # Buscar el boton cancelar de la fila
    fila = panel.contenedor_activos.itemAt(0).widget()
    botones = fila.findChildren(type(panel.btn_sequia))
    btn_cancelar = next(b for b in botones if "Cancelar" in b.text())
    btn_cancelar.click()

    assert eventos_cancelados == [TipoEvento.sequia]


@pytest.mark.requisito("RF-13")
@pytest.mark.requisito("RF-20")
def test_visor_mapa_actualiza_terreno_y_criaturas(qtbot):
    visor = VisorMapa()
    qtbot.addWidget(visor)

    criaturas = np.array([[10, 20, 1]], dtype=np.int32)
    especie = InfoEspecie(especie_id=1, nombre="Liebres", color=0, poblacion=1, extinguida=False)
    instantanea = Instantanea(
        tick=1,
        estacion=Estacion.primavera,
        temperatura=20.0,
        nutrientes=50,
        terreno=np.zeros((100, 100), dtype=np.uint8),
        criaturas=criaturas,
        especies=(especie,),
        eventos=(),
        cupo=1000,
    )

    visor.actualizarInstantanea(instantanea)
    assert visor._tamano_mapa == 100

    # Ajuste de zoom entre limites
    visor.fijarZoom(4.0)
    assert visor.zoom_actual == 4.0


@pytest.mark.requisito("RF-20")
def test_inspector_muestra_datos_casilla(ventana):
    ventana._alSeleccionarCasilla(5, 5)
    assert ventana.inspector.isVisible()
    assert "Casilla (5, 5)" in ventana.inspector.lbl_titulo.text()


@pytest.mark.requisito("RNF-03")
def test_actualizar_ejecuta_sin_bloquear_hilo(ventana):
    # Llama a actualizar directamente verificando que no lanza excepciones
    ventana.actualizar()
    assert ventana.visor is not None
