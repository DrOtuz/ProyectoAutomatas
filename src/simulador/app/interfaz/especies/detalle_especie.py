"""Detalle de especie con gestion y graficas en tiempo real (P-08, RF-42 a RF-46)."""

from __future__ import annotations

import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from simulador.app.interfaz.estilos import PALETA_ESPECIES
from simulador.contratos.instantanea import InfoEspecie


class DetalleEspecieWidget(QWidget):
    """Panel de detalle, control poblacional y graficas de dinamica temporal (RF-46)."""

    volverLista = Signal()
    agregarCriaturasSolicitado = Signal(int, int)  # especie_id, cantidad
    eliminarCriaturasSolicitado = Signal(int, int)  # especie_id, cantidad
    extinguirEspecieSolicitado = Signal(int)  # especie_id
    eliminarEspecieSolicitado = Signal(int)  # especie_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._especie: InfoEspecie | None = None
        self._historial_ticks: list[int] = []
        self._historial_poblacion: list[int] = []
        self._historial_genes: dict[str, list[float]] = {
            "velocidad": [],
            "fuerza": [],
            "vision": [],
            "tamano": [],
        }

        self._construirInterfaz()

    def _construirInterfaz(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 20, 30, 20)
        layout_principal.setSpacing(15)

        # Encabezado
        layout_nav = QHBoxLayout()
        self.btn_volver = QPushButton("< Especies")
        self.btn_volver.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_volver.setStyleSheet(
            "QPushButton { border: none; font-size: 14px; font-weight: bold; color: #555555; }"
            "QPushButton:hover { color: #1E1E1E; }"
        )
        self.btn_volver.clicked.connect(self.volverLista.emit)

        self.lbl_titulo = QLabel("Especie")
        self.lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E1E1E;")

        self.lbl_estado_badge = QLabel("● Viva · 0 criaturas")
        self.lbl_estado_badge.setStyleSheet(
            "background-color: #E8F5E9; color: #2E7D32; font-size: 12px; font-weight: bold;"
            "padding: 3px 8px; border-radius: 6px;"
        )

        layout_nav.addWidget(self.btn_volver)
        layout_nav.addSpacing(15)
        layout_nav.addWidget(self.lbl_titulo)
        layout_nav.addWidget(self.lbl_estado_badge)
        layout_nav.addStretch()
        layout_principal.addLayout(layout_nav)

        # Cuerpo: 2 columnas
        layout_cuerpo = QHBoxLayout()
        layout_cuerpo.setSpacing(25)

        # Columna Izquierda: Acciones de gestion
        col_izq = QVBoxLayout()
        col_izq.setSpacing(18)

        # Tarjeta Agregar Criaturas (RF-42)
        tarjeta_agregar = QFrame()
        tarjeta_agregar.setStyleSheet(
            "QFrame {"
            "  background-color: white; border: 1px solid #E5E0D8; border-radius: 10px; padding: 12px;"
            "}"
        )
        l_ag = QVBoxLayout(tarjeta_agregar)
        l_ag.setSpacing(10)

        lbl_ag_titulo = QLabel("Agregar criaturas")
        lbl_ag_titulo.setStyleSheet("font-weight: bold; font-size: 14px; color: #1E1E1E;")

        l_input_ag = QHBoxLayout()
        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setRange(1, 1000)
        self.spin_cantidad.setValue(10)
        self.spin_cantidad.setStyleSheet("padding: 6px; font-size: 13px; border: 1px solid #D0C9BE;")

        self.btn_agregar = QPushButton("Agregar")
        self.btn_agregar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_agregar.setStyleSheet(
            "QPushButton {"
            "  background-color: #1B5E20; color: white; font-weight: bold; padding: 6px 14px;"
            "  border-radius: 6px; border: none;"
            "}"
            "QPushButton:hover { background-color: #2E7D32; }"
        )
        self.btn_agregar.clicked.connect(self._onAgregar)

        l_input_ag.addWidget(self.spin_cantidad)
        l_input_ag.addWidget(self.btn_agregar)

        lbl_nota_ag = QLabel("Si el cupo no alcanza, se agregan las que caben y te avisamos.")
        lbl_nota_ag.setStyleSheet("font-size: 11px; color: #777777;")
        lbl_nota_ag.setWordWrap(True)

        l_ag.addWidget(lbl_ag_titulo)
        l_ag.addLayout(l_input_ag)
        l_ag.addWidget(lbl_nota_ag)
        col_izq.addWidget(tarjeta_agregar)

        # Tarjeta Gestionar (RF-43 a RF-45)
        tarjeta_gestion = QFrame()
        tarjeta_gestion.setStyleSheet(
            "QFrame {"
            "  background-color: white; border: 1px solid #E5E0D8; border-radius: 10px; padding: 12px;"
            "}"
        )
        l_gest = QVBoxLayout(tarjeta_gestion)
        l_gest.setSpacing(8)

        lbl_gest_titulo = QLabel("Gestionar")
        lbl_gest_titulo.setStyleSheet("font-weight: bold; font-size: 14px; color: #1E1E1E;")

        self.btn_eliminar_criaturas = QPushButton("⊖  Eliminar criaturas")
        self.btn_eliminar_criaturas.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_eliminar_criaturas.setStyleSheet(
            "QPushButton {"
            "  background-color: transparent; border: 1px solid #D0C9BE; border-radius: 6px;"
            "  padding: 8px; font-size: 13px; text-align: left; font-weight: 500;"
            "}"
            "QPushButton:hover { background-color: #F5F3EF; }"
        )
        self.btn_eliminar_criaturas.clicked.connect(self._onEliminarCriaturas)

        self.btn_extinguir = QPushButton("⌛  Extinguir especie")
        self.btn_extinguir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_extinguir.setStyleSheet(
            "QPushButton {"
            "  background-color: transparent; border: 1px solid #D0C9BE; border-radius: 6px;"
            "  padding: 8px; font-size: 13px; text-align: left; font-weight: 500;"
            "}"
            "QPushButton:hover { background-color: #F5F3EF; }"
        )
        self.btn_extinguir.clicked.connect(self._onExtinguir)

        self.btn_eliminar_especie = QPushButton("🗑️  Eliminar especie")
        self.btn_eliminar_especie.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_eliminar_especie.setStyleSheet(
            "QPushButton {"
            "  background-color: transparent; border: 1px solid #FFCDD2; border-radius: 6px;"
            "  padding: 8px; font-size: 13px; text-align: left; font-weight: bold; color: #D32F2F;"
            "}"
            "QPushButton:hover { background-color: #FFEBEE; }"
        )
        self.btn_eliminar_especie.clicked.connect(self._onEliminarEspecie)

        l_gest.addWidget(lbl_gest_titulo)
        l_gest.addWidget(self.btn_eliminar_criaturas)
        l_gest.addWidget(self.btn_extinguir)
        l_gest.addWidget(self.btn_eliminar_especie)
        col_izq.addWidget(tarjeta_gestion)

        lbl_pausa = QLabel("Todo funciona también con la simulación en pausa.")
        lbl_pausa.setStyleSheet("font-size: 11px; color: #777777;")
        col_izq.addWidget(lbl_pausa)
        col_izq.addStretch()

        # Columna Derecha: Gráficas de Población y Genes (RF-46)
        col_der = QVBoxLayout()
        col_der.setSpacing(14)

        # 1. Gráfica de Población
        lbl_graf_pob = QLabel("Población (Criaturas a lo largo del tiempo)")
        lbl_graf_pob.setStyleSheet("font-weight: bold; font-size: 13px; color: #1E1E1E;")
        self.plot_poblacion = pg.PlotWidget()
        self.plot_poblacion.setBackground("#FBF9F5")
        self.plot_poblacion.showGrid(x=True, y=True, alpha=0.3)
        self.curva_poblacion = self.plot_poblacion.plot(pen=pg.mkPen("#1565C0", width=2))
        col_der.addWidget(lbl_graf_pob)
        col_der.addWidget(self.plot_poblacion)

        # 2. Gráfica de Genes
        lbl_graf_genes = QLabel("Genes promedio (Velocidad, Fuerza, Visión, Tamaño)")
        lbl_graf_genes.setStyleSheet("font-weight: bold; font-size: 13px; color: #1E1E1E;")
        self.plot_genes = pg.PlotWidget()
        self.plot_genes.setBackground("#FBF9F5")
        self.plot_genes.showGrid(x=True, y=True, alpha=0.3)
        self.plot_genes.addLegend()
        self.curva_vel = self.plot_genes.plot(pen=pg.mkPen("#0606F9", width=2), name="Velocidad")
        self.curva_fza = self.plot_genes.plot(pen=pg.mkPen("#06D0F9", width=2, style=Qt.PenStyle.DashLine), name="Fuerza")
        self.curva_vis = self.plot_genes.plot(pen=pg.mkPen("#F9062F", width=2, style=Qt.PenStyle.DotLine), name="Visión")
        self.curva_tam = self.plot_genes.plot(pen=pg.mkPen("#1B5E20", width=2, style=Qt.PenStyle.DashDotLine), name="Tamaño")
        col_der.addWidget(lbl_graf_genes)
        col_der.addWidget(self.plot_genes)

        layout_cuerpo.addLayout(col_izq, 2)
        layout_cuerpo.addLayout(col_der, 3)
        layout_principal.addLayout(layout_cuerpo)

    def fijarEspecie(self, especie: InfoEspecie) -> None:
        """Carga la especie a visualizar."""
        self._especie = especie
        color_hex = PALETA_ESPECIES[especie.color % len(PALETA_ESPECIES)]
        self.lbl_titulo.setText(f"●  {especie.nombre}")
        self.lbl_titulo.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color_hex};")

        estado = "○ Extinta" if especie.extinguida else "● Viva"
        self.lbl_estado_badge.setText(f"{estado} · {especie.poblacion:,} criaturas")
        if especie.extinguida:
            self.lbl_estado_badge.setStyleSheet(
                "background-color: #FFEBEE; color: #C62828; font-size: 12px; font-weight: bold;"
                "padding: 3px 8px; border-radius: 6px;"
            )
        else:
            self.lbl_estado_badge.setStyleSheet(
                "background-color: #E8F5E9; color: #2E7D32; font-size: 12px; font-weight: bold;"
                "padding: 3px 8px; border-radius: 6px;"
            )

    def registrarMuestra(
        self,
        tick: int,
        poblacion: int,
        velocidad: float = 5.0,
        fuerza: float = 5.0,
        vision: float = 5.0,
        tamano: float = 5.0,
    ) -> None:
        """Agrega un punto a las series temporales de la especie."""
        self._historial_ticks.append(tick)
        self._historial_poblacion.append(poblacion)
        self._historial_genes["velocidad"].append(velocidad)
        self._historial_genes["fuerza"].append(fuerza)
        self._historial_genes["vision"].append(vision)
        self._historial_genes["tamano"].append(tamano)

        self.curva_poblacion.setData(self._historial_ticks, self._historial_poblacion)
        self.curva_vel.setData(self._historial_ticks, self._historial_genes["velocidad"])
        self.curva_fza.setData(self._historial_ticks, self._historial_genes["fuerza"])
        self.curva_vis.setData(self._historial_ticks, self._historial_genes["vision"])
        self.curva_tam.setData(self._historial_ticks, self._historial_genes["tamano"])

    def _onAgregar(self) -> None:
        if self._especie:
            self.agregarCriaturasSolicitado.emit(self._especie.especie_id, self.spin_cantidad.value())

    def _onEliminarCriaturas(self) -> None:
        if not self._especie:
            return
        cantidad, ok = QInputDialog.getInt(
            self,
            "Eliminar criaturas",
            f"¿Cuántas criaturas de {self._especie.nombre} deseas retirar?:",
            value=min(10, self._especie.poblacion),
            minValue=1,
            maxValue=max(1, self._especie.poblacion),
        )
        if ok:
            self.eliminarCriaturasSolicitado.emit(self._especie.especie_id, cantidad)

    def _onExtinguir(self) -> None:
        if not self._especie:
            return
        resp = QMessageBox.question(
            self,
            "Extinguir especie",
            f"¿Deseas extinguir la especie «{self._especie.nombre}»? Se retirarán todas sus criaturas.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resp == QMessageBox.StandardButton.Yes:
            self.extinguirEspecieSolicitado.emit(self._especie.especie_id)

    def _onEliminarEspecie(self) -> None:
        if not self._especie:
            return
        cuadro = QMessageBox(self)
        cuadro.setWindowTitle("Eliminar especie")
        cuadro.setText(f"¿Seguro que quieres eliminar la especie «{self._especie.nombre}»? No se puede deshacer.")
        btn_cancelar = cuadro.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        btn_eliminar = cuadro.addButton("Eliminar", QMessageBox.ButtonRole.DestructiveRole)
        cuadro.setDefaultButton(btn_cancelar)

        cuadro.exec()
        if cuadro.clickedButton() == btn_eliminar:
            self.eliminarEspecieSolicitado.emit(self._especie.especie_id)
            self.volverLista.emit()
