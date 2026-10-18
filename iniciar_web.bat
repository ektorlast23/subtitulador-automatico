@echo off
setlocal
cd /d "%~dp0"

if not defined HF_HOME set HF_HOME=H:\hf_cache
set SUBTITULADOR_ASR=whisper
set SUBTITULADOR_TRANSLATOR=marian

set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=H:\subtitulador-venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo ============================================
echo  Subtitulador automatico EN - ES
echo  Python: %PY%
echo  Abriendo http://127.0.0.1:8010 ...
echo  (Para detener: cierra esta ventana o Ctrl+C)
echo ============================================
echo.

start "" cmd /c "timeout /t 3 >nul & start "" http://127.0.0.1:8010"

"%PY%" -m uvicorn subtitulador.web:app --host 127.0.0.1 --port 8010

echo.
echo Servidor detenido.
pause
