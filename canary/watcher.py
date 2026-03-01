"""
File system monitoring for Canary.

Uses watchdog to detect file access, modification, deletion, and movement.
"""

import os
from pathlib import Path
from typing import Set, Callable, List, Optional
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler, 
    FileModifiedEvent, 
    FileDeletedEvent, 
    FileMovedEvent,
    FileClosedEvent,
    EVENT_TYPE_MODIFIED,
    EVENT_TYPE_DELETED,
    EVENT_TYPE_MOVED,
    EVENT_TYPE_CLOSED
)
from datetime import datetime

from canary.utils import compute_sha256, get_current_user, detect_process_info
from canary.logger import CanaryLogger
from canary.notifier import CanaryNotifier


class CanaryFileEventHandler(FileSystemEventHandler):
    """Custom file system event handler for Canary."""
    
    def __init__(
        self,
        monitored_files: List[str],
        logger: CanaryLogger,
        notifier: CanaryNotifier,
        alert_callback: Optional[Callable] = None
    ):
        """
        Initialize the event handler.
        
        Args:
            monitored_files: List of absolute file paths to monitor
            logger: CanaryLogger instance
            notifier: CanaryNotifier instance
            alert_callback: Optional callback for alerts (for testing/display)
        """
        super().__init__()
        self.monitored_files: Set[str] = set(monitored_files)
        self.logger = logger
        self.notifier = notifier
        self.alert_callback = alert_callback
    
    def _is_monitored(self, path: str) -> bool:
        """Check if a path is in the monitored files list."""
        # Normalize path for comparison
        normalized = str(Path(path).resolve())
        for monitored in self.monitored_files:
            if str(Path(monitored).resolve()) == normalized:
                return True
        return False
    
    def _create_event_dict(
        self,
        event_type: str,
        file_path: str,
        extra_data: dict = None
    ) -> dict:
        """
        Create a structured event dictionary.
        
        Args:
            event_type: Type of event (modified, deleted, moved, accessed)
            file_path: Path to the affected file
            extra_data: Additional event data
            
        Returns:
            Event dictionary
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        username = get_current_user()
        
        event_dict = {
            "timestamp": timestamp,
            "event_type": event_type,
            "file_path": file_path,
            "username": username
        }
        
        # Try to get file hash if file exists
        if os.path.exists(file_path):
            file_hash = compute_sha256(file_path)
            if file_hash:
                event_dict["file_hash_sha256"] = file_hash
        
        # Try to detect process info
        proc_info = detect_process_info(file_path)
        if proc_info:
            event_dict["process_id"] = proc_info[0]
            event_dict["process_command"] = proc_info[1]
        
        # Add extra data if provided
        if extra_data:
            event_dict.update(extra_data)
        
        return event_dict
    
    def _handle_event(self, event_dict: dict) -> None:
        """
        Handle an event: log it, send alert, and notify webhook.
        
        Args:
            event_dict: Event dictionary
        """
        # Log to file
        self.logger.log_event(event_dict)
        
        # Print formatted alert
        self._print_alert(event_dict)
        
        # Send webhook
        self.notifier.send_alert(event_dict)
        
        # Call callback if provided
        if self.alert_callback:
            self.alert_callback(event_dict)
    
    def _print_alert(self, event: dict) -> None:
        """Print formatted alert to console."""
        timestamp = event.get("timestamp", "unknown")
        event_type = event.get("event_type", "unknown").upper()
        file_path = event.get("file_path", "unknown")
        username = event.get("username", "unknown")
        
        print(f"[ALERT] {timestamp} | {event_type} | {file_path} | User: {username}")
    
    def on_modified(self, event):
        """Handle file modification event."""
        if event.is_directory:
            return
        
        if not self._is_monitored(event.src_path):
            return
        
        event_dict = self._create_event_dict("modified", event.src_path)
        self._handle_event(event_dict)
    
    def on_deleted(self, event):
        """Handle file deletion event."""
        if event.is_directory:
            return
        
        if not self._is_monitored(event.src_path):
            return
        
        event_dict = self._create_event_dict("deleted", event.src_path)
        self._handle_event(event_dict)
    
    def on_moved(self, event):
        """Handle file move/rename event."""
        if event.is_directory:
            return
        
        # Check if source was monitored
        if self._is_monitored(event.src_path):
            event_dict = self._create_event_dict(
                "moved",
                event.src_path,
                {"dest_path": event.dest_path}
            )
            self._handle_event(event_dict)
    
    def on_closed(self, event):
        """Handle file close event (indicates file was accessed/opened)."""
        if event.is_directory:
            return
        
        if not self._is_monitored(event.src_path):
            return
        
        # Only alert for closed file if we're explicitly monitoring for access
        # For now, we can track this as an "accessed" event
        event_dict = self._create_event_dict("accessed", event.src_path)
        self._handle_event(event_dict)


class CanaryWatcher:
    """File system watcher using watchdog Observer."""
    
    def __init__(self, monitored_files: List[str], logger: CanaryLogger, notifier: CanaryNotifier):
        """
        Initialize the watcher.
        
        Args:
            monitored_files: List of absolute file paths to monitor
            logger: CanaryLogger instance
            notifier: CanaryNotifier instance
        """
        self.monitored_files = monitored_files
        self.logger = logger
        self.notifier = notifier
        self.observer: Optional[Observer] = None
        self._watch_paths: Set[str] = set()
        self._handler: Optional[CanaryFileEventHandler] = None
    
    def _get_watch_paths(self) -> Set[str]:
        """
        Get unique parent directories for all monitored files.
        
        Returns:
            Set of directory paths to watch
        """
        watch_paths = set()
        for file_path in self.monitored_files:
            parent_dir = str(Path(file_path).parent.resolve())
            watch_paths.add(parent_dir)
        return watch_paths
    
    def start(self, alert_callback: Optional[Callable] = None) -> None:
        """
        Start monitoring files.
        
        Args:
            alert_callback: Optional callback function for alerts
        """
        if not self.monitored_files:
            print("No monitored files configured. Run 'canary add <file>' first.")
            return
        
        self._watch_paths = self._get_watch_paths()
        
        # Create event handler
        self._handler = CanaryFileEventHandler(
            self.monitored_files,
            self.logger,
            self.notifier,
            alert_callback
        )
        
        # Create and start observer
        self.observer = Observer()
        
        for watch_path in self._watch_paths:
            self.observer.schedule(self._handler, watch_path, recursive=False)
        
        self.observer.start()
        
        print(f"[CANARY] Monitoring {len(self.monitored_files)} file(s)")
        print(f"[CANARY] Watching {len(self._watch_paths)} director(ies)")
        if self.notifier.webhook_url:
            print(f"[CANARY] Webhook notifications enabled: {self.notifier.webhook_url}")
        print("[CANARY] Ctrl+C to stop monitoring")
        
        try:
            while True:
                self.observer.join(timeout=1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self) -> None:
        """Stop monitoring files."""
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            print("\n[CANARY] Monitoring stopped")
