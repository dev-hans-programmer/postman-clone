"""
Application Settings and Configuration Management
"""

import os
import json
import configparser
from pathlib import Path
from typing import Dict, Any, Optional

class AppSettings:
    """Manages application settings and configuration"""
    
    def __init__(self):
        self.app_dir = Path.home() / ".api_tester"
        self.config_file = self.app_dir / "config.ini"
        self.data_dir = self.app_dir / "data"
        
        # Ensure directories exist
        self.app_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        
        # Default settings
        self.defaults = {
            'appearance': {
                'theme': 'dark',
                'color_theme': 'blue',
                'font_size': '12',
                'window_width': '1200',
                'window_height': '800'
            },
            'network': {
                'timeout': '30',
                'verify_ssl': 'true',
                'max_redirects': '10'
            },
            'editor': {
                'auto_format_json': 'true',
                'syntax_highlighting': 'true',
                'word_wrap': 'true'
            }
        }
        
        self.config = configparser.ConfigParser()
        self.load_settings()
    
    def load_settings(self):
        """Load settings from configuration file"""
        if self.config_file.exists():
            try:
                self.config.read(self.config_file)
            except Exception as e:
                print(f"Error loading config: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration file"""
        for section, options in self.defaults.items():
            self.config[section] = options
        self.save_settings()
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, section: str, option: str, fallback: str = "") -> str:
        """Get a configuration value"""
        return self.config.get(section, option, fallback=fallback)
    
    def set(self, section: str, option: str, value: str):
        """Set a configuration value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][option] = value
    
    def get_bool(self, section: str, option: str, fallback: bool = False) -> bool:
        """Get a boolean configuration value"""
        return self.config.getboolean(section, option, fallback=fallback)
    
    def get_int(self, section: str, option: str, fallback: int = 0) -> int:
        """Get an integer configuration value"""
        return self.config.getint(section, option, fallback=fallback)
    
    @property
    def history_file(self) -> Path:
        """Path to request history file"""
        return self.data_dir / "history.json"
    
    @property
    def environments_file(self) -> Path:
        """Path to environments file"""
        return self.data_dir / "environments.json"
    
    @property
    def collections_file(self) -> Path:
        """Path to request collections file"""
        return self.data_dir / "collections.json"
