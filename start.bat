@echo off
setlocal EnableExtensions
chcp 65001 >nul

rem ASCII-only starter to avoid BOM/encoding issues in CMD
cd /d "%~dp0"

rem Check Python in PATH
python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found in PATH. Install Python 3.8+ and try again.
  pause
  exit /b 1
)

rem Ensure dependencies (best effort)
pip install -r requirements.txt >nul 2>&1

rem Open browser to the app
start "" "http://localhost:5050"

rem Start Flask server in a dedicated window
start "Flask Server" cmd /k "python app.py"

exit /b 0
