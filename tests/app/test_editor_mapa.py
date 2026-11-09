"""Pruebas unitarias para la logica del editor de mapa (RF-08, RF-09)."""

import numpy as np
import pytest

from simulador.app.editor.editor_mapa import EditorMapa, HerramientaEditor
from simulador.configuracion.app import ConfiguracionApp
from simulador.contratos.instantanea import EstadoCasilla


@pytest.mark.requisito("RF-08")
def test_mapa_inicial_todo_tierra_con_dimension_por_defecto():
    editor = EditorMapa()
    assert editor.tamano == 100
    terreno = editor.obtenerTerreno()
    assert terreno.shape == (100, 100)
    assert np.all(terreno == int(EstadoCasilla.tierra))
    assert editor.casillas_agua == 0
    assert editor.porcentaje_agua == 0.0
    assert not editor.tiene_agua
    assert not editor.puede_deshacer
    assert not editor.puede_rehacer


@pytest.mark.requisito("RF-08")
def test_tamano_invalido_lanza_error():
    with pytest.raises(ValueError):
        EditorMapa(tamano=0)
    with pytest.raises(ValueError):
        EditorMapa(tamano=-10)


@pytest.mark.requisito("RF-08")
def test_pincel_de_agua_pinta_casilla_y_permite_deshacer():
    editor = EditorMapa()
    editor.pintarCasilla(10, 20)
    terreno = editor.obtenerTerreno()
    assert terreno[20, 10] == int(EstadoCasilla.agua)
    assert editor.casillas_agua == 1
    assert editor.puede_deshacer

    assert editor.deshacer()
    terreno_deshecho = editor.obtenerTerreno()
    assert terreno_deshecho[20, 10] == int(EstadoCasilla.tierra)
    assert editor.casillas_agua == 0
    assert editor.puede_rehacer

    assert editor.rehacer()
    terreno_rehecho = editor.obtenerTerreno()
    assert terreno_rehecho[20, 10] == int(EstadoCasilla.agua)


@pytest.mark.requisito("RF-08")
def test_borrador_devuelve_casillas_a_tierra():
    editor = EditorMapa()
    editor.pintarCasilla(5, 5)
    assert editor.obtenerTerreno()[5, 5] == int(EstadoCasilla.agua)

    editor.fijarHerramienta(HerramientaEditor.borrador)
    editor.pintarCasilla(5, 5)
    assert editor.obtenerTerreno()[5, 5] == int(EstadoCasilla.tierra)
    assert editor.casillas_agua == 0


@pytest.mark.requisito("RF-08")
def test_tamanos_de_pincel_pintan_area_esperada():
    editor = EditorMapa()
    editor.fijarTamanoPincel(3)
    editor.pintarCasilla(15, 15)

    terreno = editor.obtenerTerreno()
    # Con tamano 3 centrado en (15, 15): abarca indices 14 a 16
    assert np.all(terreno[14:17, 14:17] == int(EstadoCasilla.agua))
    assert editor.casillas_agua == 9


@pytest.mark.requisito("RF-08")
def test_tamano_pincel_fuera_de_rango_lanza_error():
    configuracion = ConfiguracionApp(pincel_minimo=1, pincel_maximo=5)
    editor = EditorMapa(configuracion=configuracion)
    with pytest.raises(ValueError):
        editor.fijarTamanoPincel(0)
    with pytest.raises(ValueError):
        editor.fijarTamanoPincel(6)


@pytest.mark.requisito("RF-08")
def test_trazo_continuo_agrupa_puntos_en_un_solo_deshacer():
    editor = EditorMapa()
    editor.iniciarTrazo()
    editor.agregarPunto(1, 1)
    editor.agregarPunto(2, 2)
    editor.agregarPunto(3, 3)
    editor.finalizarTrazo()

    terreno = editor.obtenerTerreno()
    assert terreno[1, 1] == int(EstadoCasilla.agua)
    assert terreno[2, 2] == int(EstadoCasilla.agua)
    assert terreno[3, 3] == int(EstadoCasilla.agua)

    # Un solo deshacer revierte todo el trazo
    editor.deshacer()
    terreno_limpio = editor.obtenerTerreno()
    assert terreno_limpio[1, 1] == int(EstadoCasilla.tierra)
    assert terreno_limpio[2, 2] == int(EstadoCasilla.tierra)
    assert terreno_limpio[3, 3] == int(EstadoCasilla.tierra)
    assert editor.casillas_agua == 0


@pytest.mark.requisito("RF-08")
def test_cancelar_trazo_descarta_cambios_en_curso():
    editor = EditorMapa()
    editor.iniciarTrazo()
    editor.agregarPunto(8, 8)
    editor.cancelarTrazo()

    assert editor.obtenerTerreno()[8, 8] == int(EstadoCasilla.tierra)
    assert not editor.puede_deshacer


@pytest.mark.requisito("RF-08")
def test_rectangulo_pinta_area_delimitada():
    editor = EditorMapa()
    editor.pintarRectangulo(10, 10, 14, 13)
    terreno = editor.obtenerTerreno()
    # 5 columnas (10 a 14) x 4 filas (10 a 13) = 20 casillas
    assert np.all(terreno[10:14, 10:15] == int(EstadoCasilla.agua))
    assert editor.casillas_agua == 20

    # Deshacer elimina el rectangulo
    editor.deshacer()
    assert editor.casillas_agua == 0


@pytest.mark.requisito("RF-08")
def test_limpiar_restaura_todo_el_mapa_a_tierra():
    editor = EditorMapa()
    editor.pintarRectangulo(0, 0, 50, 50)
    assert editor.casillas_agua > 0

    editor.limpiar()
    assert editor.casillas_agua == 0
    assert np.all(editor.obtenerTerreno() == int(EstadoCasilla.tierra))

    # Se puede deshacer el limpiar
    editor.deshacer()
    assert editor.casillas_agua == 51 * 51


@pytest.mark.requisito("RF-08")
def test_limite_de_pasos_de_deshacer():
    configuracion = ConfiguracionApp(pasos_deshacer=3)
    editor = EditorMapa(tamano=20, configuracion=configuracion)

    for i in range(5):
        editor.pintarCasilla(i, i)

    # Solo deben poder deshacerse los ultimos 3 pasos
    assert editor.deshacer()
    assert editor.deshacer()
    assert editor.deshacer()
    assert not editor.deshacer()


@pytest.mark.requisito("RF-08")
def test_nuevo_trazo_invalida_historial_de_rehacer():
    editor = EditorMapa()
    editor.pintarCasilla(2, 2)
    editor.deshacer()
    assert editor.puede_rehacer

    editor.pintarCasilla(5, 5)
    assert not editor.puede_rehacer


@pytest.mark.requisito("RF-08")
def test_coordenadas_en_bordes_y_fuera_de_limites():
    editor = EditorMapa(tamano=10)
    # No debe fallar en esquinas o fuera
    editor.pintarCasilla(0, 0)
    editor.pintarCasilla(9, 9)
    editor.pintarCasilla(20, 20)
    editor.pintarCasilla(-5, -5)
    terreno = editor.obtenerTerreno()
    assert terreno[0, 0] == int(EstadoCasilla.agua)
    assert terreno[9, 9] == int(EstadoCasilla.agua)


@pytest.mark.requisito("RF-09")
def test_porcentaje_de_agua_y_presencia_de_agua():
    editor = EditorMapa(tamano=10)
    assert not editor.tiene_agua
    assert editor.porcentaje_agua == 0.0

    # 10x10 = 100 casillas. Pintar 21 casillas da exactamente 21.0 %
    editor.pintarRectangulo(0, 0, 2, 6)  # 3 x 7 = 21 casillas
    assert editor.casillas_agua == 21
    assert editor.porcentaje_agua == 21.0
    assert editor.tiene_agua


@pytest.mark.requisito("RF-09")
def test_cargar_terreno_valida_dimensiones():
    editor = EditorMapa(tamano=10)
    nuevo = np.full((10, 10), fill_value=int(EstadoCasilla.agua), dtype=np.uint8)
    editor.cargarTerreno(nuevo)
    assert editor.casillas_agua == 100
    assert editor.porcentaje_agua == 100.0
    assert editor.tiene_agua

    invalido = np.zeros((5, 5), dtype=np.uint8)
    with pytest.raises(ValueError):
        editor.cargarTerreno(invalido)

