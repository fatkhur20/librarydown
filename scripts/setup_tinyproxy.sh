#!/bin/bash

# Simple proxy setup for Alibaba Cloud Linux
# Using tinyproxy as an alternative to Tor/3proxy

set -e

echo "Setting up tinyproxy as a simple HTTP proxy..."

# Install tinyproxy
yum install -y tinyproxy

# Configure tinyproxy
cat > /etc/tinyproxy/tinyproxy.conf << EOF
User tinyproxy
Group tinyproxy
Port 8888
Timeout 600
DefaultErrorFile "/usr/share/tinyproxy/default.html"
StatFile "/usr/share/tinyproxy/stats.html"
Logfile "/var/log/tinyproxy/tinyproxy.log"
Syslog On
LogLevel Info
PidFile "/run/tinyproxy/tinyproxy.pid"
MaxClients 100
MinSpareServers 5
MaxSpareServers 20
StartServers 10
MaxRequestsPerChild 0
Allow 127.0.0.1
Allow 10.0.0.0/8
Allow 172.16.0.0/12
Allow 192.168.0.0/16
ViaProxyName "tinyproxy"
ConnectPort 443
ConnectPort 563
EOF

# Create log directory
mkdir -p /var/log/tinyproxy
chown tinyproxy:tinyproxy /var/log/tinyproxy

# Start and enable tinyproxy
systemctl enable tinyproxy
systemctl start tinyproxy

echo "Tinyproxy setup complete!"
echo "HTTP proxy available at: http://127.0.0.1:8888"
echo ""
echo "To use with YouTube downloads, update config/proxy_config.py:"
echo "PROXY_TYPE = 'http'"
echo "PROXY_PORT = 8888"
echo ""
echo "Test the proxy with:"
echo "curl -x http://127.0.0.1:8888 https://httpbin.org/ip"