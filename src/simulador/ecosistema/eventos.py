"""GestorEventos: sequia, lluvia y focos de incendio naturales.

Consumo de azar fijo (RNF-05): en cada paso se sacan siempre 5 numeros con una sola llamada
a rng.random(5): inicio de sequia, inicio de lluvia, foco natural, duracion de sequia y
duracion de lluvia. Un evento manual pendiente usa los mismos numeros de duracion.

Las tasas `lambda` son eventos esperados por estacion; la probabilidad por tick es
lambda / ticks_por_estacion. Las duraciones son fracciones de estacion.
"""
from __future__ import annotations

from simulador.contratos.errores import ErrorSimulador

__all__ = ["TIPOS_NATURALES", "ErrorSimulador", "GestorEventos"]

TIPOS_NATURALES = ("sequia", "lluvia")


class GestorEventos:
    def __init__(self, rng, config: dict | None = None) -> None:
        if config is None:
            from simulador.configuracion.ecosistema import EVENTOS

            config = EVENTOS
        self._rng = rng
        self._cfg = config
        self.activos: dict[str, int] = {}  # tipo -> ticks restantes
        self.foco = False  # hay foco natural de incendio en este tick
        self._pendientes: list[str] = []
        self._cancelar: list[str] = []
        self.iniciados: list[tuple[str, str]] = []  # (tipo, "natural" | "manual") del ultimo paso
        self.terminados: list[tuple[str, bool]] = []  # (tipo, cancelado) del ultimo paso

    # ---------- ordenes del usuario ----------

    def provocarEvento(self, tipo: str) -> None:
        if tipo not in TIPOS_NATURALES:
            raise ErrorSimulador(f"Evento desconocido: {tipo}")
        if tipo in self.activos or tipo in self._pendientes:
            raise ErrorSimulador("Ese evento ya esta activo")
        self._pendientes.append(tipo)

    def cancelarEvento(self, tipo: str) -> None:
        if tipo not in self.activos and tipo not in self._pendientes:
            raise ErrorSimulador("Ese evento no esta activo")
        if tipo in self._pendientes:
            self._pendientes.remove(tipo)
        else:
            self._cancelar.append(tipo)

    # ---------- paso del tick ----------

    def paso(self, reloj) -> None:
        u = self._rng.random(5)
        tps = reloj.ticks_por_estacion
        lam = self._cfg["lambda"][reloj.estacion]
        self.iniciados = []
        self.terminados = []

        for tipo in self._cancelar:
            if self.activos.pop(tipo, None) is not None:
                self.terminados.append((tipo, True))
        self._cancelar = []

        for tipo in list(self.activos):
            self.activos[tipo] -= 1
            if self.activos[tipo] <= 0:
                del self.activos[tipo]
                self.terminados.append((tipo, False))

        duraciones = {"sequia": u[3], "lluvia": u[4]}
        for tipo in self._pendientes:
            self._iniciar(tipo, duraciones[tipo], tps, "manual")
        self._pendientes = []
        for tipo, sorteo in (("sequia", u[0]), ("lluvia", u[1])):
            if tipo not in self.activos and sorteo < lam[tipo] / tps:
                self._iniciar(tipo, duraciones[tipo], tps, "natural")

        multiplicador = self._cfg["multiplicador_foco_sequia"] if "sequia" in self.activos else 1.0
        self.foco = bool(u[2] < lam["foco"] * multiplicador / tps)

    def _iniciar(self, tipo: str, u: float, tps: int, origen: str) -> None:
        minimo, maximo = self._cfg["duracion"][tipo]
        self.activos[tipo] = max(1, round((minimo + (maximo - minimo) * float(u)) * tps))
        self.iniciados.append((tipo, origen))

    # ---------- efectos sobre el resto del ecosistema ----------

    def factorLluviaFuego(self) -> float:
        return self._cfg["factor_lluvia_fuego"] if "lluvia" in self.activos else 1.0

    def probabilidadApagarLlama(self) -> float:
        return self._cfg["probabilidad_apagar_llama"] if "lluvia" in self.activos else 0.0

    def modificadorHumedad(self) -> float:
        return sum(self._cfg["modificador_humedad"][t] for t in self.activos)

    def factorCrecimiento(self) -> float:
        f = 1.0
        for t in self.activos:
            f *= self._cfg["factor_crecimiento"][t]
        return f

    def deltaTemperatura(self) -> float:
        return self._cfg["delta_temperatura_sequia"] if "sequia" in self.activos else 0.0

    # ---------- estado ----------

    def aEstado(self) -> dict:
        return {
            "activos": dict(self.activos),
            "pendientes": list(self._pendientes),
            "cancelar": list(self._cancelar),
            "foco": self.foco,
        }

    def cargarEstado(self, estado: dict) -> None:
        self.activos = {k: int(v) for k, v in estado["activos"].items()}
        self._pendientes = list(estado["pendientes"])
        self._cancelar = list(estado["cancelar"])
        self.foco = bool(estado["foco"])
        self.iniciados = []
        self.terminados = []
