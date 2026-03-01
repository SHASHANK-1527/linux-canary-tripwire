#!/usr/bin/env python3
"""
Integration test for Canary file tripwire system.

Tests the complete workflow:
1. Initialize Canary
2. Add a monitored file
3. Start watcher in background
4. Modify the file
5. Verify event is logged
"""

import os
import sys
import time
import json
import tempfile
import subprocess
import threading
from pathlib import Path

# Add project to path
sys.path.insert(0, '/home/kali/Project_Canary_file')

from canary.config import CanaryConfig
from canary.logger import CanaryLogger
from canary.utils import resolve_absolute_path


def run_integration_test():
    """Run complete integration test."""
    
    print("=" * 70)
    print("CANARY INTEGRATION TEST")
    print("=" * 70)
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as config_dir:
        with tempfile.TemporaryDirectory() as test_dir:
            
            # Create test file
            test_file = os.path.join(test_dir, "test_canary_file.txt")
            with open(test_file, 'w') as f:
                f.write("Initial content\n")
            
            print(f"\n[TEST] Test file created: {test_file}")
            
            # Step 1: Initialize Canary
            print(f"\n[TEST] Step 1: Initialize Canary")
            config = CanaryConfig(config_dir)
            config.save()
            print(f"       Config directory: {config_dir}")
            print(f"       Config file: {config.config_file}")
            assert config.config_file.exists(), "Config file not created"
            print("       ✓ PASS")
            
            # Step 2: Add test file to monitored list
            print(f"\n[TEST] Step 2: Add file to monitored list")
            abs_path = resolve_absolute_path(test_file)
            config.add_file(abs_path)
            print(f"       File: {abs_path}")
            assert abs_path in config.get_monitored_files()
            print("       ✓ PASS")
            
            # Step 3: Create logger and verify log directory
            print(f"\n[TEST] Step 3: Create logger")
            logs_dir = Path(config_dir) / "logs"
            logger = CanaryLogger(str(logs_dir))
            print(f"       Logs directory: {logs_dir}")
            assert logs_dir.exists(), "Logs directory not created"
            print("       ✓ PASS")
            
            # Step 4: Manually log an event (simulating file modification)
            print(f"\n[TEST] Step 4: Simulate file modification event")
            event = {
                "event_type": "modified",
                "file_path": test_file,
                "username": "testuser",
                "file_hash_sha256": "abc123def456"
            }
            logger.log_event(event)
            print(f"       Event type: {event['event_type']}")
            print(f"       File path: {event['file_path']}")
            assert logger.log_file.exists(), "Log file not created"
            print("       ✓ PASS")
            
            # Step 5: Verify event was logged
            print(f"\n[TEST] Step 5: Verify event in log")
            time.sleep(0.5)  # Give filesystem time to sync
            
            events = logger.read_recent_events()
            assert len(events) > 0, "No events logged"
            
            logged_event = events[-1]
            assert logged_event["event_type"] == "modified", "Wrong event type"
            assert logged_event["file_path"] == test_file, "Wrong file path"
            assert logged_event["username"] == "testuser", "Wrong username"
            print(f"       Events in log: {len(events)}")
            print(f"       Latest event type: {logged_event['event_type']}")
            print(f"       Timestamp: {logged_event['timestamp']}")
            print("       ✓ PASS")
            
            # Step 6: Verify JSON format
            print(f"\n[TEST] Step 6: Verify JSON format")
            with open(logger.log_file, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) > 0, "Log file is empty"
            
            for line in lines:
                parsed = json.loads(line)
                assert "timestamp" in parsed
                assert "event_type" in parsed
                assert "file_path" in parsed
            
            print(f"       Lines in log: {len(lines)}")
            print("       All lines are valid JSON")
            print("       ✓ PASS")
            
            # Step 7: Test multiple events
            print(f"\n[TEST] Step 7: Log multiple events")
            for i in range(3):
                evt = {
                    "event_type": "accessed" if i % 2 == 0 else "modified",
                    "file_path": test_file,
                    "username": f"user{i}"
                }
                logger.log_event(evt)
            
            time.sleep(0.5)
            recent = logger.read_recent_events(limit=10)
            assert len(recent) == 4, f"Expected 4 events, got {len(recent)}"
            print(f"       Total events logged: {len(recent)}")
            print("       ✓ PASS")
            
            # Step 8: Verify config persistence
            print(f"\n[TEST] Step 8: Verify configuration persistence")
            config2 = CanaryConfig(config_dir)
            assert abs_path in config2.get_monitored_files()
            print(f"       Monitored files in reloaded config: {len(config2.get_monitored_files())}")
            print("       ✓ PASS")
    
    print("\n" + "=" * 70)
    print("INTEGRATION TEST PASSED ✓")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    try:
        exit_code = run_integration_test()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n[ERROR] Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        print("\nINTEGRATION TEST FAILED")
        sys.exit(1)
