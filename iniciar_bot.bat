@echo off

cd /d "%~dp0\src"

echo ============================
echo INICIANDO BOT...
echo ============================

start "BOT" cmd /k py auto_run.py

timeout /t 2 >nul

echo ============================
echo INICIANDO DASHBOARD...
echo ============================

start "DASHBOARD" cmd /k py dashboard\app.py

pause