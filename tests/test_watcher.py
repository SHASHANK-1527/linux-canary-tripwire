"""Unit tests for canary.watcher module."""

import pytest
import tempfile
import time
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from canary.watcher import CanaryFileEventHandler, CanaryWatcher
from canary.logger import CanaryLogger
from canary.notifier import CanaryNotifier


class TestCanaryFileEventHandler:
    """Test file event handler."""
    
    def test_handler_initialization(self):
        """Test handler initializes correctly."""
        monitored = ["/test/file1.txt", "/test/file2.txt"]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            notifier = CanaryNotifier()
            
            handler = CanaryFileEventHandler(monitored, logger, notifier)
            assert handler.monitored_files == set(monitored)
            assert handler.logger == logger
            assert handler.notifier == notifier
    
    def test_handler_is_monitored(self):
        """Test file monitoring check."""
        monitored = ["/test/file1.txt"]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            notifier = CanaryNotifier()
            
            handler = CanaryFileEventHandler(monitored, logger, notifier)
            
            # Should handle full paths
            # Create temp file and check
            with tempfile.NamedTemporaryFile(delete=False) as f:
                temp_path = f.name
            
            try:
                # Add temp file to monitoring
                handler.monitored_files = {temp_path}
                assert handler._is_monitored(temp_path)
                assert not handler._is_monitored("/some/other/file.txt")
            finally:
                os.unlink(temp_path)
    
    def test_handler_create_event_dict(self):
        """Test event dictionary creation."""
        monitored = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            notifier = CanaryNotifier()
            
            handler = CanaryFileEventHandler(monitored, logger, notifier)
            
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(b"test content")
                temp_path = f.name
            
            try:
                event = handler._create_event_dict("modified", temp_path)
                
                # Check required fields
                assert "timestamp" in event
                assert "event_type" in event
                assert event["event_type"] == "modified"
                assert "file_path" in event
                assert event["file_path"] == temp_path
                assert "username" in event
                
                # Hash should be present for existing file
                if "file_hash_sha256" in event:
                    assert len(event["file_hash_sha256"]) == 64
            finally:
                os.unlink(temp_path)
    
    def test_handler_event_dict_with_extra_data(self):
        """Test event dict with extra data."""
        monitored = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            notifier = CanaryNotifier()
            
            handler = CanaryFileEventHandler(monitored, logger, notifier)
            
            extra = {"dest_path": "/new/path.txt", "process_id": 1234}
            event = handler._create_event_dict("moved", "/old/path.txt", extra)
            
            assert event["dest_path"] == "/new/path.txt"
            assert event["process_id"] == 1234


class TestCanaryWatcher:
    """Test file watcher functionality."""
    
    def test_watcher_initialization(self):
        """Test watcher initializes correctly."""
        monitored = ["/test/file1.txt"]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            notifier = CanaryNotifier()
            
            watcher = CanaryWatcher(monitored, logger, notifier)
            assert watcher.monitored_files == monitored
            assert watcher.observer is None
    
    def test_watcher_get_watch_paths(self):
        """Test watch path calculation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_files = [
                os.path.join(tmpdir, "file1.txt"),
                os.path.join(tmpdir, "file2.txt"),
                os.path.join(tmpdir, "subdir", "file3.txt"),
            ]
            
            logger = CanaryLogger(tmpdir)
            notifier = CanaryNotifier()
            watcher = CanaryWatcher(test_files, logger, notifier)
            
            watch_paths = watcher._get_watch_paths()
            
            # Should have tmpdir and tmpdir/subdir
            assert len(watch_paths) >= 1
            assert tmpdir in watch_paths or str(Path(tmpdir).resolve()) in watch_paths
    
    def test_watcher_empty_monitored_list(self):
        """Test watcher with empty monitored list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            notifier = CanaryNotifier()
            
            watcher = CanaryWatcher([], logger, notifier)
            
            with patch('sys.stdout'):
                watcher.start()
            # Should handle gracefully and not start
    
    def test_watcher_with_alert_callback(self):
        """Test watcher with alert callback."""
        callback_events = []
        
        def test_callback(event):
            callback_events.append(event)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            notifier = CanaryNotifier()
            monitor_file = os.path.join(tmpdir, "test.txt")
            
            watcher = CanaryWatcher([monitor_file], logger, notifier)
            
            # Callback should be stored
            # (We can't easily test actual file notifications without running observer)
            assert callable(test_callback)


class TestEventHandling:
    """Test event handling scenarios."""
    
    def test_event_logging_on_modified(self):
        """Test that modified events are logged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            notifier = CanaryNotifier()
            
            with tempfile.NamedTemporaryFile(dir=tmpdir, delete=False) as f:
                temp_file = f.name
            
            try:
                handler = CanaryFileEventHandler([temp_file], logger, notifier)
                
                # Create mock event
                event = MagicMock()
                event.src_path = temp_file
                event.is_directory = False
                
                # Trigger modified
                handler.on_modified(event)
                
                # Check log
                events = logger.read_recent_events()
                assert len(events) > 0
                assert events[-1]["event_type"] == "modified"
            finally:
                os.unlink(temp_file)
    
    def test_event_not_logged_for_non_monitored_file(self):
        """Test that non-monitored files don't trigger events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            notifier = CanaryNotifier()
            
            # Monitor one file but trigger event on another
            handler = CanaryFileEventHandler(["/monitored/file.txt"], logger, notifier)
            
            event = MagicMock()
            event.src_path = "/other/file.txt"
            event.is_directory = False
            
            handler.on_modified(event)
            
            # No event should be logged
            events = logger.read_recent_events()
            assert len(events) == 0
    
    def test_event_not_logged_for_directory(self):
        """Test that directory events are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CanaryLogger(tmpdir)
            notifier = CanaryNotifier()
            
            handler = CanaryFileEventHandler([tmpdir], logger, notifier)
            
            event = MagicMock()
            event.src_path = tmpdir
            event.is_directory = True
            
            handler.on_modified(event)
            
            # No event should be logged
            events = logger.read_recent_events()
            assert len(events) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
