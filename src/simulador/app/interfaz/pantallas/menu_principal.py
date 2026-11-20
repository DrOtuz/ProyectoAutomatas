"""Pantalla del menu principal (P-02, RF-06)."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MenuPrincipalWidget(QWidget):
    """Pantalla inicial con opciones para crear o cargar una simulacion."""

    solicitarCrear = Signal()
    solicitarCargar = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._construirInterfaz()

    def _construirInterfaz(self) -> None:
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 40)
        layout_principal.setSpacing(40)

        # Columna izquierda: titulos y opciones
        columna_izq = QVBoxLayout()
        columna_izq.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        columna_izq.setSpacing(20)

        etiqueta_logo = QLabel("🌱 Ecosistema vivo")
        etiqueta_logo.setStyleSheet("font-size: 16px; font-weight: bold; color: #2E7D32;")

        titulo = QLabel("Simulador de\necosistemas")
        titulo.setStyleSheet("font-size: 36px; font-weight: bold; color: #1E1E1E; line-height: 1.1;")

        subtitulo = QLabel(
            "Dibuja un mundo, suelta criaturas y observa\ncómo la vida se abre camino."
        )
        subtitulo.setStyleSheet("font-size: 15px; color: #555555; line-height: 1.4;")

        self.btn_crear = QPushButton("+  Crear simulación")
        self.btn_crear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_crear.setStyleSheet(
            "QPushButton {"
            "  background-color: #1B5E20; color: white; font-size: 15px; font-weight: bold;"
            "  padding: 12px 24px; border-radius: 8px; border: none; text-align: left;"
            "}"
            "QPushButton:hover { background-color: #2E7D32; }"
        )
        self.btn_crear.clicked.connect(self.solicitarCrear.emit)

        self.btn_cargar = QPushButton("📁  Cargar simulación")
        self.btn_cargar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cargar.setStyleSheet(
            "QPushButton {"
            "  background-color: #FFFFFF; color: #1E1E1E; font-size: 15px; font-weight: 500;"
            "  padding: 12px 24px; border-radius: 8px; border: 1px solid #D0C9BE; text-align: left;"
            "}"
            "QPushButton:hover { background-color: #F5F3EF; }"
        )
        self.btn_cargar.clicked.connect(self.solicitarCargar.emit)

        columna_izq.addWidget(etiqueta_logo)
        columna_izq.addWidget(titulo)
        columna_izq.addWidget(subtitulo)
        columna_izq.addSpacing(10)
        columna_izq.addWidget(self.btn_crear)
        columna_izq.addWidget(self.btn_cargar)

        # Columna derecha: panel ilustrativo / tarjeta
        panel_ilustracion = QFrame()
        panel_ilustracion.setStyleSheet(
            "QFrame {"
            "  background-color: #E8EFE6; border-radius: 16px; border: 1px solid #D4DFD2;"
            "}"
        )
        layout_ilustracion = QVBoxLayout(panel_ilustracion)
        layout_ilustracion.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icono_preview = QLabel("🌍")
        icono_preview.setStyleSheet("font-size: 72px;")
        icono_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pie_preview = QLabel("Mundo vivo determinista")
        pie_preview.setStyleSheet("font-size: 14px; font-weight: bold; color: #388E3C;")

        layout_ilustracion.addWidget(icono_preview)
        layout_ilustracion.addWidget(pie_preview)

        layout_principal.addLayout(columna_izq, 1)
        layout_principal.addWidget(panel_ilustracion, 1)

