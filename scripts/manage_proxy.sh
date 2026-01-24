#!/bin/bash

# Utility script to manage Tor proxy for LibraryDown
# This script handles starting, stopping, and checking Tor proxy status

ACTION=${1:-"status"}

case $ACTION in
    "start")
        echo "Starting Tor proxy..."
        systemctl start tor
        if systemctl is-active --quiet tor; then
            echo "Tor proxy started successfully"
            echo "SOCKS5 proxy available at: socks5://127.0.0.1:9050"
        else
            echo "Failed to start Tor proxy"
            exit 1
        fi
        ;;
    "stop")
        echo "Stopping Tor proxy..."
        systemctl stop tor
        echo "Tor proxy stopped"
        ;;
    "restart")
        echo "Restarting Tor proxy..."
        systemctl restart tor
        if systemctl is-active --quiet tor; then
            echo "Tor proxy restarted successfully"
            echo "SOCKS5 proxy available at: socks5://127.0.0.1:9050"
        else
            echo "Failed to restart Tor proxy"
            exit 1
        fi
        ;;
    "status")
        if systemctl is-active --quiet tor; then
            echo "Tor proxy: RUNNING"
            echo "SOCKS5 proxy available at: socks5://127.0.0.1:9050"
            
            # Test connectivity through proxy
            echo "Testing proxy connectivity..."
            if timeout 10 curl --socks5-hostname 127.0.0.1:9050 -s https://httpbin.org/ip | grep -q "origin"; then
                echo "Proxy connectivity: WORKING"
            else
                echo "Proxy connectivity: FAILED"
            fi
        else
            echo "Tor proxy: STOPPED"
        fi
        ;;
    "test")
        echo "Testing Tor proxy..."
        if systemctl is-active --quiet tor; then
            echo "Tor service is running"
            
            # Test if we can get a different IP through proxy
            echo "Testing proxy functionality..."
            ORIGINAL_IP=$(curl -s https://httpbin.org/ip | jq -r '.origin' 2>/dev/null)
            PROXY_IP=$(curl --socks5-hostname 127.0.0.1:9050 -s https://httpbin.org/ip | jq -r '.origin' 2>/dev/null)
            
            if [ "$ORIGINAL_IP" != "$PROXY_IP" ] && [ -n "$PROXY_IP" ]; then
                echo "Proxy test: SUCCESS - IP changed from $ORIGINAL_IP to $PROXY_IP"
            elif [ -n "$PROXY_IP" ]; then
                echo "Proxy test: PARTIAL - Connected to proxy, IP: $PROXY_IP"
            else
                echo "Proxy test: FAILED - Cannot connect through proxy"
            fi
        else
            echo "Tor service is not running. Start it first with './manage_proxy.sh start'"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|test}"
        echo "  start  - Start Tor proxy service"
        echo "  stop   - Stop Tor proxy service" 
        echo "  restart - Restart Tor proxy service"
        echo "  status - Show Tor proxy status"
        echo "  test   - Test proxy functionality"
        exit 1
        ;;
esac