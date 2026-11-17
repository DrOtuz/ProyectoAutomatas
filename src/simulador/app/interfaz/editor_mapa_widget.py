"""Widget interactivo del editor de mapa (P-04, RF-08, RF-09)."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from simulador.app.editor.editor_mapa import EditorMapa, HerramientaEditor
from simulador.app.interfaz.dialogos import confirmarMapaSinAgua
from simulador.contratos.instantanea import EstadoCasilla


class LienzoEditor(QWidget):
    """Lienzo que representa el terreno del editor."""

    def __init__(self, editor: EditorMapa | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.editor = editor or EditorMapa()
        self.tamano_celda = 6
        self.dibujando = False
        self.inicio_rectangulo: tuple[int, int] | None = None
        self.ultima_celda: tuple[int, int] | None = None

        self.setFixedSize(600, 600)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)

        terreno = self.editor.obtenerTerreno()

        color_tierra = QColor("#C9A66B")
        color_agua = QColor("#2E86DE")

        for y in range(100):
            for x in range(100):
                estado = terreno[y, x]

                if estado == EstadoCasilla.agua:
                    color = color_agua
                else:
                    color = color_tierra

                painter.fillRect(
                    x * self.tamano_celda,
                    y * self.tamano_celda,
                    self.tamano_celda,
                    self.tamano_celda,
                    color,
                )

        painter.end()

    def obtenerCelda(self, evento) -> tuple[int, int] | None:
        """Convierte la posicion del mouse en coordenadas del mapa."""
        x = int(evento.position().x() // self.tamano_celda)
        y = int(evento.position().y() // self.tamano_celda)

        if 0 <= x < self.editor.tamano and 0 <= y < self.editor.tamano:
            return x, y

        return None

    def mousePressEvent(self, evento) -> None:
        if evento.button() != Qt.MouseButton.LeftButton:
            return

        celda = self.obtenerCelda(evento)

        if celda is None:
            return

        if self.editor.herramienta == HerramientaEditor.rectangulo:
            self.inicio_rectangulo = celda
            return

        self.dibujando = True
        self.ultima_celda = celda

        self.editor.iniciarTrazo()
        self.editor.agregarPunto(*celda)
        self.update()

    def mouseMoveEvent(self, evento) -> None:
        """Dibuja un trazo continuo mientras se arrastra el mouse."""
        if not self.dibujando:
            return

        celda = self.obtenerCelda(evento)

        if celda is None or celda == self.ultima_celda:
            return

        x1, y1 = self.ultima_celda
        x2, y2 = celda

        pasos = max(abs(x2 - x1), abs(y2 - y1))

        for i in range(1, pasos + 1):
            x = round(x1 + (x2 - x1) * i / pasos)
            y = round(y1 + (y2 - y1) * i / pasos)

            self.editor.agregarPunto(x, y)

        self.ultima_celda = celda
        self.update()

    def mouseReleaseEvent(self, evento) -> None:
        if evento.button() != Qt.MouseButton.LeftButton:
            return

        # Dibujar rectangulo con dos esquinas
        if self.inicio_rectangulo is not None:
            celda_final = self.obtenerCelda(evento)

            if celda_final is not None:
                x1, y1 = self.inicio_rectangulo
                x2, y2 = celda_final

                self.editor.pintarRectangulo(x1, y1, x2, y2)
                self.update()

            self.inicio_rectangulo = None
            return

        # Finalizar trazo del pincel o borrador
        if self.dibujando:
            self.editor.finalizarTrazo()
            self.dibujando = False
            self.ultima_celda = None
            self.update()


class EditorMapaWidget(QWidget):
    """Contenedor del lienzo y sus herramientas."""

    mapaConfirmado = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.editor = EditorMapa()
        self.lienzo = LienzoEditor(self.editor, self)

        self.setWindowTitle("Editor de mapas")

        principal = QHBoxLayout(self)
        principal.addWidget(self.lienzo)

        panel = QVBoxLayout()

        # Herramientas de dibujo
        self.btn_pincel = QPushButton("Pincel")
        self.btn_borrador = QPushButton("Borrador")

        self.btn_pincel.setCheckable(True)
        self.btn_borrador.setCheckable(True)
        self.btn_pincel.setChecked(True)

        self.grupo = QButtonGroup(self)
        self.grupo.addButton(self.btn_pincel)
        self.grupo.addButton(self.btn_borrador)

        self.btn_pincel.clicked.connect(
            lambda: self.editor.fijarHerramienta(HerramientaEditor.pincel_agua)
        )

        self.btn_borrador.clicked.connect(
            lambda: self.editor.fijarHerramienta(HerramientaEditor.borrador)
        )

        panel.addWidget(self.btn_pincel)
        panel.addWidget(self.btn_borrador)

        # Herramienta rectangulo
        self.btn_rectangulo = QPushButton("Rectángulo")
        self.btn_rectangulo.setCheckable(True)

        self.grupo.addButton(self.btn_rectangulo)

        self.btn_rectangulo.clicked.connect(
            lambda: self.editor.fijarHerramienta(HerramientaEditor.rectangulo)
        )

        panel.addWidget(self.btn_rectangulo)

        # Tamaño del pincel
        self.etiqueta_tamano = QLabel("Tamaño: 1")

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(1, 5)
        self.slider.setValue(1)
        self.slider.valueChanged.connect(self.cambiarTamano)

        panel.addWidget(self.etiqueta_tamano)
        panel.addWidget(self.slider)

        # Historial
        self.btn_deshacer = QPushButton("Deshacer")
        self.btn_rehacer = QPushButton("Rehacer")

        self.btn_deshacer.clicked.connect(self.deshacer)
        self.btn_rehacer.clicked.connect(self.rehacer)

        panel.addWidget(self.btn_deshacer)
        panel.addWidget(self.btn_rehacer)

        # Limpiar mapa
        self.btn_limpiar = QPushButton("Limpiar")
        self.btn_limpiar.clicked.connect(self.limpiar)
        panel.addWidget(self.btn_limpiar)

        # Confirmar el mapa
        self.btn_confirmar = QPushButton("Confirmar")

        self.btn_confirmar.setStyleSheet(
            "QPushButton {"
            "background-color: #1B5E20;"
            "color: white;"
            "padding: 10px;"
            "font-weight: bold;"
            "border-radius: 6px;"
            "}"
            "QPushButton:hover {"
            "background-color: #2E7D32;"
            "}"
        )

        self.btn_confirmar.clicked.connect(self.confirmarMapa)

        panel.addWidget(self.btn_confirmar)

        panel.addStretch()
        principal.addLayout(panel)

    def cambiarTamano(self, valor: int) -> None:
        self.editor.fijarTamanoPincel(valor)
        self.etiqueta_tamano.setText(f"Tamaño: {valor}")

    def deshacer(self) -> None:
        self.editor.deshacer()
        self.lienzo.update()

    def rehacer(self) -> None:
        self.editor.rehacer()
        self.lienzo.update()

    def limpiar(self) -> None:
        self.editor.limpiar()
        self.lienzo.update()

    def confirmarMapa(self) -> None:
        """Confirma el terreno y advierte si no contiene agua."""
        if not self.editor.tiene_agua:
            continuar = confirmarMapaSinAgua(self)

            if not continuar:
                return

        terreno = self.editor.obtenerTerreno()
        self.mapaConfirmado.emit(terreno)
