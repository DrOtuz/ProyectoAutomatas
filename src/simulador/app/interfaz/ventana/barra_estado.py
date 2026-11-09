"""Barra inferior con metricas en tiempo real de la simulacion (RF-17, RF-41)."""

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QWidget,
)

from simulador.contratos.instantanea import Estacion, Instantanea

ICONOS_ESTACION = {
    Estacion.primavera: "🌸 Primavera",
    Estacion.verano: "☀️ Verano",
    Estacion.otono: "🍂 Otoño",
    Estacion.invierno: "❄️ Invierno",
}


class BarraEstado(QWidget):
    """Muestra el tick actual, estacion, temperatura y relacion de criaturas respecto al cupo."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._construirInterfaz()

    def _construirInterfaz(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(25)

        self.setStyleSheet(
            "BarraEstado {"
            "  background-color: #FBF9F5; border-top: 1px solid #E5E0D8;"
            "}"
        )

        # 1. Tick
        self.lbl_tick = QLabel("Tick 0")
        self.lbl_tick.setStyleSheet("font-size: 13px; font-weight: bold; color: #1E1E1E;")

        # 2. Estación
        self.lbl_estacion = QLabel("🌸 Primavera")
        self.lbl_estacion.setStyleSheet("font-size: 13px; font-weight: 500; color: #333333;")

        # 3. Temperatura
        self.lbl_temperatura = QLabel("Temperatura: 20.0 °C")
        self.lbl_temperatura.setStyleSheet("font-size: 13px; color: #555555;")

        # Separador expansible
        layout.addWidget(self.lbl_tick)
        layout.addWidget(self._crearSeparador())
        layout.addWidget(self.lbl_estacion)
        layout.addWidget(self._crearSeparador())
        layout.addWidget(self.lbl_temperatura)
        layout.addStretch()

        # 4. Contador de Criaturas y Cupo (RF-41)
        self.lbl_criaturas = QLabel("Criaturas 0 / 1000")
        self.lbl_criaturas.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #1E1E1E; padding: 2px 6px;"
        )
        layout.addWidget(self.lbl_criaturas)

    def actualizar(self, instantanea: Instantanea) -> None:
        """Actualiza las etiquetas con los datos de la instantanea."""
        self.lbl_tick.setText(f"Tick {instantanea.tick:,}")
        texto_estacion = ICONOS_ESTACION.get(instantanea.estacion, instantanea.estacion.value)
        self.lbl_estacion.setText(texto_estacion)
        self.lbl_temperatura.setText(f"Temperatura: {instantanea.temperatura:.1f} °C")

        total = instantanea.total_criaturas
        cupo = instantanea.cupo
        self.lbl_criaturas.setText(f"Criaturas {total:,} / {cupo:,}")

        # Resaltar si llega al cupo (RF-41 / P-06)
        if total >= cupo:
            self.lbl_criaturas.setStyleSheet(
                "font-size: 13px; font-weight: bold; color: white;"
                "background-color: #D32F2F; border-radius: 4px; padding: 2px 8px;"
            )
        else:
            self.lbl_criaturas.setStyleSheet(
                "font-size: 13px; font-weight: bold; color: #1E1E1E; padding: 2px 6px;"
            )

    def _crearSeparador(self) -> QFrame:
        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.VLine)
        linea.setFrameShadow(QFrame.Shadow.Sunken)
        linea.setStyleSheet("color: #E5E0D8;")
        return linea
