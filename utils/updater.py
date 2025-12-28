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
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import hashlib

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
        self.session = self._get_session()

    def _get_session(self):
        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])
        s = requests.Session()
        s.mount("https://", HTTPAdapter(max_retries=retry))
        return s

    def check_for_updates(self):
        """Checks latest GitHub release tag and returns it as update ref."""
        try:
            url = f"{self.api_base}/releases/latest"
            response = self.session.get(url, timeout=10, verify=False)
            if response.status_code == 200:
                data = response.json()
                tag = data.get("tag_name") or ""
                tag = tag.lstrip("v")
                if not tag:
                    return False, None
                last_tag = config.get("last_update_version")
                return (tag != last_tag), tag
            else:
                logger.error(f"Failed to check for updates: {response.status_code}")
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
        return False, None

    def update_strategies(self, latest_hash=None, progress_callback=None):
        """Downloads updated .bat files and lists from the repository."""
        try:
            # Determine ref (release tag or fallback to main)
            ref = (latest_hash or "main")
            
            # 1. Update .bat files in root
            url = f"{self.api_base}/contents/?ref={ref}"
            response = self.session.get(url, timeout=10, verify=False)
            if response.status_code != 200:
                logger.error(f"Failed to get repo contents: {response.status_code}")
                return False

            files = response.json()
            bat_files = [f for f in files if (f.get("name", "").startswith("general") and f.get("name", "").endswith(".bat")) or f.get("name", "") == "service.bat"]
            
            # 2. Update list files in lists/ folder
            lists_url = f"{self.api_base}/contents/lists?ref={ref}"
            lists_response = self.session.get(lists_url, timeout=10, verify=False)
            list_files = []
            if lists_response.status_code == 200:
                list_files = lists_response.json()
            else:
                logger.warning(f"Failed to get lists folder contents: {lists_response.status_code}")

            # 3. Update .service files
            service_folder_url = f"{self.api_base}/contents/.service?ref={ref}"
            service_response = self.session.get(service_folder_url, timeout=10, verify=False)
            service_files = []
            if service_response.status_code == 200:
                service_files = service_response.json()
            
            all_files = []
            for f in bat_files:
                all_files.append((f, self.zapret_path))
            for f in list_files:
                all_files.append((f, os.path.join(self.zapret_path, "lists")))
            for f in service_files:
                all_files.append((f, os.path.join(self.zapret_path, ".service")))

            total_files = len(all_files)
            if total_files == 0:
                return True

            updated_count = 0
            failed = 0
            
            for i, (file_info, target_dir) in enumerate(all_files):
                name = file_info.get("name", "")
                if progress_callback:
                    progress_callback(i, total_files, name)
                
                os.makedirs(target_dir, exist_ok=True)
                
                # Construct correct download URL based on folder
                if target_dir == self.zapret_path:
                    download_url = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/{ref}/{name}"
                elif target_dir.endswith("lists"):
                    download_url = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/{ref}/lists/{name}"
                else: # .service
                    download_url = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/{ref}/.service/{name}"
                
                target_path = os.path.join(target_dir, name)
                
                # Download file
                file_response = self.session.get(download_url, timeout=10, verify=False)
                if file_response.status_code == 200:
                    content = file_response.content
                    # Basic sanity check
                    if len(content) > 10:
                        with open(target_path, 'wb') as f:
                            f.write(content)
                        updated_count += 1
                        logger.info(f"Updated: {name} in {os.path.basename(target_dir)}")
                    else:
                        logger.error(f"File {name} is too small, skipping")
                        failed += 1
                else:
                    failed += 1
                    logger.error(f"Failed to download {name}")

            if progress_callback:
                progress_callback(total_files, total_files, "Завершено")

            if updated_count > 0:
                if latest_hash:
                    config.set("last_update_version", latest_hash.lstrip("v"))
                    config.set("last_update_hash", latest_hash)
                logger.info(f"Successfully updated {updated_count} files.")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error during update: {e}")
        return False

    def download_runtime(self, ref="main", progress_callback=None):
        """Downloads runtime binaries (bin folder) for the given ref/tag."""
        try:
            bin_url = f"{self.api_base}/contents/bin?ref={ref}"
            response = self.session.get(bin_url, timeout=10, verify=False)
            if response.status_code != 200:
                logger.error(f"Failed to get bin contents: {response.status_code}")
                return False
            files = response.json()
            target_bin = os.path.join(self.zapret_path, "bin")
            os.makedirs(target_bin, exist_ok=True)
            
            total_files = len(files)
            ok = 0
            fail = 0
            for i, f in enumerate(files):
                name = f.get("name", "")
                if progress_callback:
                    progress_callback(i, total_files, name)
                raw_url = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/{ref}/bin/{name}"
                res = self.session.get(raw_url, timeout=15, verify=False)
                if res.status_code == 200:
                    content = res.content
                    expected_size = int(f.get("size", 0) or 0)
                    actual_size = len(content)
                    if expected_size and expected_size != actual_size:
                        logger.error(f"Integrity mismatch for {name} ({actual_size}/{expected_size})")
                        fail += 1
                        continue
                    # Basic sanity for exe
                    if name.lower().endswith(".exe") and actual_size < 100000:
                        logger.error(f"Unexpected small size for {name}")
                        fail += 1
                        continue
                    with open(os.path.join(target_bin, name), "wb") as out:
                        out.write(content)
                    ok += 1
                else:
                    logger.error(f"Failed to download {name} ({res.status_code})")
                    fail += 1
            if progress_callback:
                progress_callback(total_files, total_files, "Завершено")
            if ok > 0 and fail == 0:
                logger.info(f"Runtime downloaded: {ok} files.")
                return True
            logger.error(f"Runtime download incomplete: ok={ok}, fail={fail}")
            return False
        except Exception as e:
            logger.error(f"Error downloading runtime: {e}")
            return False

updater = StrategyUpdater()
app_updater = AppUpdater()
