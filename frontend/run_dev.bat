@echo off
cd /d "%~dp0"
if not exist "node_modules" (
    echo Installing npm packages...
    call npm install
)
echo.
echo Frontend URLs - try BOTH if one does not open:
echo   http://127.0.0.1:5173
echo   http://localhost:5173
echo.
echo Backend must be running: http://127.0.0.1:8000/health
echo.
call npm run dev
pause
