@echo off
setlocal
chcp 65001 >nul
cd /d %~dp0

if not exist .venv (
  echo [!] 找不到 .venv，請先執行 install.bat
  pause
  exit /b 1
)

call .venv\Scripts\activate

echo [*] 檢查資料庫連線與資料表 ...
python check_db.py

pause
