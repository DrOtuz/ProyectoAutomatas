"""Pantalla de configuracion para una nueva simulacion (P-03, RF-07)."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from simulador.configuracion.app import ConfiguracionApp
from simulador.contratos.almacenamiento import Almacenamiento, validarNombre
from simulador.contratos.errores import NombreInvalido


class NuevaSimulacionWidget(QWidget):
    """Formulario para asignar nombre y semilla previa al editor de mapa."""

    continuarEditor = Signal(str, object)
    cancelar = Signal()

    def __init__(
        self,
        almacenamiento: Almacenamiento,
        configuracion: ConfiguracionApp | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._almacenamiento = almacenamiento
        self._configuracion = configuracion or ConfiguracionApp()
        self._construirInterfaz()

    def _construirInterfaz(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 30, 40, 30)
        layout_principal.setSpacing(25)

        # Encabezado de navegacion
        layout_nav = QHBoxLayout()
        self.btn_volver = QPushButton("< Menú")
        self.btn_volver.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_volver.setStyleSheet(
            "QPushButton { border: none; font-size: 14px; font-weight: bold; color: #555555; }"
            "QPushButton:hover { color: #1E1E1E; }"
        )
        self.btn_volver.clicked.connect(self.cancelar.emit)

        separador_nav = QLabel(" |  Nueva simulación")
        separador_nav.setStyleSheet("font-size: 14px; color: #888888;")

        layout_nav.addWidget(self.btn_volver)
        layout_nav.addWidget(separador_nav)
        layout_nav.addStretch()
        layout_principal.addLayout(layout_nav)

        # Cuerpo dividido en formulario (izq) y resumen (der)
        layout_cuerpo = QHBoxLayout()
        layout_cuerpo.setSpacing(35)

        # Columna formulario
        columna_form = QVBoxLayout()
        columna_form.setSpacing(15)

        titulo = QLabel("Ponle nombre a tu\nmundo")
        titulo.setStyleSheet("font-size: 28px; font-weight: bold; color: #1E1E1E;")

        subtitulo = QLabel("Después podrás dibujar el mapa antes de empezar.")
        subtitulo.setStyleSheet("font-size: 14px; color: #666666;")

        columna_form.addWidget(titulo)
        columna_form.addWidget(subtitulo)
        columna_form.addSpacing(10)

        # Campo Nombre
        lbl_nombre = QLabel("Nombre")
        lbl_nombre.setStyleSheet("font-weight: bold; font-size: 13px; color: #333333;")

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ej. Laguna del sur")
        self.input_nombre.setStyleSheet(
            "QLineEdit {"
            "  padding: 10px 14px; border: 1px solid #D0C9BE; border-radius: 8px; font-size: 14px;"
            "}"
            "QLineEdit:focus { border: 1px solid #1B5E20; }"
        )
        self.input_nombre.textChanged.connect(self._alCambiarTexto)

        max_caracteres = self._configuracion.largo_maximo_nombre
        ayuda_nombre = QLabel(f"De 1 a {max_caracteres} caracteres, sin espacios al inicio ni al final.")
        ayuda_nombre.setStyleSheet("font-size: 12px; color: #777777;")

        self.lbl_error_nombre = QLabel()
        self.lbl_error_nombre.setStyleSheet("font-size: 12px; color: #D32F2F; font-weight: bold;")
        self.lbl_error_nombre.hide()

        columna_form.addWidget(lbl_nombre)
        columna_form.addWidget(self.input_nombre)
        columna_form.addWidget(self.lbl_error_nombre)
        columna_form.addWidget(ayuda_nombre)
        columna_form.addSpacing(10)

        # Campo Semilla
        lbl_semilla = QLabel("Semilla (opcional)")
        lbl_semilla.setStyleSheet("font-weight: bold; font-size: 13px; color: #333333;")

        self.input_semilla = QLineEdit()
        self.input_semilla.setPlaceholderText("Por ejemplo, 2026")
        self.input_semilla.setStyleSheet(
            "QLineEdit {"
            "  padding: 10px 14px; border: 1px solid #D0C9BE; border-radius: 8px; font-size: 14px;"
            "}"
            "QLineEdit:focus { border: 1px solid #1B5E20; }"
        )

        ayuda_semilla = QLabel("La misma semilla repite la misma simulación.")
        ayuda_semilla.setStyleSheet("font-size: 12px; color: #777777;")

        columna_form.addWidget(lbl_semilla)
        columna_form.addWidget(self.input_semilla)
        columna_form.addWidget(ayuda_semilla)
        columna_form.addStretch()

        # Botonera
        layout_botones = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancelar.setStyleSheet(
            "QPushButton {"
            "  background-color: transparent; border: 1px solid #D0C9BE; border-radius: 8px;"
            "  padding: 10px 20px; font-size: 14px; font-weight: bold; color: #333333;"
            "}"
            "QPushButton:hover { background-color: #F5F3EF; }"
        )
        self.btn_cancelar.clicked.connect(self.cancelar.emit)

        self.btn_continuar = QPushButton("Continuar al editor >")
        self.btn_continuar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_continuar.setStyleSheet(
            "QPushButton {"
            "  background-color: #1B5E20; border: none; border-radius: 8px;"
            "  padding: 10px 22px; font-size: 14px; font-weight: bold; color: white;"
            "}"
            "QPushButton:hover { background-color: #2E7D32; }"
        )
        self.btn_continuar.clicked.connect(self._onContinuar)

        layout_botones.addWidget(self.btn_cancelar)
        layout_botones.addWidget(self.btn_continuar)
        layout_botones.addStretch()
        columna_form.addLayout(layout_botones)

        # Columna resumen / info ("Así empieza tu mundo")
        panel_resumen = QFrame()
        panel_resumen.setStyleSheet(
            "QFrame {"
            "  background-color: #FBF9F5; border: 1px solid #E5E0D8; border-radius: 14px;"
            "  padding: 20px;"
            "}"
        )
        layout_resumen = QVBoxLayout(panel_resumen)
        layout_resumen.setSpacing(15)

        titulo_resumen = QLabel("Así empieza tu mundo")
        titulo_resumen.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E1E1E;")

        caja_mapa = QFrame()
        caja_mapa.setStyleSheet(
            "background-color: #C9A66B; border-radius: 8px; min-height: 120px;"
        )
        layout_caja_mapa = QVBoxLayout(caja_mapa)
        layout_caja_mapa.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_casillas = QLabel("100 × 100 casillas de tierra")
        lbl_casillas.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0.85); border-radius: 6px;"
            "padding: 4px 10px; font-size: 12px; font-weight: bold; color: #333333;"
        )
        layout_caja_mapa.addWidget(lbl_casillas)

        layout_metricas = QHBoxLayout()
        for titulo_m, valor_m in [("Nutrientes", "50"), ("Tick", "0"), ("Estación", "Primavera")]:
            tarjeta = QFrame()
            tarjeta.setStyleSheet(
                "background-color: white; border: 1px solid #E5E0D8; border-radius: 8px; padding: 6px;"
            )
            l_t = QVBoxLayout(tarjeta)
            l_t.setSpacing(2)
            l_t.addWidget(QLabel(titulo_m))
            v = QLabel(valor_m)
            v.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E1E1E;")
            l_t.addWidget(v)
            layout_metricas.addWidget(tarjeta)

        layout_resumen.addWidget(titulo_resumen)
        layout_resumen.addWidget(caja_mapa)
        layout_resumen.addLayout(layout_metricas)
        layout_resumen.addStretch()

        layout_cuerpo.addLayout(columna_form, 3)
        layout_cuerpo.addWidget(panel_resumen, 2)
        layout_principal.addLayout(layout_cuerpo)

    def limpiar(self) -> None:
        """Restablece los campos de entrada."""
        self.input_nombre.clear()
        self.input_semilla.clear()
        self.lbl_error_nombre.hide()

    def _alCambiarTexto(self) -> None:
        self.lbl_error_nombre.hide()

    def _onContinuar(self) -> None:
        nombre = self.input_nombre.text()
        largo_max = self._configuracion.largo_maximo_nombre

        try:
            validarNombre(nombre, largo_max)
        except NombreInvalido as error:
            self.lbl_error_nombre.setText(str(error))
            self.lbl_error_nombre.show()
            return

        # Comprobar nombre repetido en almacenamiento (sin distinguir mayusculas)
        existentes = [s.nombre.lower() for s in self._almacenamiento.listar()]
        if nombre.lower() in existentes:
            self.lbl_error_nombre.setText("Ya existe una simulación con ese nombre.")
            self.lbl_error_nombre.show()
            return

        # Interpretar semilla
        texto_semilla = self.input_semilla.text().strip()
        semilla: int | str | None = None
        if texto_semilla:
            try:
                semilla = int(texto_semilla)
            except ValueError:
                semilla = texto_semilla

        self.continuarEditor.emit(nombre, semilla)

