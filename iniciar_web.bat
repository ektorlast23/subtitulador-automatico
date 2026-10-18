@echo off
setlocal
title Subtitulador EN-ES
cd /d "%~dp0"

if not defined HF_HOME set HF_HOME=H:\hf_cache
set SUBTITULADOR_ASR=whisper
set SUBTITULADOR_TRANSLATOR=marian

set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=H:\subtitulador-venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 8010 -State Listen -ErrorAction SilentlyContinue) { exit 1 } else { exit 0 }"
if errorlevel 1 (
  echo ============================================
  echo  Ya hay un servidor corriendo en el puerto 8010.
  echo  Abriendo http://127.0.0.1:8010 ...
  echo ============================================
  start "" "http://127.0.0.1:8010"
  timeout /t 4 >nul
  exit /b 0
)

echo ============================================
echo  Subtitulador automatico EN - ES
echo  Python: %PY%
echo  Arrancando en http://127.0.0.1:8010 ...
echo.
echo  IMPORTANTE: deja esta ventana ABIERTA mientras lo usas.
echo  Para detener el servidor: cierra esta ventana o pulsa Ctrl+C.
echo ============================================
echo.

start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep 3; Start-Process 'http://127.0.0.1:8010'"

"%PY%" -m uvicorn subtitulador.web:app --host 127.0.0.1 --port 8010
set "CODE=%ERRORLEVEL%"

echo.
if not "%CODE%"=="0" (
  echo [ERROR] El servidor termino con codigo %CODE%.
  echo Revisa el mensaje de arriba. Causas tipicas:
  echo   - El puerto 8010 esta ocupado.
  echo   - Falta ffmpeg en el PATH.
  echo   - El entorno virtual no esta instalado.
) else (
  echo Servidor detenido.
)
pause
