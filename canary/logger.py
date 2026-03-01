"""
JSON event logging for Canary.

Appends structured JSON events to the events log file.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


class CanaryLogger:
    """Logger for Canary security events."""
    
    def __init__(self, log_dir: str):
        """
        Initialize the logger.
        
        Args:
            log_dir: Directory where logs are stored
        """
        self.log_dir = Path(log_dir)
        self.log_file = self.log_dir / "events.log"
        self._ensure_log_dir()
    
    def _ensure_log_dir(self) -> None:
        """Ensure log directory exists."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def log_event(self, event: Dict[str, Any]) -> None:
        """
        Log a security event as JSON line.
        
        Args:
            event: Dictionary containing event data
        """
        try:
            # Add timestamp if not present
            if "timestamp" not in event:
                event["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
            # Write as JSON line
            with open(self.log_file, "a") as f:
                json.dump(event, f)
                f.write("\n")
        except (OSError, IOError) as e:
            print(f"Error writing to log file: {e}")
    
    def read_recent_events(self, limit: int = 10) -> list:
        """
        Read recent events from log file.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        if not self.log_file.exists():
            return []
        
        events = []
        try:
            with open(self.log_file, "r") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        except (OSError, IOError):
            pass
        
        return events
