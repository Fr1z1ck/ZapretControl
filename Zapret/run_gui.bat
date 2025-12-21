@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================
echo   Zapret GUI Launcher
echo ========================================
echo.

:: Проверка Python
echo [1/3] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found
echo.

:: Проверка и установка зависимостей
echo [2/3] Checking dependencies...
python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo [INFO] customtkinter not found, installing dependencies...
    echo.
    
    :: Пробуем python -m pip
    python -m pip --version >nul 2>&1
    if not errorlevel 1 (
        echo Using: python -m pip
        python -m pip install -r requirements.txt
        if errorlevel 1 (
            echo.
            echo [ERROR] Failed to install dependencies using python -m pip
            echo.
            echo Try installing manually:
            echo   python -m pip install customtkinter
            echo.
            pause
            exit /b 1
        )
    ) else (
        :: Пробуем просто pip
        pip --version >nul 2>&1
        if not errorlevel 1 (
            echo Using: pip
            pip install -r requirements.txt
            if errorlevel 1 (
                echo.
                echo [ERROR] Failed to install dependencies using pip
                echo.
                echo Try installing manually:
                echo   pip install customtkinter
                echo.
                pause
                exit /b 1
            )
        ) else (
            echo.
            echo [ERROR] pip is not available
            echo.
            echo Please install pip or use:
            echo   python -m ensurepip --upgrade
            echo.
            pause
            exit /b 1
        )
    )
    echo [OK] Dependencies installed successfully
) else (
    echo [OK] Dependencies already installed
)
echo.

:: Запуск приложения с правами администратора
echo [3/3] Starting Zapret GUI with admin rights...
echo.

:: Пытаемся запустить с правами администратора
powershell -Command "Start-Process python -ArgumentList 'zapret_gui.py' -Verb RunAs -WorkingDirectory '%CD%'"

:: Если не получилось - запускаем обычным способом
if errorlevel 1 (
    echo Запуск с правами администратора не удался, запускаю обычным способом...
    python zapret_gui.py
)

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start GUI
    echo.
    echo Check if all dependencies are installed correctly:
    echo   python -m pip install customtkinter
    echo.
    pause
    exit /b 1
)

exit /b 0
