"""
Canary - A file tripwire system for Linux security monitoring.

Monitors specific files (honey tokens) and alerts when they are accessed,
modified, moved, or deleted.
"""

__version__ = "1.0.0"
__author__ = "Security Team"
__all__ = ["cli", "watcher", "config", "logger", "notifier", "utils"]
