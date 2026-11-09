"""Panel de control y visualizacion de eventos naturales (RF-18, RF-28, RF-51)."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from simulador.contratos.comandos import TipoEvento
from simulador.contratos.instantanea import InfoEvento

ICONOS_EVENTO = {
    TipoEvento.sequia: "☀️ Sequía",
    TipoEvento.lluvia: "🌧️ Lluvia",
    TipoEvento.incendio: "🔥 Incendio",
}


class PanelEventos(QWidget):
    """Muestra los eventos activos con opcion de cancelarlos y botones para provocarlos."""

    provocarEvento = Signal(object)
    cancelarEvento = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._construirInterfaz()

    def _construirInterfaz(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # Encabezado
        lbl_titulo = QLabel("Eventos")
        lbl_titulo.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E1E1E;")
        layout.addWidget(lbl_titulo)

        # Lista de eventos activos
        self.contenedor_activos = QVBoxLayout()
        self.contenedor_activos.setSpacing(6)

        self.lbl_sin_eventos = QLabel("Sin eventos")
        self.lbl_sin_eventos.setStyleSheet("font-size: 13px; color: #777777; font-style: italic;")
        self.contenedor_activos.addWidget(self.lbl_sin_eventos)

        layout.addLayout(self.contenedor_activos)

        # Botones para provocar eventos
        layout_botones = QHBoxLayout()
        layout_botones.setSpacing(6)

        self.btn_sequia = QPushButton("☀️ Sequía")
        self.btn_lluvia = QPushButton("🌧️ Lluvia")
        self.btn_incendio = QPushButton("🔥 Incendio")

        for btn, tipo in [
            (self.btn_sequia, TipoEvento.sequia),
            (self.btn_lluvia, TipoEvento.lluvia),
            (self.btn_incendio, TipoEvento.incendio),
        ]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton {"
                "  background-color: white; border: 1px solid #D0C9BE; border-radius: 6px;"
                "  padding: 6px 10px; font-size: 12px; font-weight: 500; color: #1E1E1E;"
                "}"
                "QPushButton:hover { background-color: #F5F3EF; }"
            )
            btn.clicked.connect(lambda _, t=tipo: self.provocarEvento.emit(t))
            layout_botones.addWidget(btn)

        layout.addLayout(layout_botones)

    def actualizarEventos(self, eventos: tuple[InfoEvento, ...]) -> None:
        """Sincroniza la lista visual con los eventos reportados por la instantanea."""
        # Limpiar filas existentes
        while self.contenedor_activos.count():
            item = self.contenedor_activos.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not eventos:
            self.lbl_sin_eventos = QLabel("Sin eventos")
            self.lbl_sin_eventos.setStyleSheet(
                "font-size: 13px; color: #777777; font-style: italic;"
            )
            self.contenedor_activos.addWidget(self.lbl_sin_eventos)
            return

        for evento in eventos:
            fila = QFrame()
            fila.setStyleSheet(
                "QFrame {"
                "  background-color: #FFF3E0; border: 1px solid #FFE0B2; border-radius: 6px;"
                "  padding: 4px;"
                "}"
            )
            l_f = QHBoxLayout(fila)
            l_f.setContentsMargins(6, 4, 6, 4)

            nombre = ICONOS_EVENTO.get(evento.tipo, evento.tipo.value)
            if evento.casillas_en_llamas is not None:
                detalle = f"{nombre} ({evento.casillas_en_llamas} en llamas)"
            elif evento.ticks_restantes is not None:
                detalle = f"{nombre} ({evento.ticks_restantes} ticks)"
            else:
                detalle = nombre

            lbl_evento = QLabel(detalle)
            lbl_evento.setStyleSheet("font-size: 12px; font-weight: bold; color: #E65100;")

            btn_cancelar = QPushButton("Cancelar")
            btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_cancelar.setStyleSheet(
                "QPushButton {"
                "  background-color: transparent; border: none; font-size: 11px;"
                "  color: #D32F2F; font-weight: bold;"
                "}"
                "QPushButton:hover { text-decoration: underline; }"
            )
            btn_cancelar.clicked.connect(
                lambda _, t=evento.tipo: self.cancelarEvento.emit(t)
            )

            l_f.addWidget(lbl_evento)
            l_f.addStretch()
            l_f.addWidget(btn_cancelar)

            self.contenedor_activos.addWidget(fila)

