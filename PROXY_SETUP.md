# Proxy Setup for LibraryDown

This setup enables YouTube downloads on VPS with restricted IPs using Tor proxy.

## Setup Instructions

### 1. Install Tor Proxy
Run the setup script:
```bash
sudo ./scripts/setup_tor_proxy.sh
```

### 2. Manage Proxy Service
Use the management script:
```bash
# Start proxy
./scripts/manage_proxy.sh start

# Check status
./scripts/manage_proxy.sh status

# Test proxy functionality
./scripts/manage_proxy.sh test

# Restart proxy if needed
./scripts/manage_proxy.sh restart

# Stop proxy
./scripts/manage_proxy.sh stop
```

### 3. YouTube Downloads
After setup, YouTube downloads should work automatically with proxy when:
- Platform is YouTube
- Proxy is enabled in `config/proxy_config.py`
- Tor service is running

## Configuration

The proxy settings are in `config/proxy_config.py`:
- Proxy type: SOCKS5
- Address: 127.0.0.1:9050
- Enabled for: YouTube only
- Disabled for: Instagram, TikTok, Twitter

## Notes

- Tor provides anonymity but slower speeds
- May take longer to establish connections
- Some videos might still be unavailable due to YouTube restrictions
- Monitor Tor service to ensure it stays running

## Troubleshooting

If YouTube downloads still fail:
1. Check if Tor service is running: `systemctl status tor`
2. Test proxy: `./scripts/manage_proxy.sh test`
3. Check proxy connectivity: `curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip`
4. Restart Tor: `./scripts/manage_proxy.sh restart`

For best results, combine with valid YouTube cookies in `/opt/librarydown/cookies/`.