import sqlite3

import pytest

from simulador.app.almacenamiento.sqlite import (
    VERSION_ESQUEMA,
    AlmacenamientoSqlite,
    ErrorEsquema,
)


class AlmacenamientoConCorte(AlmacenamientoSqlite):
    def _puntoDeCorte(self):
        raise RuntimeError("corte simulado")


@pytest.mark.requisito("RF-49")
def test_lo_guardado_sigue_ahi_al_reabrir_el_archivo(tmp_path):
    ruta = tmp_path / "biblioteca.db"
    primero = AlmacenamientoSqlite(ruta)
    resumen = primero.crear("Isla", b"\x00\xffestado", tick=7, velocidad=20)
    primero.cerrar()
    segundo = AlmacenamientoSqlite(ruta)
    assert segundo.cargar(resumen.simulacion_id) == b"\x00\xffestado"
    assert segundo.listar()[0].nombre == "Isla"
    assert segundo.listar()[0].tick == 7
    segundo.cerrar()


@pytest.mark.requisito("RF-50")
def test_un_corte_a_mitad_de_guardar_deja_la_version_anterior(tmp_path):
    ruta = tmp_path / "biblioteca.db"
    normal = AlmacenamientoSqlite(ruta)
    resumen = normal.crear("Isla", b"viejo", tick=1, velocidad=5)
    normal.cerrar()

    con_corte = AlmacenamientoConCorte(ruta)
    with pytest.raises(RuntimeError):
        con_corte.guardar(resumen.simulacion_id, b"nuevo", tick=99, velocidad=30)
    con_corte.cerrar()

    reabierto = AlmacenamientoSqlite(ruta)
    assert reabierto.cargar(resumen.simulacion_id) == b"viejo"
    assert reabierto.listar()[0].tick == 1
    assert reabierto.listar()[0].velocidad == 5
    reabierto.cerrar()


@pytest.mark.requisito("RNF-08")
def test_el_archivo_lleva_la_version_del_esquema(tmp_path):
    ruta = tmp_path / "biblioteca.db"
    AlmacenamientoSqlite(ruta).cerrar()
    conexion = sqlite3.connect(str(ruta))
    version = conexion.execute("PRAGMA user_version").fetchone()[0]
    conexion.close()
    assert version == VERSION_ESQUEMA


@pytest.mark.requisito("RNF-08")
def test_un_archivo_de_una_version_mas_nueva_se_rechaza_sin_danarlo(tmp_path):
    ruta = tmp_path / "biblioteca.db"
    almacenamiento = AlmacenamientoSqlite(ruta)
    resumen = almacenamiento.crear("Isla", b"datos", tick=0, velocidad=1)
    almacenamiento.cerrar()
    conexion = sqlite3.connect(str(ruta))
    conexion.execute(f"PRAGMA user_version = {VERSION_ESQUEMA + 1}")
    conexion.close()

    with pytest.raises(ErrorEsquema, match="mas nueva"):
        AlmacenamientoSqlite(ruta)

    conexion = sqlite3.connect(str(ruta))
    conexion.execute(f"PRAGMA user_version = {VERSION_ESQUEMA}")
    conexion.close()
    recuperado = AlmacenamientoSqlite(ruta)
    assert recuperado.cargar(resumen.simulacion_id) == b"datos"
    recuperado.cerrar()


@pytest.mark.requisito("RF-12")
def test_un_identificador_borrado_no_se_reutiliza(tmp_path):
    almacenamiento = AlmacenamientoSqlite(tmp_path / "biblioteca.db")
    primero = almacenamiento.crear("Isla", b"a", tick=0, velocidad=1)
    almacenamiento.eliminar(primero.simulacion_id)
    segundo = almacenamiento.crear("Bosque", b"b", tick=0, velocidad=1)
    assert segundo.simulacion_id != primero.simulacion_id
    almacenamiento.cerrar()


@pytest.mark.requisito("RF-48")
def test_crea_la_carpeta_si_no_existe(tmp_path):
    ruta = tmp_path / "datos" / "nueva" / "biblioteca.db"
    almacenamiento = AlmacenamientoSqlite(ruta)
    almacenamiento.cerrar()
    assert ruta.exists()


@pytest.mark.requisito("RNF-08")
def test_migracion_de_esquema_anterior_aplica_migraciones_y_actualiza_version(tmp_path, monkeypatch):
    import simulador.app.almacenamiento.sqlite as modulo_sqlite

    ruta = tmp_path / "biblioteca.db"
    almacenamiento_v1 = AlmacenamientoSqlite(ruta)
    resumen = almacenamiento_v1.crear("Isla", b"estado_v1", tick=10, velocidad=5)
    almacenamiento_v1.cerrar()

    # Simular una nueva version de esquema (version 2)
    def migrar_a_v2(conexion: sqlite3.Connection) -> None:
        conexion.execute("ALTER TABLE simulaciones ADD COLUMN notas TEXT DEFAULT ''")

    monkeypatch.setattr(modulo_sqlite, "VERSION_ESQUEMA", 2)
    monkeypatch.setitem(modulo_sqlite._MIGRACIONES, 2, migrar_a_v2)

    almacenamiento_v2 = AlmacenamientoSqlite(ruta)
    assert almacenamiento_v2.cargar(resumen.simulacion_id) == b"estado_v1"
    assert almacenamiento_v2.listar()[0].nombre == "Isla"
    almacenamiento_v2.cerrar()

    conexion = sqlite3.connect(str(ruta))
    version = conexion.execute("PRAGMA user_version").fetchone()[0]
    columnas = [fila[1] for fila in conexion.execute("PRAGMA table_info(simulaciones)").fetchall()]
    conexion.close()

    assert version == 2
    assert "notas" in columnas


@pytest.mark.requisito("RNF-08")
def test_fallo_en_migracion_revierte_cambios_y_no_actualiza_version(tmp_path, monkeypatch):
    import simulador.app.almacenamiento.sqlite as modulo_sqlite

    ruta = tmp_path / "biblioteca.db"
    almacenamiento_v1 = AlmacenamientoSqlite(ruta)
    almacenamiento_v1.crear("Isla", b"datos", tick=1, velocidad=1)
    almacenamiento_v1.cerrar()

    def migrar_con_error(conexion: sqlite3.Connection) -> None:
        conexion.execute("ALTER TABLE simulaciones ADD COLUMN fallo TEXT")
        raise RuntimeError("Fallo forzado en migracion")

    monkeypatch.setattr(modulo_sqlite, "VERSION_ESQUEMA", 2)
    monkeypatch.setitem(modulo_sqlite._MIGRACIONES, 2, migrar_con_error)

    with pytest.raises(RuntimeError, match="Fallo forzado en migracion"):
        AlmacenamientoSqlite(ruta)

    conexion = sqlite3.connect(str(ruta))
    version = conexion.execute("PRAGMA user_version").fetchone()[0]
    columnas = [fila[1] for fila in conexion.execute("PRAGMA table_info(simulaciones)").fetchall()]
    conexion.close()

    assert version == 1
    assert "fallo" not in columnas
