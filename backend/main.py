import os
import pyautogui # <--- IMPORTANTE: La librería que controla el teclado
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Endpoint Tipo Pistola ---
@app.post("/api/escanear/{codigo}") # Usamos POST porque es una acción
def actuar_como_pistola(codigo: str):
    print(f"🔫 Disparo recibido: {codigo}")
    
    # 1. Escribe el código (simula tecleo rápido)
    pyautogui.write(codigo)
    
    # 2. Presiona Enter (para que el POS busque/agregue)
    pyautogui.press('enter')
    
    return {"status": "ok", "mensaje": f"Escribí {codigo} y di Enter"}

# --- Servir Frontend (Igual que antes) ---
backend_dir = os.path.dirname(os.path.abspath(__file__))
dist_dir = os.path.join(backend_dir, "..", "frontend", "dist")

if os.path.exists(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")