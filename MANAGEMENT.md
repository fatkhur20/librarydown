# LibraryDown Management Scripts

This directory contains the management scripts for LibraryDown system.

## Main Scripts

### `master-manager.sh` - Master Management Suite
Complete management system with multiple commands:

- `setup` - Fresh installation (dependencies + services + start)
- `start` - Start all services (auto-detect environment)
- `stop` - Stop all services
- `restart` - Restart all services
- `status` - Show service status
- `bot-config` - Configure Telegram bot settings
- `bot-start` - Start only the Telegram bot
- `bot-stop` - Stop the Telegram bot
- `check` - Run system diagnostics
- `monitor` - Monitor services continuously
- `backup` - Backup configuration and cookies
- `clean` - Clean old backups and logs
- `update` - Update system to latest version
- `upload-test` - Test cookie upload functionality

### `setup.sh` - Quick Setup
Shortcut for complete installation:
```bash
bash setup.sh
```

### `update.sh` - Quick Update
Shortcut for update and restart:
```bash
bash update.sh
```

### `restart.sh` - Quick Restart
Shortcut for restart all services:
```bash
bash restart.sh
```

## Features

- Auto-detect environment (systemd vs Termux)
- Auto-start Telegram bot with monitoring
- Cookie auto-rename based on platform
- Built-in monitoring and alerting
- Backup and restore capabilities
- Multi-platform support (YouTube, Instagram, TikTok, Twitter)

## Usage

```bash
# For complete control
bash master-manager.sh [command]

# For quick operations
bash setup.sh    # Full setup
bash update.sh   # Update and restart
bash restart.sh  # Restart services
```