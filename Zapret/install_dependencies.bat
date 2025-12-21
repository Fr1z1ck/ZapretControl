@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================
echo   Zapret GUI - Install Dependencies
echo ========================================
echo.

:: Проверка Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
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

:: Установка зависимостей
echo Installing dependencies from requirements.txt...
echo.

:: Пробуем python -m pip
python -m pip --version >nul 2>&1
if not errorlevel 1 (
    echo Using: python -m pip install -r requirements.txt
    echo.
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Installation failed
        echo.
        echo Try upgrading pip first:
        echo   python -m pip install --upgrade pip
        echo   python -m pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
) else (
    :: Пробуем просто pip
    pip --version >nul 2>&1
    if not errorlevel 1 (
        echo Using: pip install -r requirements.txt
        echo.
        pip install -r requirements.txt
        if errorlevel 1 (
            echo.
            echo [ERROR] Installation failed
            echo.
            echo Try upgrading pip first:
            echo   pip install --upgrade pip
            echo   pip install -r requirements.txt
            echo.
            pause
            exit /b 1
        )
    ) else (
        echo.
        echo [ERROR] pip is not available
        echo.
        echo Try installing pip:
        echo   python -m ensurepip --upgrade
        echo.
        echo Or download get-pip.py from:
        echo https://bootstrap.pypa.io/get-pip.py
        echo.
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo   Installation completed successfully!
echo ========================================
echo.
echo You can now run the GUI using:
echo   run_gui.bat
echo   or
echo   python zapret_gui.py
echo.
pause


