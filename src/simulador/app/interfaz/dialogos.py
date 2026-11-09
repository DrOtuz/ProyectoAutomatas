"""Dialogos de confirmacion y aviso para la aplicacion (P-11, RF-09, RF-12)."""

from PySide6.QtWidgets import QMessageBox, QWidget


def confirmarEliminarSimulacion(parent: QWidget | None, nombre_simulacion: str) -> bool:
    """Muestra confirmacion antes de eliminar una simulacion de la biblioteca (RF-12)."""
    cuadro = QMessageBox(parent)
    cuadro.setWindowTitle("Eliminar simulación")
    cuadro.setText(f"¿Seguro que quieres eliminar «{nombre_simulacion}»? No se puede deshacer.")
    btn_cancelar = cuadro.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
    btn_eliminar = cuadro.addButton("Eliminar", QMessageBox.ButtonRole.DestructiveRole)
    cuadro.setDefaultButton(btn_cancelar)

    cuadro.exec()
    return cuadro.clickedButton() == btn_eliminar


def confirmarMapaSinAgua(parent: QWidget | None) -> bool:
    """Advierte que el mapa no tiene casillas de agua antes de iniciar (RF-09)."""
    cuadro = QMessageBox(parent)
    cuadro.setWindowTitle("Tu mapa no tiene agua")
    cuadro.setText(
        "La vegetación crecerá poco y las criaturas morirán de sed. ¿Quieres continuar así?"
    )
    btn_volver = cuadro.addButton("Volver al editor", QMessageBox.ButtonRole.RejectRole)
    btn_continuar = cuadro.addButton("Continuar", QMessageBox.ButtonRole.AcceptRole)
    cuadro.setDefaultButton(btn_volver)

    cuadro.exec()
    return cuadro.clickedButton() == btn_continuar


def mostrarSimulacionNoEncontrada(parent: QWidget | None) -> None:
    """Informa que la simulacion seleccionada ya no existe en el almacenamiento."""
    cuadro = QMessageBox(parent)
    cuadro.setWindowTitle("Simulación no encontrada")
    cuadro.setText("Esa simulación ya no existe. Actualizamos la lista para que veas las que sí están.")
    cuadro.addButton("Aceptar", QMessageBox.ButtonRole.AcceptRole)
    cuadro.exec()

