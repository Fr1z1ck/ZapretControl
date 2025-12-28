import os
import requests
import time
import urllib3

# Disable SSL warnings for health checks
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from core.process_manager import ProcessManager
from core.services import get_services, get_strategies
from core.config import config
from utils.logger import logger
from utils.paths import get_resource_path
from utils.updater import updater, app_updater

class AppController:
    def __init__(self, base_path):
        self.base_path = base_path
        self.version = config.version
        # Use the provided Zapret folder
        self.zapret_path = get_resource_path("Zapret")
        self.bin_path = os.path.join(self.zapret_path, "bin")
        self.lists_path = os.path.join(self.zapret_path, "lists")
        
        self.process_manager = ProcessManager(self.bin_path)
        self.services = get_services(self.lists_path)
        self.strategies = get_strategies(self.zapret_path)
        
        # All services enabled by default, no UI toggles anymore
        self.enabled_services = {service.name: True for service in self.services}
        
        # Load last strategy
        last_strategy_name = config.get("last_strategy", "")
        self.current_strategy_index = 0
        if last_strategy_name:
            for i, s in enumerate(self.strategies):
                if s.name == last_strategy_name:
                    self.current_strategy_index = i
                    break
                    
        self.is_active = False
        
        # Health check results: {strategy_name: {"youtube": bool, "discord": bool}}
        # Changed to use name as key for better persistence across updates
        self.health_results = config.get("health_results", {})
        self.tray = None

    def set_strategy(self, index):
        if 0 <= index < len(self.strategies):
            self.current_strategy_index = index
            strategy_name = self.strategies[index].name
            logger.info(f"Strategy changed to: {strategy_name}")
            config.set("last_strategy", strategy_name)
            if self.is_active:
                self.start()

    def reset_health_results(self):
        self.health_results = {}
        config.set("health_results", {})
        logger.info("Health results reset.")

    def start(self, strategy_override=None):
        active_configs = [s for s in self.services if self.enabled_services.get(s.name)]
        if not active_configs:
            logger.warning("No services enabled. Nothing to start.")
            return False
            
        strategy = strategy_override or self.strategies[self.current_strategy_index]
        if self.process_manager.start(active_configs, strategy, self.lists_path):
            if strategy_override is None:
                self.is_active = True
            return True
        return False

    def stop(self):
        if self.process_manager.stop():
            self.is_active = False
            return True
        return False

    def check_for_updates(self):
        return updater.check_for_updates()

    def check_for_app_updates(self):
        return app_updater.check_for_updates()

    def download_app_update(self, progress_callback=None):
        return app_updater.download_and_install(progress_callback)

    def update_strategies(self, latest_hash, progress_callback=None):
        success = updater.update_strategies(latest_hash, progress_callback)
        if success:
            # Reload strategies after update
            self.strategies = get_strategies(self.zapret_path)
        return success

    def get_status(self):
        # Double check if process is actually running
        running = self.process_manager.is_running()
        if not running and self.is_active:
            self.is_active = False
            logger.warning("Process died unexpectedly.")
        return running

    def check_health(self, progress_callback=None, strategy_index=None):
        """Checks strategies for YouTube and Discord availability."""
        results = self.health_results.copy()
        original_active = self.is_active
        original_strategy = self.current_strategy_index
        
        # Stop current bypass to start tests
        self.stop()
        
        urls = {
            "youtube": "https://www.youtube.com",
            "discord": "https://discord.com"
        }
        
        # Determine which strategies to check
        if strategy_index is not None:
            indices_to_check = [strategy_index]
        else:
            indices_to_check = list(range(len(self.strategies)))
            
        total = len(indices_to_check)
        for i, idx in enumerate(indices_to_check):
            strategy = self.strategies[idx]
            if progress_callback:
                progress_callback(i, total, strategy.name)
            
            logger.info(f"Health checking strategy: {strategy.name}")
            
            # 1. Start strategy
            if not self.start(strategy_override=strategy):
                results[strategy.name] = {"youtube": False, "discord": False}
                continue
            
            # Wait for process to initialize
            time.sleep(2)
            
            res = {"youtube": False, "discord": False}
            for site, url in urls.items():
                try:
                    response = requests.get(url, timeout=5, verify=False)
                    if response.status_code == 200:
                        res[site] = True
                except Exception:
                    pass
            
            results[strategy.name] = res
            self.health_results = results.copy()
            config.set("health_results", self.health_results)
            self.stop()
        
        # Restore original state
        if original_active:
            self.current_strategy_index = original_strategy
            self.start()
            
        return results
