@echo off
echo ===========================================
echo   Instalador de Scanner Pipos
echo ===========================================
echo.

REM Verificaciones previas
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo Por favor instala Python desde python.org y marca "Add Python to PATH"
    pause
    exit /b
)

npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js no esta instalado o no esta en el PATH.
    echo Por favor instala Node.js desde nodejs.org
    pause
    exit /b
)

echo [1/3] Configurando Backend (Python)...
cd backend
if not exist venv (
    echo Creando entorno virtual...
    python -m venv venv
)
REM Usamos ruta directa para evitar depender de activate
venv\Scripts\python.exe -m pip install -r requirements.txt
cd ..

echo.
echo [2/3] Configurando Frontend (Node.js)...
cd frontend
echo Instalando dependencias del frontend...
call npm install
echo Construyendo aplicacion frontend...
call npm run build
cd ..

echo.
echo [3/3] Instalacion completada!
echo ===========================================
echo Ahora puedes iniciar la aplicacion ejecutando: start.bat
echo ===========================================
pause
