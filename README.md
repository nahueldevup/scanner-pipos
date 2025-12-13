# Scanner Pipos

Este proyecto convierte un dispositivo móvil en un escáner de códigos de barras para tu PC, actuando como una "pistola" lectora virtual. Utiliza una aplicación web para escanear y envía los códigos a la PC mediante WebSockets, escribiéndolos automáticamente donde esté el cursor (como un lector USB real).

## Características

- Escanea códigos de barras con la cámara de tu móvil
- Dashboard de escritorio con código QR para conectar fácilmente
- Contador de escáneres conectados en tiempo real
- Log de escaneos recientes
- Conexión HTTPS segura (para acceso a cámara)
- Minimizar a bandeja del sistema
- Inicio automático con Windows (opcional)

---

## Opción 1: Ejecutable (Recomendado para usuarios)

Si solo quieres usar la aplicación sin instalar nada:

1. Descarga `ScannerPipos.exe` desde los [Releases](../../releases)
2. Ejecuta el archivo
3. Escanea el código QR con tu móvil
4. ¡Listo! Los códigos se escribirán donde tengas el cursor

> **Nota**: La primera vez que escanees el QR, tu móvil mostrará una advertencia de seguridad. Acepta para continuar.

---

## Opción 2: Desde Código Fuente (Para desarrolladores)

### Requisitos Previos

- **Python 3.8+**: [Descargar Python](https://www.python.org/downloads/)
- **Node.js**: [Descargar Node.js](https://nodejs.org/)

### Instalación Automática (Windows)

1. Clona o descarga este repositorio
2. Ejecuta **`install.bat`**
3. Ejecuta **`start.bat`**

### Instalación Manual

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
npm run build

# Ejecutar
cd ../backend
python run.py
```

---

## Compilar Ejecutable

Para crear el archivo `.exe`:

```bash
# Instalar PyInstaller
pip install pyinstaller

# Compilar
pyinstaller ScannerPipos.spec --noconfirm
```

El ejecutable estará en `dist/ScannerPipos.exe`

---

## Uso

1. **En tu PC**: Ejecuta la aplicación (aparece el dashboard con código QR)
2. **En tu móvil**: Escanea el QR con la cámara
3. **Acepta la advertencia** de seguridad (solo la primera vez)
4. **Escanea códigos** y se escribirán donde tengas el cursor en la PC

## Notas Técnicas

- El servidor corre en HTTPS (puerto 8443) para acceso a cámara
- Los certificados SSL se generan automáticamente en `%APPDATA%\ScannerPipos\ssl`
- La configuración de inicio automático se guarda en el registro de Windows
