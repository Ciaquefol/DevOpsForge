@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"
set "VENV_PY=%BACKEND%\.venv\Scripts\python.exe"

cd /d "%BACKEND%"
if errorlevel 1 (
    echo ERROR: Cannot find folder: %BACKEND%
    pause
    exit /b 1
)

REM --- Python venv ---
set "NEED_VENV=1"
if exist "%VENV_PY%" (
    "%VENV_PY%" -c "exit(0)" >nul 2>&1
    if not errorlevel 1 set "NEED_VENV=0"
)

if "%NEED_VENV%"=="1" (
    echo [DevOpsForge] Creating virtual environment...
    if exist ".venv" rmdir /s /q ".venv"
    py -3 -m venv .venv
    if errorlevel 1 (
        echo ERROR: Install Python 3.11+ from https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Cannot activate .venv
    pause
    exit /b 1
)

python -m ensurepip --upgrade >nul 2>&1
echo [DevOpsForge] Installing backend dependencies...
python -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo ERROR: pip install failed
    pause
    exit /b 1
)

REM --- 1) Backend first ---
echo [DevOpsForge] Starting backend...
start "DevOpsForge Backend" "%BACKEND%\run_dev.bat"

REM --- 2) Wait until :8000 answers (frontend was starting too early) ---
echo [DevOpsForge] Waiting for backend http://127.0.0.1:8000/health ...
set /a WAIT_COUNT=0

:wait_health
set /a WAIT_COUNT+=1
if %WAIT_COUNT% GTR 45 (
    echo WARNING: Backend did not respond in 90 sec. Starting frontend anyway.
    goto start_frontend
)

powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if %errorlevel%==0 (
    echo [DevOpsForge] Backend is ready.
    goto start_frontend
)

timeout /t 2 /nobreak >nul
goto wait_health

:start_frontend
echo [DevOpsForge] Starting frontend...
start "DevOpsForge Frontend" "%FRONTEND%\run_dev.bat"

echo.
echo ==========================================
echo   UI:      http://127.0.0.1:5173
echo   API:     http://127.0.0.1:8000/docs
echo   Health:  http://127.0.0.1:8000/health
echo ==========================================
echo.
pause
endlocal
