import os
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pyautogui
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- WebSocket: Conexiones activas de browsers ---
connected_browsers: Set[WebSocket] = set()


async def broadcast_to_browsers(codigo: str):
    """Envía el código escaneado a todos los browsers conectados"""
    if not connected_browsers:
        print("⚠️  No hay browsers conectados, usando pyautogui como fallback")
        return False
    
    print(f"📡 Enviando a {len(connected_browsers)} browser(s): {codigo}")
    
    # Enviar a todos los browsers conectados
    disconnected = set()
    for browser in connected_browsers:
        try:
            await browser.send_json({"type": "scan", "barcode": codigo})
        except Exception as e:
            print(f"❌ Error enviando a browser: {e}")
            disconnected.add(browser)
    
    # Limpiar conexiones muertas
    for browser in disconnected:
        connected_browsers.discard(browser)
    
    return len(connected_browsers) - len(disconnected) > 0


@app.websocket("/ws/scanner")
async def websocket_scanner(websocket: WebSocket):
    """WebSocket endpoint para browsers del POS"""
    await websocket.accept()
    connected_browsers.add(websocket)
    print(f"🔌 Browser conectado. Total: {len(connected_browsers)}")
    
    try:
        while True:
            # Mantener conexión viva, recibir pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        connected_browsers.discard(websocket)
        print(f"🔌 Browser desconectado. Total: {len(connected_browsers)}")
    except Exception as e:
        connected_browsers.discard(websocket)
        print(f"❌ WebSocket error: {e}")


# --- Endpoint para el móvil scanner ---
@app.post("/api/escanear/{codigo}")
async def actuar_como_pistola(codigo: str):
    """Recibe código del móvil y lo envía a los browsers conectados"""
    print(f"🔫 Disparo recibido: {codigo}")
    
    # Intentar enviar por WebSocket primero
    enviado = await broadcast_to_browsers(codigo)
    
    if not enviado:
        # Fallback: usar pyautogui si no hay browsers conectados
        print("⌨️  Usando pyautogui como fallback...")
        pyautogui.write(codigo, interval=0.01)
        pyautogui.press('enter')
    
    return {
        "status": "ok",
        "mensaje": f"Código {codigo} {'enviado por WebSocket' if enviado else 'escrito con pyautogui'}",
        "websocket": enviado
    }


# --- Endpoint de estado ---
@app.get("/api/status")
async def get_status():
    """Devuelve estado del servidor y conexiones"""
    return {
        "status": "online",
        "connected_browsers": len(connected_browsers)
    }


# --- Servir Frontend del móvil ---
backend_dir = os.path.dirname(os.path.abspath(__file__))
dist_dir = os.path.join(backend_dir, "..", "frontend", "dist")

if os.path.exists(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")