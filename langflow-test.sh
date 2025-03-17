#!/bin/bash
# Simple MCP Server Connectivity Test
# This script uses minimal tools available in most containers

echo "=== Simple MCP Server Connectivity Test ==="
echo ""

# Configuration
PORT=8000
HOSTS=("localhost" "127.0.0.1" "host.docker.internal" "172.17.0.1" "192.168.1.7")

# Check if curl is available
if command -v curl >/dev/null 2>&1; then
    HAS_CURL=true
    echo "✓ curl is available - will use it for testing"
else
    HAS_CURL=false
    echo "✗ curl not available - some tests will be skipped"
fi

# Basic container info
echo ""
echo "Container information:"
echo "Hostname: $(hostname 2>/dev/null || echo 'unknown')"
echo ""

# Try to test connectivity with /dev/tcp (bash built-in)
echo "Testing TCP connectivity:"
for host in "${HOSTS[@]}"; do
    echo -n "TCP connection to $host:$PORT: "
    # Use timeout to avoid hanging if connection fails
    timeout 2 bash -c "echo > /dev/tcp/$host/$PORT" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Success ✓"
        WORKING_HOST=$host
    else
        echo "Failed ✗"
    fi
done
echo ""

# Use curl if available
if [ "$HAS_CURL" = true ]; then
    echo "Testing HTTP connectivity with curl:"
    for host in "${HOSTS[@]}"; do
        echo -n "HTTP request to $host:$PORT: "
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 http://$host:$PORT 2>/dev/null)
        if [ $? -eq 0 ] && [ "$HTTP_STATUS" != "000" ]; then
            echo "Success ✓ (Status: $HTTP_STATUS)"
        else
            echo "Failed ✗"
        fi
    done
    echo ""
fi

# Check if we found a working host
if [ -n "$WORKING_HOST" ]; then
    echo "✅ Found working connection to MCP server via: $WORKING_HOST:$PORT"
    echo "   Use this host in your MCP component configuration"
else
    echo "❌ Could not connect to the MCP server from this container"
    echo ""
    echo "Recommendations:"
    echo "1. Make sure the MCP server is running"
    echo "2. The server is currently listening only on 127.0.0.1"
    echo "3. Either:"
    echo "   a) Restart the server with --host 0.0.0.0, or"
    echo "   b) Use Docker with host networking mode (already added to docker-compose.yml)"
    echo "   c) Use port forwarding to expose the port to Docker"
fi

echo ""
echo "=== Test Complete ===" 