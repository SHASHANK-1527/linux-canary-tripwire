"""Unit tests for canary.logger module."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from canary.logger import CanaryLogger


class TestCanaryLogger:
    """Test event logging functionality."""
    
    def test_logger_initialization(self):
        """Test logger initializes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            assert logger.log_dir == Path(tmpdir)
            assert logger.log_file == Path(tmpdir) / "events.log"
    
    def test_logger_creates_directory(self):
        """Test that logger creates log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "logs"
            logger = CanaryLogger(str(log_path))
            assert log_path.exists()
    
    def test_logger_creates_log_file(self):
        """Test that logger creates log file on first write."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            event = {
                "event_type": "modified",
                "file_path": "/test/file.txt",
                "username": "testuser"
            }
            logger.log_event(event)
            assert logger.log_file.exists()
    
    def test_log_event_format(self):
        """Test that logged event is valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            event = {
                "event_type": "modified",
                "file_path": "/test/file.txt",
                "username": "testuser"
            }
            logger.log_event(event)
            
            # Read and verify JSON format
            with open(logger.log_file, 'r') as f:
                logged_event = json.loads(f.readline())
            
            assert logged_event["event_type"] == "modified"
            assert logged_event["file_path"] == "/test/file.txt"
            assert logged_event["username"] == "testuser"
            assert "timestamp" in logged_event
    
    def test_log_event_adds_timestamp(self):
        """Test that logger adds timestamp if not present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            event = {"event_type": "accessed"}
            logger.log_event(event)
            
            with open(logger.log_file, 'r') as f:
                logged_event = json.loads(f.readline())
            
            assert "timestamp" in logged_event
            # Check timestamp format (ISO 8601)
            assert "T" in logged_event["timestamp"]
            assert "Z" in logged_event["timestamp"]
    
    def test_log_multiple_events(self):
        """Test logging multiple events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            
            events = [
                {"event_type": "modified", "file_path": "/test/1.txt"},
                {"event_type": "deleted", "file_path": "/test/2.txt"},
                {"event_type": "accessed", "file_path": "/test/3.txt"},
            ]
            
            for event in events:
                logger.log_event(event)
            
            # Read all events
            with open(logger.log_file, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 3
            for line in lines:
                json_obj = json.loads(line)
                assert "event_type" in json_obj
                assert "file_path" in json_obj
    
    def test_log_event_one_per_line(self):
        """Test that each event is on its own line (JSON Lines format)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            
            logger.log_event({"event_type": "modified"})
            logger.log_event({"event_type": "deleted"})
            logger.log_event({"event_type": "accessed"})
            
            with open(logger.log_file, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 3
            # Each line should be valid JSON
            for line in lines:
                json.loads(line)
    
    def test_read_recent_events(self):
        """Test reading recent events from log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            
            for i in range(5):
                logger.log_event({"event_type": f"event_{i}", "index": i})
            
            recent = logger.read_recent_events(limit=3)
            assert len(recent) <= 3
            # Last event should be the most recent
            assert recent[-1]["index"] == 4
    
    def test_read_recent_events_empty_log(self):
        """Test reading from empty log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            events = logger.read_recent_events()
            assert events == []
    
    def test_read_recent_events_limit(self):
        """Test that limit is respected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            
            for i in range(10):
                logger.log_event({"event_type": f"event_{i}"})
            
            recent = logger.read_recent_events(limit=3)
            assert len(recent) == 3
    
    def test_event_preserves_all_data(self):
        """Test that all event data is preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            
            event = {
                "event_type": "modified",
                "file_path": "/test/file.txt",
                "username": "testuser",
                "file_hash_sha256": "abc123def456",
                "process_id": 1234,
                "process_command": "cat",
            }
            
            logger.log_event(event)
            
            with open(logger.log_file, 'r') as f:
                logged = json.loads(f.readline())
            
            for key in event:
                assert key in logged
                assert logged[key] == event[key]
    
    def test_invalid_json_in_log_skipped(self):
        """Test that invalid JSON lines are skipped when reading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            
            # Write valid then invalid JSON
            with open(logger.log_file, 'w') as f:
                f.write('{"valid": true}\n')
                f.write('{ invalid json }\n')
                f.write('{"valid": true}\n')
            
            # Read recent - should skip invalid
            recent = logger.read_recent_events()
            assert len(recent) == 2  # Only 2 valid events
            assert recent[0]["valid"] == True
            assert recent[1]["valid"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
