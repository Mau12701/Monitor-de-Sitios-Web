from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import checker
import database

app = FastAPI(title="Monitor de Sitios Web")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")


# ── MODELOS ──
class SitioInput(BaseModel):
    url: str
    nombre: str = None


# ── ENDPOINTS ──

@app.get("/")
def root():
    return FileResponse(os.path.join(frontend_path, "index.html"))


@app.get("/api/sitios")
def listar_sitios():
    """Lista todos los sitios registrados con su estado actual"""
    sitios = database.obtener_sitios()
    resultado = []

    for sitio in sitios:
        historial = database.obtener_historial_sitio(sitio["id"], limite=1)
        ultimo = historial[0] if historial else None
        uptime = database.calcular_uptime(sitio["id"])

        resultado.append({
            **sitio,
            "ultimo_chequeo": ultimo,
            "uptime": uptime,
        })

    return resultado


@app.post("/api/sitios")
def agregar_sitio(data: SitioInput):
    """Agrega un nuevo sitio a monitorear"""
    resultado = database.agregar_sitio(data.url, data.nombre)
    if not resultado["ok"]:
        raise HTTPException(status_code=400, detail=resultado["mensaje"])
    return resultado


@app.delete("/api/sitios/{sitio_id}")
def eliminar_sitio(sitio_id: int):
    """Elimina un sitio y su historial"""
    return database.eliminar_sitio(sitio_id)


@app.post("/api/chequear")
def chequear_todos():
    """Chequea todos los sitios registrados y guarda resultados"""
    sitios = database.obtener_sitios()

    if not sitios:
        return {"mensaje": "No hay sitios registrados", "resultados": []}

    resultados = []
    for sitio in sitios:
        resultado = checker.verificar_sitio(sitio["url"])
        database.guardar_resultado(sitio["id"], resultado)
        resultados.append({
            "id": sitio["id"],
            "nombre": sitio["nombre"],
            **resultado,
        })

    return {"total": len(resultados), "resultados": resultados}


@app.post("/api/chequear/{sitio_id}")
def chequear_uno(sitio_id: int):
    """Chequea un sitio específico"""
    sitios = database.obtener_sitios()
    sitio = next((s for s in sitios if s["id"] == sitio_id), None)

    if not sitio:
        raise HTTPException(status_code=404, detail="Sitio no encontrado")

    resultado = checker.verificar_sitio(sitio["url"])
    database.guardar_resultado(sitio_id, resultado)
    return resultado


@app.get("/api/historial/{sitio_id}")
def historial_sitio(sitio_id: int):
    """Historial de chequeos de un sitio"""
    return database.obtener_historial_sitio(sitio_id, limite=20)