"""
Configuration management module
Handles loading and saving application settings
"""
import os
import json
import logging
from typing import Dict, Any


class Config:
    DEFAULT_CONFIG = {
        'last_host': '8.8.8.8',
        'last_interval': 2,
        'max_log_lines': 1000,
        'max_log_size': 1024 * 1024,  # 1 MB
        'max_log_files': 5
    }

    def __init__(self, config_file: str = 'ping_monitor_config.json'):
        self.config_file = config_file
        self.settings: Dict[str, Any] = self.DEFAULT_CONFIG.copy()
        self.load()

    def load(self) -> None:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    self.settings.update(loaded_config)
        except Exception as e:
            logging.warning(f"Error loading configuration: {e}")

    def save(self) -> bool:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            return True
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self.settings[key] = value

    def update(self, new_settings: Dict[str, Any]) -> None:
        """Update multiple settings at once"""
        self.settings.update(new_settings)
