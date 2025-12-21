@echo off
setlocal enabledelayedexpansion
title Zapret Control Manager

:: Force UTF-8 encoding for console
chcp 65001 > nul

:MENU
cls
echo ==================================================
echo              ZAPRET CONTROL MANAGER
echo ==================================================
echo:
echo  [1] Install dependencies
echo  [2] Run Application
echo  [3] Build EXE
echo  [4] Cleanup
echo  [5] Exit
echo:
echo ==================================================
set /p choice="Select action [1-5]: "

if "%choice%"=="1" goto INSTALL
if "%choice%"=="2" goto RUN
if "%choice%"=="3" goto BUILD
if "%choice%"=="4" goto CLEANUP
if "%choice%"=="5" exit
goto MENU

:INSTALL
cls
echo [+] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    goto MENU
)

if not exist "venv" (
    echo [+] Creating virtual environment...
    python -m venv venv
)

echo [+] Installing requirements...
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo:
echo [+] Done!
pause
goto MENU

:RUN
cls
if not exist "venv" (
    echo [!] venv not found. Run Install first.
    pause
    goto MENU
)
echo [+] Starting Zapret Control...
call venv\Scripts\activate
start "" pythonw main.py
exit

:BUILD
cls
if not exist "venv" (
    echo [!] venv not found. Run Install first.
    pause
    goto MENU
)
echo [+] Activating environment...
call venv\Scripts\activate

echo [+] Cleaning old build files...
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"

echo [+] Running PyInstaller...
pyinstaller --clean ZapretControl.spec

echo:
if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
) else (
    echo [+] Build finished! Check dist/ folder.
)
pause
goto MENU

:CLEANUP
cls
echo [+] Cleaning up...
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist "ZapretControl.spec" del /f /q "ZapretControl.spec"
if exist "logs\app.log" del /f /q "logs\app.log"
echo [+] Done.
pause
goto MENU
