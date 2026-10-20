@echo off
cd /d "%~dp0"
set PORT=5055
py -3 server.py
if errorlevel 1 (
  echo.
  echo Nao foi possivel iniciar. Confira se Python 3 e Flask estao instalados.
  pause
)
