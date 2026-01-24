#!/bin/bash

# Alternative Proxy Setup for YouTube (using 3proxy)
# This creates a lightweight proxy server as fallback to Tor

set -e

echo "Setting up 3proxy as alternative proxy solution..."

# Install prerequisites
if command -v yum &> /dev/null; then
    yum install -y wget gcc make
elif command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y wget gcc make
else
    echo "Please install wget, gcc, and make manually"
    exit 1
fi

# Download and compile 3proxy
cd /tmp
wget https://github.com/z3APA3A/3proxy/archive/0.9.4.tar.gz
tar xzf 0.9.4.tar.gz
cd 3proxy-0.9.4

# Compile 3proxy
make -C src

# Install 3proxy
mkdir -p /opt/3proxy
cp src/3proxy /opt/3proxy/
cp -r scripts/ /opt/3proxy/

# Create configuration
cat > /opt/3proxy/3proxy.cfg << EOF
# 3proxy configuration for LibraryDown
daemon
log /opt/3proxy/3proxy.log D
logformat "- +_L%t.%.0c +_s %+I:%P -> %+i:%p %E %U %C:%c %R:%r %O %I %h %T"

# Admin panel
admin -p127.0.0.1

# SOCKS5 proxy
socks -p2080

# HTTP proxy
proxy -p2081

# Allow all (for testing)
allow *
flush
EOF

# Create log file
touch /opt/3proxy/3proxy.log
chmod 644 /opt/3proxy/3proxy.log

# Create startup script
cat > /opt/3proxy/start_proxy.sh << 'EOF'
#!/bin/bash
/opt/3proxy/3proxy /opt/3proxy/3proxy.cfg
EOF

chmod +x /opt/3proxy/start_proxy.sh

# Start 3proxy
echo "Starting 3proxy server..."
/opt/3proxy/3proxy /opt/3proxy/3proxy.cfg

# Wait for initialization
sleep 2

# Check if running
if pgrep -f "3proxy" > /dev/null; then
    echo "3proxy setup complete!"
    echo "SOCKS5 proxy available at: socks5://127.0.0.1:2080"
    echo "HTTP proxy available at: http://127.0.0.1:2081"
    
    # Test proxy if possible
    if command -v curl &> /dev/null; then
        echo "Testing proxy connectivity..."
        if timeout 10 curl --socks5-hostname 127.0.0.1:2080 -s https://httpbin.org/ip > /dev/null 2>&1; then
            echo -e "\nProxy connection test: \e[32mSUCCESS\e[0m"
        else
            echo -e "\nProxy connection test: \e[33mMay not be fully operational\e[0m"
            echo "This is normal for a fresh proxy setup"
        fi
    fi
    
    echo ""
    echo "To use this proxy in LibraryDown, update config/proxy_config.py:"
    echo "PROXY_HOST = '127.0.0.1'"
    echo "PROXY_PORT = 2080"
    echo "PROXY_TYPE = 'socks5'"
else
    echo -e "\n3proxy setup: \e[31mFAILED\e[0m"
    echo "Check compilation and permissions"
    exit 1
fi