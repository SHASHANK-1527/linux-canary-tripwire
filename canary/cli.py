"""
Command-line interface for Canary.

Provides CLI subcommands for managing and running the file tripwire.
"""

import argparse
import sys
from pathlib import Path

from canary.config import CanaryConfig
from canary.logger import CanaryLogger
from canary.notifier import CanaryNotifier
from canary.watcher import CanaryWatcher
from canary.utils import resolve_absolute_path


def get_config_dir() -> str:
    """Get the Canary config directory."""
    return str(Path.home() / ".canary")


def cmd_init(args) -> int:
    """Initialize Canary configuration."""
    config_dir = get_config_dir()
    config = CanaryConfig(config_dir)
    config.save()  # Explicitly save initial config to disk
    
    logs_dir = Path(config_dir) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[CANARY] Initialized configuration in {config_dir}")
    print(f"[CANARY] Config file: {config.config_file}")
    print(f"[CANARY] Logs directory: {logs_dir}")
    return 0


def cmd_add(args) -> int:
    """Add a file to the monitored list."""
    if not args.file:
        print("Error: file path required")
        return 1
    
    config_dir = get_config_dir()
    config = CanaryConfig(config_dir)
    
    try:
        abs_path = resolve_absolute_path(args.file)
    except Exception as e:
        print(f"Error resolving path: {e}")
        return 1
    
    if config.add_file(abs_path):
        print(f"[CANARY] Added file to monitored list: {abs_path}")
        return 0
    else:
        print(f"[CANARY] File already in monitored list: {abs_path}")
        return 0


def cmd_remove(args) -> int:
    """Remove a file from the monitored list."""
    if not args.file:
        print("Error: file path required")
        return 1
    
    config_dir = get_config_dir()
    config = CanaryConfig(config_dir)
    
    try:
        abs_path = resolve_absolute_path(args.file)
    except Exception as e:
        print(f"Error resolving path: {e}")
        return 1
    
    if config.remove_file(abs_path):
        print(f"[CANARY] Removed file from monitored list: {abs_path}")
        return 0
    else:
        print(f"[CANARY] File not found in monitored list: {abs_path}")
        return 1


def cmd_list(args) -> int:
    """List monitored files."""
    config_dir = get_config_dir()
    config = CanaryConfig(config_dir)
    
    files = config.get_monitored_files()
    
    if not files:
        print("[CANARY] No monitored files configured")
        return 0
    
    print("[CANARY] Monitored files:")
    for i, file_path in enumerate(files, 1):
        print(f"  {i}. {file_path}")
    
    return 0


def cmd_watch(args) -> int:
    """Start monitoring files."""
    config_dir = get_config_dir()
    config = CanaryConfig(config_dir)
    logs_dir = Path(config_dir) / "logs"
    
    monitored_files = config.get_monitored_files()
    
    if not monitored_files:
        print("[CANARY] Error: No monitored files configured")
        print("[CANARY] Use 'canary add <file>' to add files")
        return 1
    
    logger = CanaryLogger(str(logs_dir))
    webhook_url = config.get_webhook_url()
    notifier = CanaryNotifier(webhook_url)
    
    watcher = CanaryWatcher(monitored_files, logger, notifier)
    
    try:
        watcher.start()
    except Exception as e:
        print(f"[CANARY] Error during monitoring: {e}")
        return 1
    
    return 0


def cmd_set_webhook(args) -> int:
    """Set or remove webhook URL."""
    if not args.url:
        print("Error: webhook URL required (or 'none' to disable)")
        return 1
    
    config_dir = get_config_dir()
    config = CanaryConfig(config_dir)
    
    if args.url.lower() == "none":
        config.set_webhook_url(None)
        print("[CANARY] Webhook notifications disabled")
    else:
        config.set_webhook_url(args.url)
        print(f"[CANARY] Webhook URL set to: {args.url}")
    
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="canary",
        description="Canary - File tripwire system for Linux security monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  canary init                              Initialize Canary
  canary add /home/user/passwords.txt      Add file to monitor
  canary list                              List monitored files
  canary watch                             Start monitoring
  canary set-webhook https://example.com   Set webhook URL
  canary set-webhook none                  Disable webhook
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # init command
    subparsers.add_parser("init", help="Initialize Canary configuration")
    
    # add command
    add_parser = subparsers.add_parser("add", help="Add file to monitored list")
    add_parser.add_argument("file", help="Path to file to monitor")
    
    # remove command
    remove_parser = subparsers.add_parser("remove", help="Remove file from monitored list")
    remove_parser.add_argument("file", help="Path to file to stop monitoring")
    
    # list command
    subparsers.add_parser("list", help="List monitored files")
    
    # watch command
    subparsers.add_parser("watch", help="Start monitoring files")
    
    # set-webhook command
    webhook_parser = subparsers.add_parser("set-webhook", help="Set webhook URL")
    webhook_parser.add_argument("url", help="Webhook URL (or 'none' to disable)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Map commands to functions
    commands = {
        "init": cmd_init,
        "add": cmd_add,
        "remove": cmd_remove,
        "list": cmd_list,
        "watch": cmd_watch,
        "set-webhook": cmd_set_webhook,
    }
    
    cmd_func = commands.get(args.command)
    if cmd_func:
        return cmd_func(args)
    
    print(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
