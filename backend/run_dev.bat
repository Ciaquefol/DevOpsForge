@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: .venv not found. Run start_all.bat from project root.
    pause
    exit /b 1
)
call ".venv\Scripts\activate.bat"
echo Backend: http://127.0.0.1:8000/docs
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
