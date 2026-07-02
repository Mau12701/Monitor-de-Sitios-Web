import httpx
import time
from datetime import datetime

def verificar_sitio(url: str) -> dict:
    """Verifica si un sitio está arriba y mide su tiempo de respuesta"""

    # Asegurarse de que la URL tenga protocolo
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    inicio = time.time()
    try:
        response = httpx.get(
            url,
            timeout=10,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SiteMonitor/1.0)"}
        )
        fin = time.time()
        tiempo_ms = round((fin - inicio) * 1000, 1)

        online = response.status_code < 400

        return {
            "url": url,
            "online": online,
            "status_code": response.status_code,
            "tiempo_ms": tiempo_ms,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": None,
        }

    except httpx.TimeoutException:
        return {
            "url": url,
            "online": False,
            "status_code": None,
            "tiempo_ms": None,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": "Timeout",
        }
    except httpx.ConnectError:
        return {
            "url": url,
            "online": False,
            "status_code": None,
            "tiempo_ms": None,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": "No se pudo conectar",
        }
    except Exception as e:
        return {
            "url": url,
            "online": False,
            "status_code": None,
            "tiempo_ms": None,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": str(e),
        }


def verificar_todos(sitios: list) -> list:
    """Verifica una lista de URLs y devuelve los resultados"""
    return [verificar_sitio(s) for s in sitios]


# Para probar sin FastAPI
if __name__ == "__main__":
    prueba = [
        "https://google.com",
        "https://github.com",
        "https://facebook.com",
        "https://un-sitio-que-no-existe-123.com",
    ]

    print("Verificando sitios...\n")
    for url in prueba:
        r = verificar_sitio(url)
        estado = "✓ ONLINE" if r["online"] else "✗ OFFLINE"
        ping = f"{r['tiempo_ms']} ms" if r["tiempo_ms"] else r["error"]
        print(f"{estado:12} {r['status_code'] or '---'}  {ping:12}  {url}")