@echo off
setlocal enabledelayedexpansion
title Zapret Control Manager

:MENU
cls
echo ==================================================
echo              ZAPRET CONTROL MANAGER
echo ==================================================
echo:
echo  [1] Install dependencies
echo  [2] Run Application
echo  [3] Build EXE
echo  [4] Git Push (Update Repo)
echo  [5] Git Release (Build + Tag + Push)
echo  [6] Cleanup
echo  [7] Exit
echo:
echo ==================================================
set /p choice="Select action [1-7]: "

if "%choice%"=="1" goto INSTALL
if "%choice%"=="2" goto RUN
if "%choice%"=="3" goto BUILD
if "%choice%"=="4" goto GIT_PUSH
if "%choice%"=="5" goto GIT_RELEASE
if "%choice%"=="6" goto CLEANUP
if "%choice%"=="7" exit
goto MENU

:INSTALL
cls
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found!
    pause
    goto MENU
)
if not exist "venv" (
    echo [+] Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
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
call venv\Scripts\activate
start "" pythonw main.py
exit

:BUILD
cls
if not exist "venv" (
    echo [!] venv not found.
    pause
    goto MENU
)
call venv\Scripts\activate
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
python -m PyInstaller --clean ZapretControl.spec
if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
) else (
    echo [+] Build finished! Check dist/ folder.
)
pause
goto MENU

:GIT_PUSH
cls
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git not found!
    pause
    goto MENU
)
set "msg="
set /p msg="Enter commit message (or press Enter for default): "
if "!msg!"=="" set "msg=Update application"

echo [+] Adding files...
git add .
echo [+] Status:
git status -s

:: Check if user identity is set
git config user.email >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Git user identity not set.
    set /p uemail="Enter your GitHub email: "
    set /p uname="Enter your GitHub username: "
    if not "!uemail!"=="" git config user.email "!uemail!"
    if not "!uname!"=="" git config user.name "!uname!"
)

echo [+] Committing with message: !msg!
git commit -m "!msg!"
if errorlevel 1 (
    echo [WARNING] Nothing to commit or commit failed.
)
echo [+] Pushing to origin main...
git push origin main
pause
goto MENU

:GIT_RELEASE
cls
echo [+] Starting Release Mode...
echo [+] Step 1: Checking Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed or not in PATH.
    pause
    goto MENU
)

echo [+] Step 2: Checking GitHub CLI (gh)...
gh --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] GitHub CLI (gh) is not installed.
    echo Please install it from https://cli.github.com/
    pause
    goto MENU
)

echo [+] Step 3: Checking GitHub Authorization...
gh auth status >nul 2>&1
if errorlevel 1 (
    echo [ERROR] You are not logged into GitHub CLI.
    echo Please run 'gh auth login' in a separate terminal.
    pause
    goto MENU
)

echo [+] Step 4: Fetching tags...
echo --------------------------------------------------
git tag -l
echo --------------------------------------------------
echo:

set "rtag="
set /p rtag="Enter version tag (e.g. v1.1.0) or press Enter to cancel: "
if "!rtag!"=="" (
    echo [+] Release cancelled.
    pause
    goto MENU
)

echo [+] Step 5: Checking if tag '!rtag!' already exists...
git rev-parse "!rtag!" >nul 2>&1
if errorlevel 1 (
    echo [+] Tag '!rtag!' is available.
) else (
    echo [ERROR] Tag '!rtag!' already exists. Please use a new version.
    pause
    goto MENU
)

echo [+] Step 6: Building EXE...
if not exist "venv" (
    echo [ERROR] Virtual environment (venv) not found.
    pause
    goto MENU
)

:: Ensure we are in the right environment
call venv\Scripts\activate
python -m PyInstaller --clean ZapretControl.spec
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    pause
    goto MENU
)

if not exist "dist\ZapretControl.exe" (
    echo [ERROR] Build succeeded but ZapretControl.exe not found in dist/
    pause
    goto MENU
)

echo [+] Step 7: Committing and Tagging...
git add .

:: Check if user identity is set
git config user.email >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Git user identity not set.
    set /p uemail="Enter your GitHub email: "
    set /p uname="Enter your GitHub username: "
    if not "!uemail!"=="" git config user.email "!uemail!"
    if not "!uname!"=="" git config user.name "!uname!"
)

:: Ignore error if nothing to commit
git commit -m "Release !rtag!" >nul 2>&1
git tag -a "!rtag!" -m "Version !rtag!"
if errorlevel 1 (
    echo [ERROR] Failed to create git tag. Maybe it already exists locally?
    pause
    goto MENU
)

echo [+] Step 8: Pushing to GitHub...
git push origin main --tags
if errorlevel 1 (
    echo [ERROR] Failed to push to GitHub. Check your internet connection or permissions.
    pause
    goto MENU
)

echo [+] Step 9: Creating GitHub Release and uploading EXE...
gh release create "!rtag!" "dist\ZapretControl.exe" --title "Release !rtag!" --notes "Automated release !rtag!"
if errorlevel 1 (
    echo [ERROR] Failed to create GitHub release. 
    echo You might need to delete the tag manually: git tag -d !rtag!
) else (
    echo [+] SUCCESS: Release !rtag! created and EXE uploaded.
)

pause
goto MENU

:CLEANUP
cls
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist "logs\app.log" del /f /q "logs\app.log"
echo [+] Done.
pause
goto MENU
