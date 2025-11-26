"""
Configuration Module
Handles loading and saving application settings
"""

import json
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """Manages application configuration persistence"""

    def __init__(self, config_file: Path = None):
        """
        Initialize config manager

        Args:
            config_file: Path to config file (default: ~/.spotdl_gui_config.json)
        """
        self.config_file = config_file or (Path.home() / ".spotdl_gui_config.json")
        self.settings = self.load_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        """
        Get default settings

        Returns:
            Dictionary of default settings
        """
        return {
            "format": "mp3",
            "bitrate": "320k",
            "playlist_output": "{list-name}/{list-position} - {artists} - {title}.{output-ext}",
            "threads": "4",
            "output": "{album-artist}/{year} - {album}/{track-number} - {title}.{output-ext}",
            "download_folder": str(Path.home() / "Music"),
            "create_folder_per_url": True,
            "auto_download": True,
            "auto_clear_completed": False
        }

    def load_settings(self) -> Dict[str, Any]:
        """
        Load settings from config file

        Returns:
            Dictionary of settings (merged with defaults)
        """
        default_settings = self.get_default_settings()

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to handle new settings
                    return {**default_settings, **loaded_settings}
            except Exception as e:
                print(f"Warning: Failed to load settings: {e}")
                return default_settings
        else:
            return default_settings

    def save_settings(self, settings: Dict[str, Any] = None) -> bool:
        """
        Save settings to config file

        Args:
            settings: Settings dictionary to save (if None, uses internal settings)

        Returns:
            True if successful, False otherwise
        """
        if settings is not None:
            self.settings = settings

        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error: Failed to save settings: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value

        Args:
            key: Setting key
            default: Default value if key not found

        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        """
        Set a setting value

        Args:
            key: Setting key
            value: Setting value
        """
        self.settings[key] = value

    def update(self, updates: Dict[str, Any]):
        """
        Update multiple settings at once

        Args:
            updates: Dictionary of settings to update
        """
        self.settings.update(updates)
