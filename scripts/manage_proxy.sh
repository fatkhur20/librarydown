#!/bin/bash

# Utility script to manage proxy for LibraryDown
# This script handles starting, stopping, and checking proxy status
# Supports both Tor and 3proxy

PROXY_TYPE=${2:-"tor"}  # Default to tor, can specify 3proxy/tinyproxy as second argument

# Determine proxy settings based on type
if [ "$PROXY_TYPE" = "3proxy" ]; then
    PROXY_NAME="3proxy"
    PROXY_PORT=2080
    PROXY_SERVICE="3proxy"
    PROXY_PID_FILE="/tmp/3proxy.pid"
elif [ "$PROXY_TYPE" = "tinyproxy" ]; then
    PROXY_NAME="tinyproxy"
    PROXY_PORT=8888
    PROXY_SERVICE="tinyproxy"
    PROXY_PID_FILE=""
else
    PROXY_NAME="Tor"
    PROXY_PORT=9050
    PROXY_SERVICE="tor"
    PROXY_PID_FILE=""
fi

ACTION=${1:-"status"}

case $ACTION in
    "start")
        if [ "$PROXY_TYPE" = "3proxy" ]; then
            echo "Starting 3proxy..."
            if [ -f "/opt/3proxy/3proxy.cfg" ]; then
                /opt/3proxy/3proxy /opt/3proxy/3proxy.cfg
                sleep 2
                if pgrep -f "3proxy" > /dev/null; then
                    echo "3proxy started successfully"
                    echo "SOCKS5 proxy available at: socks5://127.0.0.1:2080"
                else
                    echo "Failed to start 3proxy"
                    exit 1
                fi
            else
                echo "3proxy configuration not found. Run setup_3proxy.sh first."
                exit 1
            fi
        elif [ "$PROXY_TYPE" = "tinyproxy" ]; then
            echo "Starting tinyproxy..."
            systemctl start tinyproxy
            if systemctl is-active --quiet tinyproxy; then
                echo "tinyproxy started successfully"
                echo "HTTP proxy available at: http://127.0.0.1:8888"
            else
                echo "Failed to start tinyproxy"
                exit 1
            fi
        else
            echo "Starting Tor proxy..."
            systemctl start tor
            if systemctl is-active --quiet tor; then
                echo "Tor proxy started successfully"
                echo "SOCKS5 proxy available at: socks5://127.0.0.1:9050"
            else
                echo "Failed to start Tor proxy"
                exit 1
            fi
        fi
        ;;
    "stop")
        if [ "$PROXY_TYPE" = "3proxy" ]; then
            echo "Stopping 3proxy..."
            pkill -f "3proxy" 2>/dev/null || true
            echo "3proxy stopped"
        elif [ "$PROXY_TYPE" = "tinyproxy" ]; then
            echo "Stopping tinyproxy..."
            systemctl stop tinyproxy
            echo "tinyproxy stopped"
        else
            echo "Stopping Tor proxy..."
            systemctl stop tor
            echo "Tor proxy stopped"
        fi
        ;;
    "restart")
        if [ "$PROXY_TYPE" = "3proxy" ]; then
            echo "Restarting 3proxy..."
            pkill -f "3proxy" 2>/dev/null || true
            sleep 2
            if [ -f "/opt/3proxy/3proxy.cfg" ]; then
                /opt/3proxy/3proxy /opt/3proxy/3proxy.cfg
                sleep 2
                if pgrep -f "3proxy" > /dev/null; then
                    echo "3proxy restarted successfully"
                    echo "SOCKS5 proxy available at: socks5://127.0.0.1:2080"
                else
                    echo "Failed to restart 3proxy"
                    exit 1
                fi
            else
                echo "3proxy configuration not found. Run setup_3proxy.sh first."
                exit 1
            fi
        elif [ "$PROXY_TYPE" = "tinyproxy" ]; then
            echo "Restarting tinyproxy..."
            systemctl restart tinyproxy
            if systemctl is-active --quiet tinyproxy; then
                echo "tinyproxy restarted successfully"
                echo "HTTP proxy available at: http://127.0.0.1:8888"
            else
                echo "Failed to restart tinyproxy"
                exit 1
            fi
        else
            echo "Restarting Tor proxy..."
            systemctl restart tor
            if systemctl is-active --quiet tor; then
                echo "Tor proxy restarted successfully"
                echo "SOCKS5 proxy available at: socks5://127.0.0.1:9050"
            else
                echo "Failed to restart Tor proxy"
                exit 1
            fi
        fi
        ;;
    "status")
        if [ "$PROXY_TYPE" = "3proxy" ]; then
            if pgrep -f "3proxy" > /dev/null; then
                echo "3proxy: RUNNING"
                echo "SOCKS5 proxy available at: socks5://127.0.0.1:2080"
                
                # Test connectivity through 3proxy
                echo "Testing 3proxy connectivity..."
                if timeout 10 curl --socks5-hostname 127.0.0.1:2080 -s https://httpbin.org/ip | grep -q "origin" 2>/dev/null; then
                    echo "3proxy connectivity: WORKING"
                else
                    echo "3proxy connectivity: FAILED"
                fi
            else
                echo "3proxy: STOPPED"
            fi
        elif [ "$PROXY_TYPE" = "tinyproxy" ]; then
            if systemctl is-active --quiet tinyproxy; then
                echo "tinyproxy: RUNNING"
                echo "HTTP proxy available at: http://127.0.0.1:8888"
                
                # Test connectivity through tinyproxy
                echo "Testing tinyproxy connectivity..."
                if timeout 10 curl -x http://127.0.0.1:8888 -s https://httpbin.org/ip | grep -q "origin" 2>/dev/null; then
                    echo "tinyproxy connectivity: WORKING"
                else
                    echo "tinyproxy connectivity: FAILED"
                fi
            else
                echo "tinyproxy: STOPPED"
            fi
        else
            if systemctl is-active --quiet tor; then
                echo "Tor proxy: RUNNING"
                echo "SOCKS5 proxy available at: socks5://127.0.0.1:9050"
                
                # Test connectivity through Tor
                echo "Testing Tor proxy connectivity..."
                if timeout 10 curl --socks5-hostname 127.0.0.1:9050 -s https://httpbin.org/ip | grep -q "origin" 2>/dev/null; then
                    echo "Tor proxy connectivity: WORKING"
                else
                    echo "Tor proxy connectivity: FAILED"
                fi
            else
                echo "Tor proxy: STOPPED"
            fi
        fi
        ;;
    "test")
        if [ "$PROXY_TYPE" = "3proxy" ]; then
            echo "Testing 3proxy..."
            if pgrep -f "3proxy" > /dev/null; then
                echo "3proxy service is running"
                
                # Test if we can get a response through 3proxy
                echo "Testing 3proxy functionality..."
                if timeout 10 curl --socks5-hostname 127.0.0.1:2080 -s https://httpbin.org/ip | grep -q "origin" 2>/dev/null; then
                    echo "3proxy test: SUCCESS - Connected through proxy"
                else
                    echo "3proxy test: FAILED - Cannot connect through proxy"
                fi
            else
                echo "3proxy is not running. Start it first with './manage_proxy.sh start 3proxy'"
            fi
        elif [ "$PROXY_TYPE" = "tinyproxy" ]; then
            echo "Testing tinyproxy..."
            if systemctl is-active --quiet tinyproxy; then
                echo "tinyproxy service is running"
                
                # Test if we can get a response through tinyproxy
                echo "Testing tinyproxy functionality..."
                if timeout 10 curl -x http://127.0.0.1:8888 -s https://httpbin.org/ip | grep -q "origin" 2>/dev/null; then
                    echo "tinyproxy test: SUCCESS - Connected through proxy"
                else
                    echo "tinyproxy test: FAILED - Cannot connect through proxy"
                fi
            else
                echo "tinyproxy is not running. Start it first with './manage_proxy.sh start tinyproxy'"
            fi
        else
            echo "Testing Tor proxy..."
            if systemctl is-active --quiet tor; then
                echo "Tor service is running"
                
                # Test if we can get a response through Tor
                echo "Testing Tor proxy functionality..."
                if timeout 10 curl --socks5-hostname 127.0.0.1:9050 -s https://httpbin.org/ip | grep -q "origin" 2>/dev/null; then
                    echo "Tor proxy test: SUCCESS - Connected through proxy"
                else
                    echo "Tor proxy test: FAILED - Cannot connect through proxy"
                fi
            else
                echo "Tor service is not running. Start it first with './manage_proxy.sh start tor'"
            fi
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|test} [proxy_type]"
        echo "  start  - Start proxy service"
        echo "  stop   - Stop proxy service" 
        echo "  restart - Restart proxy service"
        echo "  status - Show proxy status"
        echo "  test   - Test proxy functionality"
        echo ""
        echo "  proxy_type: tor (default), 3proxy, or tinyproxy"
        echo ""
        echo "  Examples:"
        echo "    $0 start            # Start Tor proxy (default)"
        echo "    $0 start tor        # Start Tor proxy"
        echo "    $0 start 3proxy     # Start 3proxy"
        echo "    $0 start tinyproxy  # Start tinyproxy"
        echo "    $0 status tor       # Check Tor status"
        echo "    $0 status 3proxy    # Check 3proxy status"
        echo "    $0 status tinyproxy # Check tinyproxy status"
        exit 1
        ;;
esac