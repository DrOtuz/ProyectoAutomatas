@echo off
rem Abre el simulador. La primera vez crea el entorno e instala lo necesario (necesita internet).
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
    echo No se encontro Python. Instala Python 3.11 o superior desde https://www.python.org/downloads/
    echo y marca "Add python.exe to PATH" durante la instalacion.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creando el entorno virtual...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo No se pudo crear el entorno virtual. Revisa que tengas Python 3.11 o superior.
        pause
        exit /b 1
    )
)

echo Comprobando dependencias...
".venv\Scripts\python.exe" -m pip install --quiet -e .
if errorlevel 1 (
    echo No se pudieron instalar las dependencias. Revisa tu conexion a internet y que Python sea 3.11 o superior.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m simulador
if errorlevel 1 pause
