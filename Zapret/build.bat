@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================
echo   Zapret GUI - Build Executable
echo ========================================
echo.

:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Установка зависимостей для сборки
echo [1/2] Installing build dependencies...
python -m pip install -r requirements_build.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

:: Сборка
echo.
echo [2/2] Building executable...
python build_exe.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build completed!
echo ========================================
echo.
echo Executable file: dist\ZapretGUI.exe
echo.
pause



