# Proxy Setup for LibraryDown

This setup enables YouTube downloads on VPS with restricted IPs using proxy solutions.

## Setup Instructions

### Option 1: Tor Proxy (Recommended for anonymity)
Run the enhanced setup script:
```bash
sudo ./scripts/setup_tor_proxy_enhanced.sh
```

### Option 2: 3proxy (Lightweight alternative)
Run the 3proxy setup script:
```bash
sudo ./scripts/setup_3proxy.sh
```

## Manage Proxy Service

Use the management script with proxy type specification:
```bash
# For Tor proxy
./scripts/manage_proxy.sh start tor
./scripts/manage_proxy.sh status tor
./scripts/manage_proxy.sh test tor
./scripts/manage_proxy.sh restart tor
./scripts/manage_proxy.sh stop tor

# For 3proxy
./scripts/manage_proxy.sh start 3proxy
./scripts/manage_proxy.sh status 3proxy
./scripts/manage_proxy.sh test 3proxy
./scripts/manage_proxy.sh restart 3proxy
./scripts/manage_proxy.sh stop 3proxy

# Default (tor) if no type specified
./scripts/manage_proxy.sh start
```

## Configuration

The proxy settings are in `config/proxy_config.py`:
- Default: Tor proxy at 127.0.0.1:9050
- 3proxy: 127.0.0.1:2080
- Enabled for: YouTube only
- Disabled for: Instagram, TikTok, Twitter

To switch to 3proxy, update `config/proxy_config.py`:
```python
PROXY_PORT = 2080  # Change from 9050 to 2080
```

Or use the `set_proxy_type()` method:
```python
ProxyConfig.set_proxy_type('3proxy')  # Options: 'tor', '3proxy'
```

## YouTube Downloads

After setup, YouTube downloads should work automatically with proxy when:
- Platform is YouTube
- Proxy is enabled in `config/proxy_config.py`
- Selected proxy service is running

## Notes

### Tor Proxy:
- Provides anonymity and good circumvention
- Slower speeds due to relay network
- More stable for long-term use

### 3proxy:
- Lightweight and faster than Tor
- Direct proxy without relay network
- Good for performance-sensitive applications

Both solutions work with EJS and TV Client configurations already in place.

## Troubleshooting

If YouTube downloads still fail:

### For Tor:
1. Check if Tor service is running: `systemctl status tor`
2. Test proxy: `./scripts/manage_proxy.sh test tor`
3. Check proxy connectivity: `curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip`

### For 3proxy:
1. Check if 3proxy is running: `ps aux | grep 3proxy`
2. Test proxy: `./scripts/manage_proxy.sh test 3proxy`
3. Check proxy connectivity: `curl --socks5-hostname 127.0.0.1:2080 https://httpbin.org/ip`

4. Restart proxy: `./scripts/manage_proxy.sh restart [tor|3proxy]`

For best results, combine with valid YouTube cookies in `/opt/librarydown/cookies/`.