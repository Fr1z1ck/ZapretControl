import json
import os
from utils.paths import get_resource_path

class ConfigManager:
    def __init__(self):
        self.version = "1.1.8"
        self.config_path = os.path.join(os.environ.get('APPDATA', '.'), 'ZapretControl', 'config.json')
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        self.settings = {
            "last_strategy": "",
            "health_results": {}
        }
        self.load()

    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.settings.update(data)
            except Exception as e:
                print(f"Error loading config: {e}")

    def save(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save()

config = ConfigManager()
