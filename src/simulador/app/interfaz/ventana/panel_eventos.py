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
    incendioSolicitado = Signal()  # el usuario quiere elegir en el mapa donde empieza

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._filas: dict[TipoEvento, QLabel] = {}
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
            if tipo == TipoEvento.incendio:
                btn.clicked.connect(lambda _=False: self.incendioSolicitado.emit())
            else:
                btn.clicked.connect(lambda _, t=tipo: self.provocarEvento.emit(t))
            layout_botones.addWidget(btn)

        layout.addLayout(layout_botones)

        self.lbl_foco = QLabel("Haz clic en el mapa donde quieres que empiece el incendio. Esc para cancelar.")
        self.lbl_foco.setWordWrap(True)
        self.lbl_foco.setStyleSheet("font-size: 12px; color: #B71C1C; font-weight: bold;")
        self.lbl_foco.hide()
        layout.addWidget(self.lbl_foco)

        self.lbl_error = QLabel()
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setStyleSheet("font-size: 12px; color: #D32F2F; font-weight: bold;")
        self.lbl_error.hide()
        layout.addWidget(self.lbl_error)

    def marcarEligiendoFoco(self, activo: bool) -> None:
        """Resalta el boton de incendio y muestra la instruccion mientras se espera el clic."""
        self.lbl_foco.setVisible(activo)
        self.btn_incendio.setText("🔥 Elige la casilla…" if activo else "🔥 Incendio")
        self.btn_incendio.setStyleSheet(
            "QPushButton { background-color: #FFCDD2; border: 1px solid #B71C1C; border-radius: 6px;"
            "  padding: 6px 10px; font-size: 12px; font-weight: 600; color: #B71C1C; }"
            if activo
            else "QPushButton {"
            "  background-color: white; border: 1px solid #D0C9BE; border-radius: 6px;"
            "  padding: 6px 10px; font-size: 12px; font-weight: 500; color: #1E1E1E;"
            "}"
            "QPushButton:hover { background-color: #F5F3EF; }"
        )

    def mostrarError(self, texto: str) -> None:
        """Muestra el motivo por el que el motor rechazo una orden (se borra solo al limpiar)."""
        self.lbl_error.setText(texto)
        self.lbl_error.setVisible(bool(texto))

    @staticmethod
    def _textoEvento(evento: InfoEvento) -> str:
        nombre = ICONOS_EVENTO.get(evento.tipo, evento.tipo.value)
        if evento.casillas_en_llamas is not None:
            return f"{nombre} ({evento.casillas_en_llamas} en llamas)"
        if evento.ticks_restantes is not None:
            return f"{nombre} ({evento.ticks_restantes} ticks)"
        return nombre

    def actualizarEventos(self, eventos: tuple[InfoEvento, ...]) -> None:
        """Sincroniza la lista visual con los eventos reportados por la instantanea.

        Se llama ~30 veces por segundo: las filas (y sus botones Cancelar) solo se rehacen
        cuando cambia el conjunto de eventos. Si se rehicieran en cada llamada, el boton
        desapareceria entre el clic y el soltar y Cancelar nunca respondia.
        """
        tipos = {e.tipo for e in eventos}
        if tipos != set(self._filas):
            self._reconstruir(eventos)
            return
        for evento in eventos:
            self._filas[evento.tipo].setText(self._textoEvento(evento))

    def _reconstruir(self, eventos: tuple[InfoEvento, ...]) -> None:
        while self.contenedor_activos.count():
            item = self.contenedor_activos.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._filas = {}

        if not eventos:
            self.lbl_sin_eventos = QLabel("Sin eventos")
            self.lbl_sin_eventos.setStyleSheet("font-size: 13px; color: #777777; font-style: italic;")
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

            lbl_evento = QLabel(self._textoEvento(evento))
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
            btn_cancelar.clicked.connect(lambda _, t=evento.tipo: self.cancelarEvento.emit(t))

            l_f.addWidget(lbl_evento)
            l_f.addStretch()
            l_f.addWidget(btn_cancelar)

            self.contenedor_activos.addWidget(fila)
            self._filas[evento.tipo] = lbl_evento
