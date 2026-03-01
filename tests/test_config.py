"""Unit tests for canary.config module."""

import pytest
import json
import tempfile
from pathlib import Path
from canary.config import CanaryConfig


class TestCanaryConfig:
    """Test configuration management."""
    
    def test_config_initialization(self):
        """Test that config initializes with default values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CanaryConfig(tmpdir)
            assert config.config_dir == Path(tmpdir)
            assert config.config_file == Path(tmpdir) / "config.json"
    
    def test_config_creates_directory(self):
        """Test that config creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "subdir" / "canary"
            config = CanaryConfig(str(config_path))
            assert config_path.exists()
    
    def test_config_creates_json_file(self):
        """Test that config JSON file is created when saved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CanaryConfig(tmpdir)
            # File is created when save() is called
            config.save()
            assert config.config_file.exists()
            # Verify it's valid JSON
            with open(config.config_file, 'r') as f:
                data = json.load(f)
            assert "version" in data
            assert "monitored_files" in data
            assert "webhook_url" in data
    
    def test_default_config_structure(self):
        """Test that default config has correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CanaryConfig(tmpdir)
            assert config.data["version"] == 1
            assert isinstance(config.data["monitored_files"], list)
            assert config.data["webhook_url"] is None
    
    def test_add_file(self):
        """Test adding a file to monitoring list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CanaryConfig(tmpdir)
            result = config.add_file("/test/file1.txt")
            assert result is True
            assert "/test/file1.txt" in config.get_monitored_files()
    
    def test_add_duplicate_file(self):
        """Test that adding duplicate file returns False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CanaryConfig(tmpdir)
            config.add_file("/test/file1.txt")
            result = config.add_file("/test/file1.txt")
            assert result is False
            assert len(config.get_monitored_files()) == 1
    
    def test_add_multiple_files(self):
        """Test adding multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CanaryConfig(tmpdir)
            config.add_file("/test/file1.txt")
            config.add_file("/test/file2.txt")
            config.add_file("/test/file3.txt")
            files = config.get_monitored_files()
            assert len(files) == 3
            assert "/test/file1.txt" in files
            assert "/test/file2.txt" in files
            assert "/test/file3.txt" in files
    
    def test_remove_file(self):
        """Test removing a file from monitoring list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CanaryConfig(tmpdir)
            config.add_file("/test/file1.txt")
            config.add_file("/test/file2.txt")
            result = config.remove_file("/test/file1.txt")
            assert result is True
            assert "/test/file1.txt" not in config.get_monitored_files()
            assert "/test/file2.txt" in config.get_monitored_files()
    
    def test_remove_nonexistent_file(self):
        """Test that removing non-existent file returns False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CanaryConfig(tmpdir)
            result = config.remove_file("/nonexistent/file.txt")
            assert result is False
    
    def test_set_webhook_url(self):
        """Test setting webhook URL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CanaryConfig(tmpdir)
            config.set_webhook_url("https://example.com/webhook")
            assert config.get_webhook_url() == "https://example.com/webhook"
    
    def test_set_webhook_url_none(self):
        """Test clearing webhook URL by setting to None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CanaryConfig(tmpdir)
            config.set_webhook_url("https://example.com/webhook")
            config.set_webhook_url(None)
            assert config.get_webhook_url() is None
    
    def test_config_persistence(self):
        """Test that config is saved and reloaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and modify config
            config1 = CanaryConfig(tmpdir)
            config1.add_file("/test/file1.txt")
            config1.add_file("/test/file2.txt")
            config1.set_webhook_url("https://example.com/webhook")
            
            # Create new instance from same directory
            config2 = CanaryConfig(tmpdir)
            assert "/test/file1.txt" in config2.get_monitored_files()
            assert "/test/file2.txt" in config2.get_monitored_files()
            assert config2.get_webhook_url() == "https://example.com/webhook"
    
    def test_config_file_format(self):
        """Test that config file is valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CanaryConfig(tmpdir)
            config.add_file("/test/file.txt")
            config.set_webhook_url("https://example.com")
            
            # Read file directly and verify JSON format
            with open(config.config_file, 'r') as f:
                data = json.load(f)
            
            assert data["version"] == 1
            assert "/test/file.txt" in data["monitored_files"]
            assert data["webhook_url"] == "https://example.com"
    
    def test_get_monitored_files_empty(self):
        """Test getting monitored files when list is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CanaryConfig(tmpdir)
            files = config.get_monitored_files()
            assert isinstance(files, list)
            assert len(files) == 0
    
    def test_load_invalid_json_creates_default(self):
        """Test that invalid JSON creates default config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            # Write invalid JSON
            config_file.write_text("{ invalid json }")
            
            # Load config - should create default
            config = CanaryConfig(tmpdir)
            assert config.data["version"] == 1
            assert isinstance(config.data["monitored_files"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
