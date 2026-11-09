"""Visor de mapa interactivo con pyqtgraph (P-06, RF-13, RF-20, RNF-03)."""

from __future__ import annotations

import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from simulador.app.interfaz.estilos import PALETA_ESPECIES, construirTablaColoresTerreno
from simulador.configuracion.app import ConfiguracionApp
from simulador.contratos.instantanea import Instantanea

FIGURAS_PYQTGRAPH = {
    "circulo": "o",
    "cuadrado": "s",
    "triangulo": "t",
    "rombo": "d",
}


class VisorMapa(QWidget):
    """Lienzo central que dibuja la matriz de terreno y las criaturas a partir de una Instantanea."""

    casillaSeleccionada = Signal(int, int)

    def __init__(
        self,
        configuracion: ConfiguracionApp | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._configuracion = configuracion or ConfiguracionApp()
        self._nivel_zoom = float(self._configuracion.zoom_minimo)
        self._tamano_mapa = 100

        self._construirInterfaz()

    def _construirInterfaz(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Widget de pyqtgraph
        self.grafico = pg.GraphicsLayoutWidget(self)
        self.grafico.setBackground("#FBF9F5")

        self.vista = self.grafico.addViewBox(lockAspect=True, enableMenu=False)
        self.vista.setRange(xRange=(0, self._tamano_mapa), yRange=(0, self._tamano_mapa))

        # Item de imagen para terreno
        self._item_terreno = pg.ImageItem()
        self._lut = construirTablaColoresTerreno()
        self._item_terreno.setLookupTable(self._lut)
        self._item_terreno.setLevels([0, 255])
        self.vista.addItem(self._item_terreno)

        # Item de dispersion para criaturas
        self._item_criaturas = pg.ScatterPlotItem(
            size=self._configuracion.tamano_casilla_px,
            pen=pg.mkPen(color="w", width=1),
        )
        self.vista.addItem(self._item_criaturas)

        # Capturar clics del raton en la vista
        self.vista.scene().sigMouseClicked.connect(self._alHacerClic)

        # Etiqueta flotante / indicador de zoom en la esquina
        self.etiqueta_zoom = QLabel(
            f"Rueda: zoom {self._configuracion.zoom_minimo}× a {self._configuracion.zoom_maximo}× · Arrastra para mover",
            self,
        )
        self.etiqueta_zoom.setStyleSheet(
            "background-color: rgba(30, 30, 30, 0.75); color: white; padding: 4px 10px;"
            "border-radius: 6px; font-size: 11px;"
        )

        contenedor_flotante = QFrame(self)
        contenedor_layout = QVBoxLayout(contenedor_flotante)
        contenedor_layout.addStretch()
        contenedor_layout.addWidget(self.etiqueta_zoom, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(self.grafico)

    @property
    def zoom_actual(self) -> float:
        """Nivel actual de zoom."""
        return self._nivel_zoom

    def fijarZoom(self, nivel: float) -> None:
        """Ajusta el zoom entre los limites configurados."""
        minimo = float(self._configuracion.zoom_minimo)
        maximo = float(self._configuracion.zoom_maximo)
        self._nivel_zoom = max(minimo, min(maximo, nivel))
        ancho_visible = self._tamano_mapa / self._nivel_zoom
        centro = self._tamano_mapa / 2.0
        rango = (centro - ancho_visible / 2.0, centro + ancho_visible / 2.0)
        self.vista.setRange(xRange=rango, yRange=rango, padding=0)

    def actualizarInstantanea(self, instantanea: Instantanea) -> None:
        """Dibuja el nuevo fotograma a partir de los arreglos inmutables de la instantanea."""
        terreno = instantanea.terreno
        self._tamano_mapa = terreno.shape[0]

        # pyqtgraph ImageItem espera matriz transpuesta (eje x, eje y)
        self._item_terreno.setImage(terreno.T, autoLevels=False)

        # Dibujar criaturas
        criaturas = instantanea.criaturas
        if criaturas.shape[0] == 0:
            self._item_criaturas.setData([])
            return

        xs = criaturas[:, 0] + 0.5
        ys = criaturas[:, 1] + 0.5
        simbolo = FIGURAS_PYQTGRAPH.get(self._configuracion.figura_criatura, "o")

        # Asignar colores segun especie_id
        spots = []
        colores_especie: dict[int, str] = {}
        for esp in instantanea.especies:
            idx = esp.color % len(PALETA_ESPECIES)
            colores_especie[esp.especie_id] = PALETA_ESPECIES[idx]

        for i in range(criaturas.shape[0]):
            especie_id = int(criaturas[i, 2])
            color_hex = colores_especie.get(especie_id, "#FFFFFF")
            spots.append({
                "pos": (xs[i], ys[i]),
                "brush": pg.mkBrush(color_hex),
                "symbol": simbolo,
            })

        self._item_criaturas.setData(spots)

    def _alHacerClic(self, evento) -> None:
        posicion = evento.scenePos()
        if not self.vista.sceneBoundingRect().contains(posicion):
            return
        punto_vista = self.vista.mapSceneToView(posicion)
        x = int(punto_vista.x())
        y = int(punto_vista.y())
        if 0 <= x < self._tamano_mapa and 0 <= y < self._tamano_mapa:
            self.casillaSeleccionada.emit(x, y)
