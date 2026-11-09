"""Formulario para la creacion de una nueva especie (P-09, RF-37, RF-55)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from simulador.app.interfaz.estilos import PALETA_ESPECIES


class CrearEspecieWidget(QWidget):
    """Permite configurar y lanzar una nueva especie con color de paleta asignado automaticamente."""

    volverLista = Signal()
    crearEspecieSolicitado = Signal(str, int, object)  # nombre, cantidad, genes (tuple o None)

    def __init__(self, color_siguiente_idx: int = 0, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color_idx = color_siguiente_idx % len(PALETA_ESPECIES)
        self._construirInterfaz()

    def _construirInterfaz(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 30, 40, 30)
        layout_principal.setSpacing(25)

        # Encabezado
        layout_nav = QHBoxLayout()
        self.btn_volver = QPushButton("< Especies")
        self.btn_volver.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_volver.setStyleSheet(
            "QPushButton { border: none; font-size: 14px; font-weight: bold; color: #555555; }"
            "QPushButton:hover { color: #1E1E1E; }"
        )
        self.btn_volver.clicked.connect(self.volverLista.emit)

        lbl_sep = QLabel(" |  Crear especie")
        lbl_sep.setStyleSheet("font-size: 14px; color: #888888;")

        layout_nav.addWidget(self.btn_volver)
        layout_nav.addWidget(lbl_sep)
        layout_nav.addStretch()
        layout_principal.addLayout(layout_nav)

        # Cuerpo: Formulario (izq) y Color (der)
        layout_cuerpo = QHBoxLayout()
        layout_cuerpo.setSpacing(35)

        # Columna Izquierda: Formulario
        col_form = QVBoxLayout()
        col_form.setSpacing(14)

        # Fila Nombre y Cantidad
        layout_campos = QHBoxLayout()
        layout_campos.setSpacing(15)

        col_nombre = QVBoxLayout()
        lbl_nom = QLabel("Nombre")
        lbl_nom.setStyleSheet("font-weight: bold; font-size: 13px; color: #333333;")
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ej. Venados")
        self.input_nombre.setStyleSheet("padding: 8px 12px; border: 1px solid #D0C9BE; border-radius: 6px;")
        col_nombre.addWidget(lbl_nom)
        col_nombre.addWidget(self.input_nombre)

        col_cant = QVBoxLayout()
        lbl_cant = QLabel("Cantidad inicial")
        lbl_cant.setStyleSheet("font-weight: bold; font-size: 13px; color: #333333;")
        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setRange(1, 500)
        self.spin_cantidad.setValue(20)
        self.spin_cantidad.setStyleSheet("padding: 8px 12px; border: 1px solid #D0C9BE; border-radius: 6px;")
        col_cant.addWidget(lbl_cant)
        col_cant.addWidget(self.spin_cantidad)

        layout_campos.addLayout(col_nombre, 2)
        layout_campos.addLayout(col_cant, 1)
        col_form.addLayout(layout_campos)

        # Modo avanzado: genes
        self.chk_modo_avanzado = QCheckBox("Modo avanzado: genes")
        self.chk_modo_avanzado.setStyleSheet("font-size: 13px; font-weight: bold; color: #1E1E1E;")
        self.chk_modo_avanzado.toggled.connect(self._alAlternarModoAvanzado)
        col_form.addWidget(self.chk_modo_avanzado)

        lbl_ayuda_genes = QLabel("Si no los tocas, se usan los valores por defecto.")
        lbl_ayuda_genes.setStyleSheet("font-size: 12px; color: #777777;")
        col_form.addWidget(lbl_ayuda_genes)

        # Panel genes (oculto por defecto)
        self.panel_genes = QFrame()
        self.panel_genes.setStyleSheet(
            "QFrame { background-color: #FBF9F5; border: 1px solid #E5E0D8; border-radius: 8px; padding: 10px; }"
        )
        l_genes = QVBoxLayout(self.panel_genes)
        l_genes.setSpacing(8)

        self.spin_vel = self._crearSpinGen("Velocidad:", l_genes)
        self.spin_fza = self._crearSpinGen("Fuerza:", l_genes)
        self.spin_vis = self._crearSpinGen("Visión:", l_genes)
        self.spin_tam = self._crearSpinGen("Tamaño:", l_genes)
        self.panel_genes.hide()
        col_form.addWidget(self.panel_genes)

        self.lbl_error = QLabel()
        self.lbl_error.setStyleSheet("font-size: 12px; color: #D32F2F; font-weight: bold;")
        self.lbl_error.hide()
        col_form.addWidget(self.lbl_error)
        col_form.addStretch()

        # Botonera
        layout_btns = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancelar.setStyleSheet(
            "QPushButton {"
            "  background-color: transparent; border: 1px solid #D0C9BE; border-radius: 8px;"
            "  padding: 10px 20px; font-size: 14px; font-weight: bold; color: #333333;"
            "}"
            "QPushButton:hover { background-color: #F5F3EF; }"
        )
        self.btn_cancelar.clicked.connect(self.volverLista.emit)

        self.btn_crear = QPushButton("✓  Crear especie")
        self.btn_crear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_crear.setStyleSheet(
            "QPushButton {"
            "  background-color: #1B5E20; border: none; border-radius: 8px;"
            "  padding: 10px 22px; font-size: 14px; font-weight: bold; color: white;"
            "}"
            "QPushButton:hover { background-color: #2E7D32; }"
        )
        self.btn_crear.clicked.connect(self._onCrear)

        layout_btns.addWidget(self.btn_cancelar)
        layout_btns.addWidget(self.btn_crear)
        layout_btns.addStretch()
        col_form.addLayout(layout_btns)

        # Columna Derecha: Tarjeta de Color (RF-55)
        col_color = QVBoxLayout()
        col_color.setSpacing(12)

        lbl_color_tit = QLabel("Su color en el mapa")
        lbl_color_tit.setStyleSheet("font-weight: bold; font-size: 14px; color: #1E1E1E;")

        color_hex = PALETA_ESPECIES[self._color_idx]
        self.tarjeta_color = QFrame()
        self.tarjeta_color.setStyleSheet(
            "QFrame {"
            "  background-color: #FBF9F5; border: 1px solid #E5E0D8; border-radius: 12px; padding: 20px;"
            "}"
        )
        l_c = QVBoxLayout(self.tarjeta_color)
        l_c.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_c.setSpacing(10)

        self.circulo_color = QFrame()
        self.circulo_color.setFixedSize(50, 50)
        self.circulo_color.setStyleSheet(
            f"background-color: {color_hex}; border-radius: 25px; border: 2px solid white;"
        )

        self.lbl_hex = QLabel(color_hex)
        self.lbl_hex.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E1E1E;")

        self.lbl_color_desc = QLabel(
            f"Color {self._color_idx + 1} de 12 de la paleta. Se asigna solo."
        )
        self.lbl_color_desc.setStyleSheet("font-size: 12px; color: #666666;")
        self.lbl_color_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        l_c.addWidget(self.circulo_color)
        l_c.addWidget(self.lbl_hex)
        l_c.addWidget(self.lbl_color_desc)

        col_color.addWidget(lbl_color_tit)
        col_color.addWidget(self.tarjeta_color)
        col_color.addStretch()

        layout_cuerpo.addLayout(col_form, 3)
        layout_cuerpo.addLayout(col_color, 2)
        layout_principal.addLayout(layout_cuerpo)

    def _crearSpinGen(self, etiqueta: str, layout: QVBoxLayout) -> QDoubleSpinBox:
        l = QHBoxLayout()
        lbl = QLabel(etiqueta)
        lbl.setStyleSheet("font-size: 12px; color: #333333;")
        spin = QDoubleSpinBox()
        spin.setRange(1.0, 10.0)
        spin.setValue(5.0)
        spin.setSingleStep(0.5)
        spin.setStyleSheet("padding: 4px; font-size: 12px;")
        l.addWidget(lbl)
        l.addStretch()
        l.addWidget(spin)
        layout.addLayout(l)
        return spin

    def _alAlternarModoAvanzado(self, activo: bool) -> None:
        self.panel_genes.setVisible(activo)

    def _onCrear(self) -> None:
        nombre = self.input_nombre.text().strip()
        if not nombre:
            self.lbl_error.setText("Debes indicar un nombre para la especie.")
            self.lbl_error.show()
            return

        cantidad = self.spin_cantidad.value()
        genes = None
        if self.chk_modo_avanzado.isChecked():
            genes = (
                self.spin_vel.value(),
                self.spin_fza.value(),
                self.spin_vis.value(),
                self.spin_tam.value(),
            )

        self.crearEspecieSolicitado.emit(nombre, cantidad, genes)
