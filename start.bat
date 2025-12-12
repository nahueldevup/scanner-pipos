@echo off
echo ===========================================
echo   Iniciando Scanner Pipos
echo ===========================================
echo.

if not exist backend\venv (
    echo [ERROR] No se detecto el entorno virtual.
    echo Por favor ejecuta install.bat primero.
    pause
    exit /b
)

if not exist frontend\dist (
    echo [WARNING] No se detecto el build del frontend.
    echo La aplicacion web podria no verse. Se recomienda ejecutar install.bat.
    timeout /t 3
)

cd backend
call venv\Scripts\activate
echo Iniciando servidor en http://localhost:8001 ...
echo Presiona Ctrl+C para detener el servidor.
echo.
REM Usamos el ejecutable directo para evitar problemas de PATH
venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8001 --reload
pause
