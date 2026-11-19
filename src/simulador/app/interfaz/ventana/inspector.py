"""Inspector de casillas y criaturas del mapa (P-10, RF-20)."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class InspectorWidget(QFrame):
    """Tarjeta flotante de detalle para la casilla o criatura seleccionada."""

    cerrarSolicitado = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._construirInterfaz()

    def _construirInterfaz(self) -> None:
        self.setStyleSheet(
            "InspectorWidget {"
            "  background-color: white; border: 1px solid #D0C9BE; border-radius: 10px;"
            "}"
        )
        self.setFixedWidth(240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Encabezado: Título + Botón Cerrar
        layout_header = QHBoxLayout()
        self.lbl_titulo = QLabel("Criatura")
        self.lbl_titulo.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E1E1E;")

        self.btn_cerrar = QPushButton("✕")
        self.btn_cerrar.setFixedSize(20, 20)
        self.btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cerrar.setStyleSheet(
            "QPushButton { border: none; font-size: 14px; color: #888888; font-weight: bold; }"
            "QPushButton:hover { color: #1E1E1E; }"
        )
        self.btn_cerrar.clicked.connect(self.cerrarSolicitado.emit)

        layout_header.addWidget(self.lbl_titulo)
        layout_header.addStretch()
        layout_header.addWidget(self.btn_cerrar)
        layout.addLayout(layout_header)

        # Especie
        self.lbl_especie = QLabel("Especie: Desconocida")
        self.lbl_especie.setStyleSheet("font-size: 12px; font-weight: 500; color: #333333;")
        layout.addWidget(self.lbl_especie)

        # Métricas vitales
        self.contenedor_metricas = QVBoxLayout()
        self.contenedor_metricas.setSpacing(4)

        self.lbl_edad = QLabel("Edad: 0 ticks")
        self.lbl_saciedad = QLabel("Saciedad: 100 %")
        self.lbl_hidratacion = QLabel("Hidratación: 100 %")
        self.lbl_estado = QLabel("Estado: Normal")

        for lbl in (self.lbl_edad, self.lbl_saciedad, self.lbl_hidratacion, self.lbl_estado):
            lbl.setStyleSheet("font-size: 12px; color: #555555;")
            self.contenedor_metricas.addWidget(lbl)

        layout.addLayout(self.contenedor_metricas)

    def _mostrar(self, titulo: str, especie: str, lineas: list[str]) -> None:
        """Pone el texto, oculta las filas vacias y ajusta el tamano a lo que hay.

        El inspector flota sobre el mapa sin estar en ningun layout, asi que no
        toma solo el tamano de su contenido: hay que pedirselo con adjustSize()."""
        self.lbl_titulo.setText(titulo)
        self.lbl_especie.setText(especie)
        etiquetas = (self.lbl_edad, self.lbl_saciedad, self.lbl_hidratacion, self.lbl_estado)
        for etiqueta, texto in zip(etiquetas, lineas + [""] * len(etiquetas), strict=False):
            etiqueta.setText(texto)
            etiqueta.setVisible(bool(texto))
        self.adjustSize()
        self.move(10, 10)
        self.show()
        self.raise_()

    def mostrarCasilla(self, x: int, y: int, tipo: str, detalles: list[str] | None = None) -> None:
        """Presenta los datos de una casilla seleccionada."""
        self._mostrar(f"Casilla ({x}, {y})", f"Tipo: {tipo}", detalles or [])

    def mostrarCriatura(
        self,
        especie_nombre: str,
        edad: int | None = None,
        saciedad: int | None = None,
        hidratacion: int | None = None,
        estado: str | None = None,
        detalles: list[str] | None = None,
    ) -> None:
        """Presenta lo que se sabe de una criatura. Solo se muestran los datos que se dan."""
        lineas = list(detalles or [])
        if edad is not None:
            lineas.append(f"Edad: {edad} ticks")
        if saciedad is not None:
            lineas.append(f"Saciedad: {saciedad} %")
        if hidratacion is not None:
            lineas.append(f"Hidratación: {hidratacion} %")
        if estado is not None:
            lineas.append(f"Estado: {estado}")
        self._mostrar("Criatura", f"Especie: {especie_nombre}", lineas)
