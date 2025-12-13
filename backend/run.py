import os
import sys

# Ocultar ventana de consola en Windows (solo para .exe empaquetado)
if getattr(sys, 'frozen', False):
    try:
        import ctypes
        # Obtener handle de la ventana de consola
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        
        hWnd = kernel32.GetConsoleWindow()
        if hWnd:
            # SW_HIDE = 0, oculta la ventana
            user32.ShowWindow(hWnd, 0)
    except:
        pass

import threading
import uvicorn
import webview
from PIL import Image
import pystray

# Detectar si está corriendo desde PyInstaller bundle
if getattr(sys, 'frozen', False):
    # Corriendo desde .exe empaquetado
    bundle_dir = sys._MEIPASS
    current_dir = bundle_dir
    # En .exe, el SSL se genera en la carpeta del ejecutable
    exe_dir = os.path.dirname(sys.executable)
    SSL_DIR = os.path.join(exe_dir, "ssl")
    icon_path = os.path.join(bundle_dir, "frontend", "dist", "icon-192.png")
else:
    # Corriendo desde código fuente
    current_dir = os.path.dirname(os.path.abspath(__file__))
    SSL_DIR = os.path.join(current_dir, "ssl")
    icon_path = os.path.join(current_dir, "..", "frontend", "public", "icon-192.png")

sys.path.insert(0, current_dir)

from main import app, minimize_callback
import main

# Variables globales
window = None
tray_icon = None

# Configuración SSL
SSL_KEY = os.path.join(SSL_DIR, "key.pem")
SSL_CERT = os.path.join(SSL_DIR, "cert.pem")
HTTPS_PORT = 8443


def ensure_ssl_certificate():
    """Genera certificado SSL si no existe"""
    # Crear carpeta SSL si no existe
    os.makedirs(SSL_DIR, exist_ok=True)
    
    if os.path.exists(SSL_KEY) and os.path.exists(SSL_CERT):
        print(f"Certificado SSL encontrado en {SSL_DIR}")
        return True
    
    try:
        print(f"Generando certificado SSL en {SSL_DIR}...")
        # Generar certificado inline para el .exe
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from datetime import datetime, timedelta
        import ipaddress
        
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "AR"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Scanner Pipos"),
            x509.NameAttribute(NameOID.COMMON_NAME, "scanner-pipos.local"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365 * 10)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(key, hashes.SHA256(), default_backend())
        
        with open(SSL_KEY, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        with open(SSL_CERT, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        print(f"Certificado SSL generado correctamente")
        return True
    except Exception as e:
        print(f"Error generando certificado SSL: {e}")
        return False


def create_tray_icon():
    """Crea el icono de la bandeja del sistema"""
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
    else:
        print("ERROR: No se encontró certificado SSL para HTTPS")


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
    print(f"SSL Dir: {SSL_DIR}")
    
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
