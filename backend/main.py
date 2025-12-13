import os
import socket
import io
from typing import Set, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.requests import Request
import pyautogui
import qrcode
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuración ---
backend_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(backend_dir, "templates")
templates = Jinja2Templates(directory=templates_dir)

# Servir archivos estáticos del dashboard (CSS, etc.)
app.mount("/static", StaticFiles(directory=templates_dir), name="dashboard_static")

# --- Estado Global ---
# Escáneres móviles (se cuentan en dashboard)
scanner_connections: Dict[str, WebSocket] = {}
# Browsers POS (funcionan pero no se cuentan)
connected_browsers: Set[WebSocket] = set()
# Dashboard GUI
connected_dashboard: Set[WebSocket] = set()


def get_local_ip():
    """Detecta la IP local de la máquina"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


# ============================================
# RUTAS DEL DASHBOARD (GUI de escritorio)
# ============================================

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/info")
async def get_server_info():
    ip = get_local_ip()
    return JSONResponse({
        "url": f"https://{ip}:8443",
        "ip": ip,
        "port": 8443,
        "http_port": 8001
    })


@app.get("/api/qr")
async def get_qr_code():
    ip = get_local_ip()
    url = f"https://{ip}:8443"
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


# --- Autostart con Windows ---
import winreg

def get_autostart_status():
    """Verifica si el autostart está habilitado"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, "ScannerPipos")
        winreg.CloseKey(key)
        return True
    except:
        return False

def set_autostart(enable: bool):
    """Habilita o deshabilita el autostart"""
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
    if enable:
        start_bat = os.path.abspath(os.path.join(backend_dir, "..", "start.bat"))
        winreg.SetValueEx(key, "ScannerPipos", 0, winreg.REG_SZ, f'"{start_bat}"')
    else:
        try:
            winreg.DeleteValue(key, "ScannerPipos")
        except:
            pass
    winreg.CloseKey(key)

@app.get("/api/autostart")
async def get_autostart():
    return JSONResponse({"enabled": get_autostart_status()})

@app.post("/api/autostart/toggle")
async def toggle_autostart():
    current = get_autostart_status()
    set_autostart(not current)
    return JSONResponse({"enabled": not current})


# --- Minimizar a bandeja ---
# Variable global para controlar la ventana desde el endpoint
minimize_callback = None

@app.post("/api/minimize")
async def minimize_to_tray():
    global minimize_callback
    if minimize_callback:
        minimize_callback()
    return JSONResponse({"status": "ok"})


@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket para la GUI de escritorio - recibe actualizaciones"""
    await websocket.accept()
    connected_dashboard.add(websocket)
    try:
        await websocket.send_json({
            "type": "stats",
            "scanner_count": len(scanner_connections)
        })
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_dashboard.discard(websocket)


# ============================================
# FUNCIONES AUXILIARES
# ============================================

async def notify_dashboard(event_type: str, data: dict = None):
    """Envía actualizaciones a la GUI"""
    if not connected_dashboard:
        return
    message = {"type": event_type}
    if data:
        message.update(data)
    
    dead = set()
    for ws in connected_dashboard:
        try:
            await ws.send_json(message)
        except:
            dead.add(ws)
    for ws in dead:
        connected_dashboard.discard(ws)


async def broadcast_to_browsers(codigo: str):
    """Envía el código escaneado a todos los browsers POS conectados"""
    await notify_dashboard("scan", {"code": codigo})
    
    if not connected_browsers:
        print("⚠️  No hay browsers POS conectados, usando pyautogui como fallback")
        return False
    
    print(f"📡 Enviando a {len(connected_browsers)} browser(s) POS: {codigo}")
    
    disconnected = set()
    for browser in connected_browsers:
        try:
            await browser.send_json({"type": "scan", "barcode": codigo})
        except Exception as e:
            print(f"❌ Error enviando a browser: {e}")
            disconnected.add(browser)
    
    for browser in disconnected:
        connected_browsers.discard(browser)
    
    return len(connected_browsers) > 0


# ============================================
# WEBSOCKET PRINCIPAL (Scanner Móvil + POS)
# ============================================

@app.websocket("/ws/scanner")
async def websocket_scanner(
    websocket: WebSocket, 
    id: str = Query(default="unknown"),
    type: str = Query(default="pos")
):
    """WebSocket endpoint para escáneres móviles y browsers POS"""
    await websocket.accept()
    
    is_scanner = (type == "scanner")
    
    if is_scanner:
        # Escáner móvil - gestionar con ID único
        if id in scanner_connections:
            print(f"🔄 Reconexión escáner [{id}]")
            try:
                await scanner_connections[id].close()
            except:
                pass
        
        scanner_connections[id] = websocket
        print(f"📱 Escáner móvil conectado [{id}]. Total: {len(scanner_connections)}")
        await notify_dashboard("stats", {"scanner_count": len(scanner_connections)})
        await notify_dashboard("scanner_connected", {"id": id})
    else:
        # Browser POS - solo añadir al set
        connected_browsers.add(websocket)
        print(f"💻 POS conectado. Total POS: {len(connected_browsers)}")

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        if is_scanner:
            if scanner_connections.get(id) == websocket:
                scanner_connections.pop(id, None)
                print(f"📱 Escáner desconectado [{id}]. Total: {len(scanner_connections)}")
                await notify_dashboard("stats", {"scanner_count": len(scanner_connections)})
                await notify_dashboard("scanner_disconnected", {"id": id})
        else:
            connected_browsers.discard(websocket)
            print(f"💻 POS desconectado. Total POS: {len(connected_browsers)}")
    except Exception as e:
        if is_scanner and scanner_connections.get(id) == websocket:
            scanner_connections.pop(id, None)
        else:
            connected_browsers.discard(websocket)


# ============================================
# API ENDPOINTS
# ============================================

@app.post("/api/escanear/{codigo}")
async def actuar_como_pistola(codigo: str):
    """Recibe código del móvil y lo envía a los browsers POS"""
    print(f"🔫 Disparo recibido: {codigo}")
    
    enviado = await broadcast_to_browsers(codigo)
    
    if not enviado:
        print("⌨️  Usando pyautogui como fallback...")
        pyautogui.write(codigo, interval=0.01)
        pyautogui.press('enter')
    
    return {
        "status": "ok",
        "mensaje": f"Código {codigo} {'enviado por WebSocket' if enviado else 'escrito con pyautogui'}",
        "websocket": enviado
    }


@app.get("/api/status")
async def get_status():
    return {
        "status": "online",
        "scanners": len(scanner_connections),
        "browsers": len(connected_browsers)
    }


# --- Servir Frontend del móvil ---
dist_dir = os.path.join(backend_dir, "..", "frontend", "dist")
if os.path.exists(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")