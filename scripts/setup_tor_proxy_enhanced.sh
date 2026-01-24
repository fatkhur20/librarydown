#!/bin/bash

# Enhanced Tor Proxy Setup Script for Alibaba Cloud Linux
# This script detects the OS and installs Tor appropriately

set -e  # Exit on any error

echo "Detecting OS and setting up Tor proxy..."

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    echo "Cannot detect OS. Please install Tor manually."
    exit 1
fi

echo "Detected OS: $OS (Version: $VER)"

# Install Tor based on detected OS
if [[ "$OS" =~ "Alibaba" || "$OS" =~ "Alinux" ]]; then
    echo "Installing Tor for Alibaba Cloud Linux..."
    
    # Try installing EPEL and Tor
    if command -v yum &> /dev/null; then
        # Enable EPEL repository
        yum install -y epel-release || {
            echo "Trying alternative EPEL installation..."
            yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
        }
        
        # Install Tor
        yum install -y tor || {
            echo "Tor not available in default repos. Trying from REMI..."
            yum install -y https://rpms.remirepo.net/enterprise/remi-release-8.rpm
            yum-config-manager --enable remi
            yum install -y tor
        }
    fi
elif [[ "$OS" =~ "CentOS" || "$OS" =~ "Red Hat" || "$OS" =~ "Rocky" ]]; then
    echo "Installing Tor for CentOS/RHEL/Rocky Linux..."
    
    if command -v yum &> /dev/null; then
        yum install -y epel-release
        yum install -y tor
    elif command -v dnf &> /dev/null; then
        dnf install -y epel-release
        dnf install -y tor
    fi
elif [[ "$OS" =~ "Ubuntu" || "$OS" =~ "Debian" ]]; then
    echo "Installing Tor for Ubuntu/Debian..."
    
    apt-get update
    apt-get install -y tor
else
    echo "Unsupported OS: $OS"
    echo "Attempting to install via package managers..."
    
    # Try different package managers
    if command -v yum &> /dev/null; then
        yum install -y epel-release 2>/dev/null || true
        yum install -y tor 2>/dev/null || {
            echo "Trying with dnf..."
            dnf install -y tor 2>/dev/null || {
                echo "Tor installation failed. Please install manually."
                exit 1
            }
        }
    elif command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y tor
    else
        echo "No supported package manager found. Please install Tor manually."
        exit 1
    fi
fi

# Verify Tor installation
if ! command -v tor &> /dev/null; then
    echo "Tor installation failed. Please install manually."
    exit 1
fi

echo "Tor installed successfully!"

# Backup original config
if [ -f /etc/tor/torrc ]; then
    cp /etc/tor/torrc /etc/tor/torrc.backup.$(date +%s)
fi

# Configure Tor for SOCKS proxy
cat > /etc/tor/torrc << EOF
SocksPort 9050
SocksBindAddress 127.0.0.1
DataDirectory /var/lib/tor

# Additional security settings
AutomapHostsOnResolve 1
DNSPort 53

# Reduce logging
Log notice file /var/log/tor/notices.log
EOF

# Create log directory if it doesn't exist
mkdir -p /var/log/tor
chown -R toranon:toranon /var/log/tor 2>/dev/null || true

# Start Tor service
echo "Starting Tor service..."
systemctl enable tor || true
systemctl start tor

# Wait for Tor to initialize
sleep 5

# Check if Tor is running
if systemctl is-active --quiet tor; then
    echo "Tor proxy setup complete!"
    echo "SOCKS5 proxy available at: socks5://127.0.0.1:9050"
    echo "DNS available at: 127.0.0.1:53"
    
    # Test Tor connectivity if curl supports socks
    echo "Testing Tor connectivity..."
    if timeout 15 curl --socks5-hostname 127.0.0.1:9050 -s https://check.torproject.org/api/ip > /tmp/tor_ip_check 2>&1; then
        TOR_IP=$(cat /tmp/tor_ip_check 2>/dev/null | tr -d '\n\r ')
        if [ -n "$TOR_IP" ] && [ "$TOR_IP" != "null" ]; then
            echo -e "\nTor connection test: \e[32mSUCCESS\e[0m"
            echo "Your IP appears to be routed through Tor: $TOR_IP"
        else
            echo -e "\nTor connection test: \e[33mPARTIAL\e[0m"
            echo "Tor service running but IP check failed"
        fi
    else
        echo -e "\nTor connection test: \e[33mSKIPPED\e[0m"
        echo "Could not test Tor connectivity (curl may not support socks5)"
    fi
    rm -f /tmp/tor_ip_check 2>/dev/null
    
    echo ""
    echo "Next steps:"
    echo "1. Restart your LibraryDown services to use the proxy"
    echo "2. Run: ./scripts/manage_proxy.sh status to check proxy status"
    echo "3. Run: ./scripts/manage_proxy.sh test to test functionality"
else
    echo -e "\nTor connection test: \e[31mFAILED\e[0m"
    echo "Tor service failed to start. Check configuration and logs."
    echo "Try: journalctl -u tor -n 20 to see logs"
    exit 1
fi