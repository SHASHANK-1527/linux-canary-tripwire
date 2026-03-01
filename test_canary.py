#!/usr/bin/env python3
"""
Test script for Canary components.
Verifies all modules work correctly.
"""

import sys
import tempfile
import json
from pathlib import Path

# Add the project to path
sys.path.insert(0, '/home/kali/Project_Canary_file')

from canary.config import CanaryConfig
from canary.logger import CanaryLogger
from canary.notifier import CanaryNotifier
from canary.utils import compute_sha256, get_current_user, resolve_absolute_path

def test_utils():
    """Test utility functions."""
    print("[TEST] Testing utils module...")
    
    # Test SHA256 hashing
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test data")
        temp_file = f.name
    
    hash_val = compute_sha256(temp_file)
    assert hash_val is not None, "Hash should not be None"
    assert len(hash_val) == 64, "SHA256 hash should be 64 chars"
    print(f"  ✓ SHA256 hash: {hash_val[:16]}...")
    
    # Test username
    user = get_current_user()
    assert user != "unknown", "Should get valid username"
    print(f"  ✓ Current user: {user}")
    
    # Test path resolution
    resolved = resolve_absolute_path("~/.bashrc")
    assert resolved.startswith("/"), "Should resolve to absolute path"
    print(f"  ✓ Path resolution: {resolved}")
    
    Path(temp_file).unlink()
    print("  ✓ Utils module passed all tests\n")

def test_config():
    """Test configuration management."""
    print("[TEST] Testing config module...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CanaryConfig(tmpdir)
        
        # Test adding files
        config.add_file("/test/file1.txt")
        config.add_file("/test/file2.txt")
        assert len(config.get_monitored_files()) == 2
        print("  ✓ Added files to config")
        
        # Test removing files
        config.remove_file("/test/file1.txt")
        assert len(config.get_monitored_files()) == 1
        print("  ✓ Removed file from config")
        
        # Test webhook
        config.set_webhook_url("https://example.com/webhook")
        assert config.get_webhook_url() == "https://example.com/webhook"
        print("  ✓ Webhook URL stored")
        
        # Verify persistence
        config2 = CanaryConfig(tmpdir)
        assert config2.get_webhook_url() == "https://example.com/webhook"
        print("  ✓ Config persisted correctly")
    
    print("  ✓ Config module passed all tests\n")

def test_logger():
    """Test logging functionality."""
    print("[TEST] Testing logger module...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = CanaryLogger(tmpdir)
        
        # Log an event
        event = {
            "event_type": "modified",
            "file_path": "/test/file.txt",
            "username": "testuser",
            "file_hash_sha256": "abc123"
        }
        
        logger.log_event(event)
        
        # Verify log file exists
        assert logger.log_file.exists(), "Log file should exist"
        print("  ✓ Log file created")
        
        # Read events
        events = logger.read_recent_events()
        assert len(events) == 1, "Should read 1 event"
        assert events[0]["event_type"] == "modified"
        print("  ✓ Event logged and read correctly")
    
    print("  ✓ Logger module passed all tests\n")

def test_notifier():
    """Test notifier functionality."""
    print("[TEST] Testing notifier module...")
    
    # Test without webhook
    notifier = CanaryNotifier()
    event = {"event_type": "modified", "file_path": "/test/file.txt"}
    result = notifier.send_alert(event)
    assert result == False, "Should return False without webhook URL"
    print("  ✓ Notifier handles missing webhook correctly")
    
    # Test with webhook URL
    notifier.update_webhook_url("https://example.com/webhook")
    assert notifier.webhook_url == "https://example.com/webhook"
    print("  ✓ Webhook URL updated")
    
    print("  ✓ Notifier module passed all tests\n")

def main():
    """Run all tests."""
    print("=" * 60)
    print("CANARY COMPONENT TESTS")
    print("=" * 60 + "\n")
    
    try:
        test_utils()
        test_config()
        test_logger()
        test_notifier()
        
        print("=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
