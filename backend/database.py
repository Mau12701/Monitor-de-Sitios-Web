import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "sitios.db")


def inicializar_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabla de sitios registrados
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sitios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            nombre TEXT,
            fecha_agregado TEXT
        )
    """)

    # Tabla de historial de chequeos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sitio_id INTEGER,
            online INTEGER,
            status_code INTEGER,
            tiempo_ms REAL,
            error TEXT,
            fecha TEXT,
            FOREIGN KEY (sitio_id) REFERENCES sitios(id)
        )
    """)

    conn.commit()
    conn.close()


def agregar_sitio(url: str, nombre: str = None):
    inicializar_db()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    if not nombre:
        nombre = url.replace("https://", "").replace("http://", "").split("/")[0]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO sitios (url, nombre, fecha_agregado)
            VALUES (?, ?, ?)
        """, (url, nombre, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return {"ok": True, "mensaje": f"Sitio '{nombre}' agregado correctamente"}
    except sqlite3.IntegrityError:
        return {"ok": False, "mensaje": "Ese sitio ya está registrado"}
    finally:
        conn.close()


def eliminar_sitio(sitio_id: int):
    inicializar_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM historial WHERE sitio_id = ?", (sitio_id,))
    cursor.execute("DELETE FROM sitios WHERE id = ?", (sitio_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "mensaje": "Sitio eliminado"}


def obtener_sitios():
    inicializar_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, url, nombre, fecha_agregado FROM sitios ORDER BY id")
    filas = cursor.fetchall()
    conn.close()
    return [
        {"id": f[0], "url": f[1], "nombre": f[2], "fecha_agregado": f[3]}
        for f in filas
    ]


def guardar_resultado(sitio_id: int, resultado: dict):
    inicializar_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO historial (sitio_id, online, status_code, tiempo_ms, error, fecha)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        sitio_id,
        1 if resultado["online"] else 0,
        resultado.get("status_code"),
        resultado.get("tiempo_ms"),
        resultado.get("error"),
        resultado.get("fecha"),
    ))
    conn.commit()
    conn.close()


def obtener_historial_sitio(sitio_id: int, limite: int = 20):
    inicializar_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT online, status_code, tiempo_ms, error, fecha
        FROM historial
        WHERE sitio_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (sitio_id, limite))
    filas = cursor.fetchall()
    conn.close()
    return [
        {
            "online": bool(f[0]),
            "status_code": f[1],
            "tiempo_ms": f[2],
            "error": f[3],
            "fecha": f[4],
        }
        for f in filas
    ]


def calcular_uptime(sitio_id: int) -> float:
    """Calcula el % de uptime basado en el historial"""
    inicializar_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(online) as online
        FROM historial
        WHERE sitio_id = ?
    """, (sitio_id,))
    fila = cursor.fetchone()
    conn.close()

    total, en_linea = fila
    if not total:
        return 100.0
    return round((en_linea / total) * 100, 1)