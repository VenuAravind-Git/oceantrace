@echo off
title OCEANTRACE Tactical Surveillance Platform
cd /d "%~dp0"

echo ================================================================
echo   Launching OCEANTRACE - Maritime Oil Spill & Vessel Attribution
echo ================================================================

:: Check for Python 3.11 direct executable
if exist "C:\Users\pritam kumar\AppData\Local\Programs\Python\Python311\python.exe" (
    set "PY_CMD=C:\Users\pritam kumar\AppData\Local\Programs\Python\Python311\python.exe"
    goto RUN
)

:: Fallback to python in PATH
where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto RUN
)

:: Fallback to py launcher
where py >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto RUN
)

echo [ERROR] Python was not found. Please verify Python is installed.
pause
exit /b 1

:RUN
echo Using Python at: "%PY_CMD%"
"%PY_CMD%" run.py
pause
