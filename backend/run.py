import os
import sys
import threading
import uvicorn
import webview
from PIL import Image
import pystray

# Asegurar imports correctos
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from main import app, minimize_callback
import main

# Variables globales
window = None
tray_icon = None

# Configuración SSL
SSL_DIR = os.path.join(current_dir, "ssl")
SSL_KEY = os.path.join(SSL_DIR, "key.pem")
SSL_CERT = os.path.join(SSL_DIR, "cert.pem")
HTTPS_PORT = 8443


def ensure_ssl_certificate():
    """Genera certificado SSL si no existe"""
    if os.path.exists(SSL_KEY) and os.path.exists(SSL_CERT):
        return True
    
    try:
        from generate_ssl import generate_ssl_certificate
        generate_ssl_certificate()
        return True
    except Exception as e:
        print(f"Error generando certificado SSL: {e}")
        return False


def create_tray_icon():
    """Crea el icono de la bandeja del sistema"""
    icon_path = os.path.join(current_dir, "..", "frontend", "public", "icon-192.png")
    
    if os.path.exists(icon_path):
        icon_image = Image.open(icon_path)
    else:
        icon_image = Image.new('RGB', (64, 64), color='#3b82f6')
    
    menu = pystray.Menu(
        pystray.MenuItem("Mostrar", show_window, default=True),
        pystray.MenuItem("Salir", quit_app)
    )
    
    return pystray.Icon("scanner_pipos", icon_image, "Scanner Pipos", menu)


def show_window(icon=None, item=None):
    """Muestra la ventana principal"""
    global window
    if window:
        window.show()


def hide_window():
    """Oculta la ventana a la bandeja"""
    global window, tray_icon
    if window:
        window.hide()
    if tray_icon and not tray_icon.visible:
        threading.Thread(target=tray_icon.run, daemon=True).start()


def quit_app(icon=None, item=None):
    """Cierra la aplicación completamente"""
    global window, tray_icon
    if tray_icon:
        tray_icon.stop()
    if window:
        window.destroy()
    os._exit(0)


def run_http_server():
    """Servidor HTTP para el dashboard local"""
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="warning")


def run_https_server():
    """Servidor HTTPS para el móvil (acceso a cámara)"""
    if os.path.exists(SSL_CERT) and os.path.exists(SSL_KEY):
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=HTTPS_PORT, 
            ssl_keyfile=SSL_KEY,
            ssl_certfile=SSL_CERT,
            log_level="warning"
        )


def main_app():
    global window, tray_icon
    
    # Generar certificado SSL si no existe
    ensure_ssl_certificate()
    
    # Configurar callback de minimizar
    main.minimize_callback = hide_window
    
    # Crear icono de bandeja
    tray_icon = create_tray_icon()
    
    # Iniciar servidores en hilos separados
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    https_thread = threading.Thread(target=run_https_server, daemon=True)
    https_thread.start()
    
    print(f"HTTP:  http://localhost:8001 (dashboard)")
    print(f"HTTPS: https://localhost:{HTTPS_PORT} (móvil)")
    
    # Dar tiempo a los servidores para iniciar
    import time
    time.sleep(1.5)

    # Crear ventana del dashboard
    window = webview.create_window(
        "Scanner Pipos Server",
        "http://localhost:8001/dashboard",
        width=950,
        height=680,
        resizable=True,
        min_size=(800, 550)
    )
    
    webview.start()


if __name__ == "__main__":
    main_app()
