# Scanner Pipos

Este proyecto convierte un dispositivo móvil en un escáner de códigos de barras para tu PC, actuando como una "pistola" lectora virtual. Utiliza una aplicación web para escanear y envía los códigos a la PC mediante WebSockets, escribiéndolos automáticamente donde esté el cursor (como un lector USB real).

## Requisitos Previos

Antes de instalar, asegúrate de tener instalados:

1.  **Python 3.8+**: [Descargar Python](https://www.python.org/downloads/) (Asegúrate de marcar "Add Python to PATH" durante la instalación).
2.  **Node.js**: [Descargar Node.js](https://nodejs.org/) (Versión LTS recomendada).

## Instalación Automática (Windows)

1.  Clona o descarga este repositorio.
2.  Haz doble clic en el archivo **`install.bat`**.
3.  Espera a que termine el proceso (instalará dependencias y construirá la aplicación).

## Cómo Usar

1.  Haz doble clic en **`start.bat`**.
2.  Se abrirá una ventana de comandos mostrando que el servidor está corriendo en `http://localhost:8000`.
3.  **En tu celular**:
    - Asegúrate de estar en la misma red Wi-Fi que tu PC.
    - Abre el navegador y ve a `http://<IP-DE-TU-PC>:8000`.
    - (Puedes ver la IP de tu PC ejecutando `ipconfig` en una terminal, es la IPv4).
4.  **En tu PC**:
    - Coloca el cursor donde quieras escribir el código (Excel, Sistema de ventas, Notepad, etc.).
    - Usa el celular para escanear un código de barras.
    - El código aparecerá escrito mágicamente en tu PC.

## Instalación Manual (Si falla el script)

### Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
npm run build
```

### Ejecutar

```bash
cd backend
# Asegúrate de tener el venv activado
uvicorn main:app --host 0.0.0.0 --port 8001
```
