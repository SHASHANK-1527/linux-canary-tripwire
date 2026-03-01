# Canary - File Tripwire System

A Linux-only file tripwire system that monitors specific files (honey tokens) and alerts when they are accessed, modified, moved, or deleted.

## Features

- **Real-time File Monitoring**: Uses `watchdog` to detect file system events in real-time
- **Multiple File Support**: Monitor multiple files simultaneously
- **Event Logging**: Stores all events in JSON format for audit trails
- **Webhook Integration**: Send security alerts to external systems
- **Process Tracking**: Attempts to capture the PID and command of processes accessing files
- **File Hashing**: Computes SHA256 hashes of files to detect modifications
- **Production-Grade**: Modular, type-hinted, and properly exception-handled code
- **Linux-Only**: Optimized for Linux security operations

## Installation

### Prerequisites

- Python 3.11 or higher
- Linux operating system
- pip package manager

### Install from Source

Clone the repository and install in development mode:

```bash
cd /path/to/Project_Canary_file
pip install -e .
```

This creates a console command `canary` that can be run from anywhere.

## Quick Start

### 1. Initialize Canary

```bash
canary init
```

This creates:
- `~/.canary/config.json` - Configuration file
- `~/.canary/logs/` - Directory for event logs

### 2. Add Files to Monitor

Monitor specific files by adding them:

```bash
canary add /home/user/passwords.txt
canary add /etc/shadow
canary add /var/www/html/index.php
```

### 3. View Monitored Files

```bash
canary list
```

Output:
```
[CANARY] Monitored files:
  1. /home/user/passwords.txt
  2. /etc/shadow
  3. /var/www/html/index.php
```

### 4. Start Monitoring

```bash
canary watch
```

Output:
```
[CANARY] Monitoring 3 file(s)
[CANARY] Watching 3 director(ies)
[CANARY] Ctrl+C to stop monitoring
```

When a monitored file is accessed, modified, or deleted, you'll see alerts:

```
[ALERT] 2026-03-01T14:23:45.123Z | MODIFIED | /home/user/passwords.txt | User: kali
[ALERT] 2026-03-01T14:24:12.456Z | DELETED | /home/user/passwords.txt | User: kali
```

## Configuration

### Set Webhook URL

Send alerts to an external service (like Slack, Discord, or a custom server):

```bash
canary set-webhook https://webhook.site/your-unique-id
canary set-webhook https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

To disable webhooks:

```bash
canary set-webhook none
```

### Configuration File

The configuration is stored in `~/.canary/config.json`:

```json
{
  "version": 1,
  "monitored_files": [
    "/home/user/passwords.txt",
    "/etc/shadow"
  ],
  "webhook_url": "https://webhook.site/unique-id"
}
```

## Event Log

All events are logged in JSON format to `~/.canary/logs/events.log`.

Each line is a separate JSON object:

```json
{
  "timestamp": "2026-03-01T14:23:45.123Z",
  "event_type": "modified",
  "file_path": "/home/user/passwords.txt",
  "username": "kali",
  "file_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "process_id": 2847,
  "process_command": "cat"
}
```

Query recent events:

```bash
tail -10 ~/.canary/logs/events.log
```

Pretty-print events:

```bash
cat ~/.canary/logs/events.log | jq '.'
```

## Webhook Integration

### Webhook Payload

When an event occurs, Canary sends a JSON POST request to the configured webhook URL:

```json
{
  "timestamp": "2026-03-01T14:23:45.123Z",
  "event_type": "accessed",
  "file_path": "/home/user/passwords.txt",
  "username": "kali",
  "file_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "process_id": 2847,
  "process_command": "cat"
}
```

### Supported Event Types

- `accessed` - File was opened or accessed
- `modified` - File contents were changed
- `deleted` - File was deleted
- `moved` - File was moved or renamed

### Example: Slack Integration

Create a Slack webhook and configure it:

```bash
canary set-webhook https://hooks.slack.com/services/<YOUR_SLACK_WEBHOOK_URL>
```

The alert will appear in Slack as a POST request to your webhook.

### Example: Custom Server

If you have a custom webhook server, configure it:

```bash
canary set-webhook http://security-server.local:5000/events
```

Your server would receive:

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/events', methods=['POST'])
def receive_event():
    event = request.json
    print(f"Security Alert: {event['event_type']} on {event['file_path']}")
    print(f"User: {event['username']}, Timestamp: {event['timestamp']}")
    if event.get('process_command'):
        print(f"Process: {event['process_command']} (PID: {event['process_id']})")
    return {"status": "ok"}, 200

if __name__ == '__main__':
    app.run(port=5000)
```

## CLI Commands Reference

### `canary init`

Initialize Canary configuration and directories.

```bash
canary init
```

### `canary add <file_path>`

Add a file to the monitored list. Supports absolute and relative paths.

```bash
canary add /home/kali/passwords.txt
canary add ~/.ssh/id_rsa
canary add ./secret.txt
```

### `canary remove <file_path>`

Remove a file from the monitored list.

```bash
canary remove /home/kali/passwords.txt
```

### `canary list`

List all monitored files.

```bash
canary list
```

### `canary watch`

Start real-time monitoring of all configured files.

```bash
canary watch
```

Press `Ctrl+C` to stop monitoring.

### `canary set-webhook <url>`

Configure webhook URL for alerts, or disable with 'none'.

```bash
canary set-webhook https://webhook.site/unique-id
canary set-webhook none  # Disable webhooks
```

## Files and Directories

```
~/.canary/
├── config.json          # Configuration file
└── logs/
    └── events.log       # JSON event log
```

## Security Considerations

### Disclaimer

**This tool is designed for legitimate security monitoring and testing purposes.**

- Use only on systems you own or have explicit permission to monitor
- Do not use for unauthorized surveillance
- Ensure compliance with applicable laws and regulations
- This tool captures usernames and process information
- Monitor webhook endpoints for security
- Keep event logs secure (appropriate file permissions)

### Best Practices

1. **File Permissions**: Protect config and log files:
   ```bash
   chmod 600 ~/.canary/config.json
   chmod 700 ~/.canary/logs/
   ```

2. **Webhook Security**: Use HTTPS for webhook URLs
   ```bash
   canary set-webhook https://webhook.site/...  # HTTPS recommended
   ```

3. **Monitor Honey Tokens**: Place decoy files in strategic locations:
   ```bash
   echo "db_password_123" > /tmp/honeypot.txt
   canary add /tmp/honeypot.txt
   ```

4. **Regular Log Review**: Check logs periodically:
   ```bash
   tail -50 ~/.canary/logs/events.log
   ```

5. **Run as Non-Root**: Avoid running as root when possible (unless monitoring restricted files)
   ```bash
   # Good - runs as current user
   canary watch
   
   # Not recommended
   sudo canary watch
   ```

## Example Use Cases

### Honeypot Monitoring

Create decoy files and monitor them:

```bash
echo "CONFIDENTIAL_API_KEY=sk_test_12345" > /tmp/api_key.cfg
canary add /tmp/api_key.cfg
canary watch
```

Any access to this file will immediately trigger an alert.

### Configuration File Monitoring

Monitor critical system or application configuration:

```bash
canary add /etc/postgresql/postgresql.conf
canary add /var/www/app/config.json
canary add /home/app/.env
canary watch
```

### SSH Key Monitoring

Alert on any access to SSH keys:

```bash
canary add ~/.ssh/id_rsa
canary add ~/.ssh/id_ed25519
canary set-webhook https://security-team.example.com/alerts
canary watch
```

## Terminal Output Examples

### Initialization

```
$ canary init
[CANARY] Initialized configuration in /home/kali/.canary
[CANARY] Config file: /home/kali/.canary/config.json
[CANARY] Logs directory: /home/kali/.canary/logs
```

### Adding Files

```
$ canary add ~/passwords.txt
[CANARY] Added file to monitored list: /home/kali/passwords.txt

$ canary add /etc/shadow
[CANARY] Added file to monitored list: /etc/shadow
```

### Listing Files

```
$ canary list
[CANARY] Monitored files:
  1. /home/kali/passwords.txt
  2. /etc/shadow
```

### Monitoring Active

```
$ canary watch
[CANARY] Monitoring 2 file(s)
[CANARY] Watching 2 director(ies)
[CANARY] Ctrl+C to stop monitoring

[ALERT] 2026-03-01T14:23:45.123Z | ACCESSED | /home/kali/passwords.txt | User: kali
[ALERT] 2026-03-01T14:23:47.456Z | MODIFIED | /etc/shadow | User: root
[ALERT] 2026-03-01T14:23:50.789Z | DELETED | /home/kali/passwords.txt | User: kali

^C
[CANARY] Monitoring stopped
```

### Event Log

```
$ tail -3 ~/.canary/logs/events.log
{"timestamp": "2026-03-01T14:23:45.123Z", "event_type": "accessed", "file_path": "/home/kali/passwords.txt", "username": "kali"}
{"timestamp": "2026-03-01T14:23:47.456Z", "event_type": "modified", "file_path": "/etc/shadow", "username": "root", "file_hash_sha256": "abc123..."}
{"timestamp": "2026-03-01T14:23:50.789Z", "event_type": "deleted", "file_path": "/home/kali/passwords.txt", "username": "kali"}
```

## Technologies Used

- **watchdog** - File system event monitoring
- **requests** - HTTP webhook communication
- **argparse** - Command-line interface
- **pathlib** - Cross-platform path handling
- **json** - Configuration and event logging
- **subprocess** - Process information via lsof
- **hashlib** - SHA256 hashing

## Project Structure

```
canary/
├── __init__.py          # Package initialization
├── cli.py               # Command-line interface (argparse)
├── config.py            # Configuration management
├── logger.py            # JSON event logging
├── notifier.py          # Webhook notifications
├── utils.py             # Utility functions (hashing, process info)
└── watcher.py           # File system monitoring (watchdog)

pyproject.toml           # Package metadata and setuptools config
requirements.txt         # Dependencies
README.md                # This file
LICENSE                  # MIT License
.gitignore               # Git ignore file
```

## Development

### Running Tests (Future)

Tests would be placed in a `tests/` directory and run with:

```bash
pytest tests/
```

### Code Quality

Format code with Black:

```bash
black canary/
```

Check with flake8:

```bash
flake8 canary/
```

Type check with mypy:

```bash
mypy canary/
```

## Known Limitations

1. **File Rename/Move Detection**: The file must be in a monitored directory for the move event to be detected
2. **Application Start**: Monitoring starts after `canary watch` is run; past events are not captured
3. **Root Files**: Some system files require elevated privileges
4. **Network Latency**: Webhook sends are asynchronous but may have network delays

## Troubleshooting

### File not being monitored

- Ensure the file path is absolute: Use `canary add /absolute/path/to/file`
- Check that the file exists: `ls -la /path/to/file`
- Verify it's in the list: `canary list`

### Webhook not sending

- Check the webhook URL: `cat ~/.canary/config.json | jq '.webhook_url'`
- Verify network connectivity: `curl https://your-webhook-url`
- Check logs for errors: `tail ~/.canary/logs/events.log`

### Permission denied errors

- Ensure you have read access to monitored files
- For system files, use `sudo canary watch`
- Check file permissions: `ls -la /path/to/file`

## License

MIT License - See LICENSE file for details

## Contributing

This is a prototype security tool. Contributions and improvements are welcome.

## Support

For issues, questions, or suggestions, refer to the project documentation.

---

**Stay vigilant. Canaries sing when danger approaches.** 🐦‍⬛
