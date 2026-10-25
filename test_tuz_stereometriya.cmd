@echo off
chcp 65001 >nul
title QANOT.AI - Stereometriya test tuzish
cd /d "%~dp0"
echo Docker konteynerlari tekshirilmoqda...
docker compose up -d db backend >nul 2>&1
if errorlevel 1 (
  echo.
  echo Docker ishlamayapti. Docker Desktop ni ishga tushirib, qayta urinib ko'ring.
  pause
  exit /b 1
)
docker compose exec backend python test_tuz_stereometriya.py %*
echo.
pause
