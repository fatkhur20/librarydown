#!/bin/bash

# Setup Tor Proxy for YouTube requests
# This script installs and configures Tor as a SOCKS5 proxy

set -e  # Exit on any error

echo "Setting up Tor proxy..."

# Install Tor
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y tor
elif command -v yum &> /dev/null; then
    yum install -y epel-release
    yum install -y tor
elif command -v dnf &> /dev/null; then
    dnf install -y tor
else
    echo "Unsupported OS. Please install Tor manually."
    exit 1
fi

# Backup original config
cp /etc/tor/torrc /etc/tor/torrc.backup

# Configure Tor for SOCKS proxy
cat > /etc/tor/torrc << EOF
SocksPort 9050
SocksBindAddress 127.0.0.1
DataDirectory /var/lib/tor

# Additional security settings
AutomapHostsOnResolve 1
DNSPort 53
EOF

# Start Tor service
systemctl start tor
systemctl enable tor

echo "Tor proxy setup complete!"
echo "SOCKS5 proxy available at: socks5://127.0.0.1:9050"
echo "DNS available at: 127.0.0.1:53"

# Test Tor connectivity
sleep 5
if curl --socks5-hostname 127.0.0.1:9050 -s https://check.torproject.org/api/ip; then
    echo -e "\nTor connection test: \e[32mSUCCESS\e[0m"
    echo "Your IP appears to be routed through Tor"
else
    echo -e "\nTor connection test: \e[31mFAILED\e[0m"
    echo "Check Tor configuration and firewall settings"
fi