import requests
import os
import shutil
import urllib3
import sys
import subprocess
import tempfile
import zipfile
from utils.logger import logger
from core.config import config
from utils.paths import get_resource_path

# Disable SSL warnings for updates if needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AppUpdater:
    def __init__(self):
        self.repo_owner = "Fr1z1ck"
        self.repo_name = "ZapretControl"
        self.api_base = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        self.current_version = config.version

    def check_for_updates(self):
        """Checks for a new release on GitHub."""
        try:
            url = f"{self.api_base}/releases/latest"
            response = requests.get(url, timeout=10, verify=False)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("tag_name", "").lstrip('v')
                if not latest_version:
                    return False, None, None

                if self._is_newer(latest_version, self.current_version):
                    return True, latest_version, data.get("html_url")
            else:
                logger.error(f"Failed to check for app updates: {response.status_code}")
        except Exception as e:
            logger.error(f"Error checking for app updates: {e}")
        return False, None, None

    def _is_newer(self, latest, current):
        try:
            l_parts = [int(p) for p in latest.split('.')]
            c_parts = [int(p) for p in current.split('.')]
            return l_parts > c_parts
        except:
            return latest != current

    def download_and_install(self, progress_callback=None):
        """Downloads the latest release and prepares for installation."""
        try:
            url = f"{self.api_base}/releases/latest"
            response = requests.get(url, timeout=10, verify=False)
            if response.status_code != 200:
                return False

            data = response.json()
            assets = data.get("assets", [])
            
            # Look for an EXE asset first if we are running as EXE
            is_frozen = getattr(sys, 'frozen', False)
            download_url = None
            
            if is_frozen:
                for asset in assets:
                    if asset.get("name", "").endswith(".exe"):
                        download_url = asset.get("browser_download_url")
                        break
            
            # If no EXE or not frozen, download source zip
            if not download_url:
                download_url = data.get("zipball_url")

            if not download_url:
                return False

            # Download to temp file
            if progress_callback: progress_callback(0, 100, "Скачивание...")
            
            temp_dir = tempfile.gettempdir()
            download_path = os.path.join(temp_dir, "zapret_update.zip" if download_url.endswith(".zip") or "zipball" in download_url else "zapret_update.exe")
            
            res = requests.get(download_url, stream=True, verify=False)
            total_size = int(res.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in res.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            progress_callback(percent, 100, f"Скачивание: {percent}%")

            if progress_callback: progress_callback(100, 100, "Подготовка к установке...")
            
            self._create_updater_script(download_path, is_frozen)
            return True

        except Exception as e:
            logger.error(f"Error downloading update: {e}")
            return False

    def _create_updater_script(self, download_path, is_frozen):
        """Creates a batch script to replace files and restart the app."""
        # Use sys.executable to get the real path to the EXE
        app_path = os.path.abspath(sys.executable if is_frozen else sys.argv[0])
        app_name = os.path.basename(app_path)
        script_path = os.path.join(tempfile.gettempdir(), "zapret_updater.bat")
        
        logger.info(f"Creating updater script. App path: {app_path}, Download path: {download_path}")
        
        with open(script_path, "w", encoding="cp1251") as f:
            f.write("@echo off\n")
            f.write("title ZapretControl Updater\n")
            f.write("echo ==================================================\n")
            f.write("echo             ZapretControl Auto-Updater\n")
            f.write("echo ==================================================\n")
            f.write("echo.\n")
            f.write("echo Waiting for application to exit...\n")
            f.write("timeout /t 3 /nobreak > nul\n")
            
            # Force kill the process just in case
            f.write(f'taskkill /F /IM "{app_name}" /T > nul 2>&1\n')
            
            if is_frozen and download_path.endswith(".exe"):
                f.write("echo Updating executable...\n")
                f.write(":retry_move\n")
                # Use copy /y instead of move for cross-volume compatibility, then delete source
                f.write(f'copy /y "{download_path}" "{app_path}" > nul\n')
                f.write("if errorlevel 1 (\n")
                f.write("    echo [!] File is locked or access denied. Retrying in 2 seconds...\n")
                f.write("    timeout /t 2 /nobreak > nul\n")
                f.write("    goto retry_move\n")
                f.write(")\n")
                f.write("echo [OK] Update successful!\n")
                f.write(f'del /f /q "{download_path}" > nul 2>&1\n')
                f.write("echo Starting new version...\n")
                f.write(f'start "" "{app_path}"\n')
            else:
                # For source code (ZIP)
                f.write(f'explorer /select,"{download_path}"\n')
                f.write("echo --------------------------------------------------\n")
                f.write(f"echo Update downloaded to: {download_path}\n")
                f.write("echo Please extract the contents of the ZIP archive\n")
                f.write(f"echo to the application folder: {os.path.dirname(app_path)}\n")
                f.write("echo --------------------------------------------------\n")
                f.write("pause\n")
            
            f.write("echo Done! Cleaning up...\n")
            f.write("del %0\n")
        
        # Run the script and exit
        logger.info(f"Launching updater script: {script_path}")
        subprocess.Popen([script_path], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
        os._exit(0)

class StrategyUpdater:
    def __init__(self):
        self.repo_owner = "Flowseal"
        self.repo_name = "zapret-discord-youtube"
        self.api_base = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        self.raw_base = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/main"
        self.zapret_path = get_resource_path("Zapret")

    def check_for_updates(self):
        """Checks if there is a new commit on the main branch."""
        try:
            url = f"{self.api_base}/commits/main"
            response = requests.get(url, timeout=10, verify=False)
            if response.status_code == 200:
                latest_hash = response.json().get("sha")
                current_hash = config.get("last_update_hash")
                return latest_hash != current_hash, latest_hash
            else:
                logger.error(f"Failed to check for updates: {response.status_code}")
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
        return False, None

    def update_strategies(self, latest_hash=None, progress_callback=None):
        """Downloads updated .bat files from the repository."""
        try:
            # 1. Get the list of files in the repo
            url = f"{self.api_base}/contents/"
            response = requests.get(url, timeout=10, verify=False)
            if response.status_code != 200:
                logger.error(f"Failed to get repo contents: {response.status_code}")
                return False

            files = response.json()
            
            # Filter relevant files
            files_to_update = [f for f in files if (f.get("name", "").startswith("general") and f.get("name", "").endswith(".bat")) or f.get("name", "") == "service.bat"]
            total_files = len(files_to_update)
            
            if total_files == 0:
                return True

            updated_count = 0
            for i, file_info in enumerate(files_to_update):
                name = file_info.get("name", "")
                
                if progress_callback:
                    progress_callback(i, total_files, name)
                
                download_url = f"{self.raw_base}/{name}"
                target_path = os.path.join(self.zapret_path, name)
                
                # Backup existing file
                if os.path.exists(target_path):
                    shutil.copy2(target_path, target_path + ".bak")
                
                # Download new file
                file_response = requests.get(download_url, timeout=10, verify=False)
                if file_response.status_code == 200:
                    with open(target_path, 'wb') as f:
                        f.write(file_response.content)
                    updated_count += 1
                    logger.info(f"Updated: {name}")
                else:
                    logger.error(f"Failed to download {name}")

            if progress_callback:
                progress_callback(total_files, total_files, "Завершено")

            if updated_count > 0:
                if latest_hash:
                    config.set("last_update_hash", latest_hash)
                logger.info(f"Successfully updated {updated_count} strategy files.")
                return True
            
        except Exception as e:
            logger.error(f"Error during update: {e}")
        return False

updater = StrategyUpdater()
app_updater = AppUpdater()
