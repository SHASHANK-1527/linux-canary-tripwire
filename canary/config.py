"""
Configuration management for Canary.

Handles loading, saving, and managing the configuration.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any


class CanaryConfig:
    """Manages Canary configuration."""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize the configuration handler.
        
        Args:
            config_dir: Directory for configuration files (default: ~/.canary)
        """
        if config_dir is None:
            config_dir = str(Path.home() / ".canary")
        
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_dir()
        self._load_config()
    
    def _ensure_config_dir(self) -> None:
        """Create config directory if it doesn't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> None:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self.data = self._default_config()
        else:
            self.data = self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "version": 1,
            "monitored_files": [],
            "webhook_url": None
        }
    
    def save(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.data, f, indent=2)
        except (OSError, IOError) as e:
            print(f"Error saving config: {e}")
    
    def add_file(self, file_path: str) -> bool:
        """
        Add a file to the monitored list.
        
        Args:
            file_path: Absolute path to file
            
        Returns:
            True if added, False if already exists
        """
        if file_path not in self.data["monitored_files"]:
            self.data["monitored_files"].append(file_path)
            self.save()
            return True
        return False
    
    def remove_file(self, file_path: str) -> bool:
        """
        Remove a file from the monitored list.
        
        Args:
            file_path: Path to file to remove
            
        Returns:
            True if removed, False if not found
        """
        if file_path in self.data["monitored_files"]:
            self.data["monitored_files"].remove(file_path)
            self.save()
            return True
        return False
    
    def get_monitored_files(self) -> List[str]:
        """
        Get list of monitored files.
        
        Returns:
            List of absolute file paths
        """
        return self.data.get("monitored_files", [])
    
    def set_webhook_url(self, url: Optional[str]) -> None:
        """
        Set or clear the webhook URL.
        
        Args:
            url: Webhook URL or None to disable
        """
        self.data["webhook_url"] = url
        self.save()
    
    def get_webhook_url(self) -> Optional[str]:
        """
        Get the configured webhook URL.
        
        Returns:
            Webhook URL or None
        """
        return self.data.get("webhook_url")
