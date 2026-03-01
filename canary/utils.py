"""
Utility functions for Canary.

Provides helpers for hashing, system info, and process detection.
"""

import hashlib
import subprocess
import os
from pathlib import Path
from typing import Optional, Tuple


def compute_sha256(file_path: str) -> Optional[str]:
    """
    Compute SHA256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hex digest of SHA256 hash or None if file doesn't exist or can't be read
    """
    try:
        if not os.path.exists(file_path):
            return None
            
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (OSError, IOError):
        return None


def get_current_user() -> str:
    """
    Get the current username.
    
    Returns:
        Current username or 'unknown'
    """
    try:
        return os.getlogin()
    except OSError:
        # Fallback if os.getlogin() fails
        return os.environ.get("USER", "unknown")


def detect_process_info(file_path: str) -> Optional[Tuple[int, str]]:
    """
    Detect the process ID and command accessing a file using lsof.
    
    Args:
        file_path: Absolute path to the file
        
    Returns:
        Tuple of (PID, command) or None if unable to detect
    """
    try:
        # Use lsof to find processes accessing this file
        result = subprocess.run(
            ["lsof", file_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return None
            
        lines = result.stdout.strip().split("\n")
        if len(lines) < 2:
            return None
        
        # Parse lsof output: skip header, get first entry
        parts = lines[1].split()
        if len(parts) >= 2:
            try:
                pid = int(parts[1])
                command = parts[0]
                return (pid, command)
            except (ValueError, IndexError):
                return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None
    
    return None


def resolve_absolute_path(file_path: str) -> str:
    """
    Resolve a file path to its absolute form.
    
    Args:
        file_path: File path (can be relative or absolute)
        
    Returns:
        Absolute path as string
    """
    return str(Path(file_path).expanduser().resolve())
