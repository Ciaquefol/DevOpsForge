@echo off
setlocal
cd /d "%~dp0"

set "VENV_PY=.venv\Scripts\python.exe"
if not exist "%VENV_PY%" goto create_venv
"%VENV_PY%" -c "exit(0)" >nul 2>&1
if errorlevel 1 goto create_venv
goto run

:create_venv
echo Recreating .venv...
if exist ".venv" rmdir /s /q ".venv"
py -3 -m venv .venv
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+
    pause
    exit /b 1
)

:run
call ".venv\Scripts\activate.bat"
python -m ensurepip --upgrade >nul 2>&1
python -m pip install -r requirements.txt -q
call "%~dp0run_dev.bat"
endlocal
