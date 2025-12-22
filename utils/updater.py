import requests
import os
import shutil
import urllib3
from utils.logger import logger
from core.config import config
from utils.paths import get_resource_path

# Disable SSL warnings for updates if needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
