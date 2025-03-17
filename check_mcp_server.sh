#!/bin/bash
# MCP Server Configuration Checker
# Run this on your host system to verify MCP server configuration

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'

# Configuration
PORT=8000

echo -e "${BLUE}==============================================${NC}"
echo -e "${BLUE}=       MCP Server Configuration Check       =${NC}"
echo -e "${BLUE}==============================================${NC}"
echo ""

# Get host system information
echo -e "${YELLOW}Host System Information:${NC}"
echo -e "Hostname: $(hostname)"
echo -e "IP Addresses:"
ip -4 addr | grep -v "127.0.0.1" | grep "inet" | awk '{print "- " $2}' | cut -d/ -f1

# Check if the port is in use and what's using it
echo -e "\n${YELLOW}Checking MCP server port (TCP/$PORT):${NC}"
if command -v ss >/dev/null 2>&1; then
    # Use ss if available (more modern)
    PORT_STATUS=$(ss -tulpn | grep ":$PORT ")
elif command -v netstat >/dev/null 2>&1; then
    # Fallback to netstat
    PORT_STATUS=$(netstat -tulpn 2>/dev/null | grep ":$PORT ")
else
    PORT_STATUS=""
    echo -e "${RED}Neither ss nor netstat commands available${NC}"
fi

if [ -z "$PORT_STATUS" ]; then
    echo -e "${RED}❌ No process is listening on port $PORT${NC}"
    echo -e "The MCP server is not running or is using a different port."
else
    echo -e "${GREEN}✅ Found process listening on port $PORT:${NC}"
    echo -e "$PORT_STATUS"
    
    # Check if it's listening on localhost only or all interfaces
    if echo "$PORT_STATUS" | grep -q "127.0.0.1:$PORT"; then
        echo -e "${RED}⚠️ The server is only listening on localhost (127.0.0.1)${NC}"
        echo -e "Docker containers cannot connect to this server."
        echo -e "Recommendation: Configure your server to listen on all interfaces (0.0.0.0)"
    elif echo "$PORT_STATUS" | grep -q "0.0.0.0:$PORT"; then
        echo -e "${GREEN}✅ The server is correctly listening on all interfaces (0.0.0.0)${NC}"
        echo -e "Docker containers should be able to connect to this server."
    else
        echo -e "${YELLOW}⚠️ The server is listening on a specific interface${NC}"
        echo -e "Make sure Docker containers can reach this interface."
    fi
fi

# Try to make a local connection to the server
echo -e "\n${YELLOW}Testing local connection to MCP server:${NC}"
if command -v curl >/dev/null 2>&1; then
    # Test with curl
    echo -ne "Connection to localhost:$PORT: "
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT >/dev/null 2>&1; then
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT)
        echo -e "${GREEN}Success${NC} (HTTP Status: $STATUS)"
    else
        echo -e "${RED}Failed${NC}"
    fi

    # Test with 0.0.0.0 (all interfaces)
    echo -ne "Connection to 0.0.0.0:$PORT: "
    if curl -s -o /dev/null -w "%{http_code}" http://0.0.0.0:$PORT >/dev/null 2>&1; then
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://0.0.0.0:$PORT)
        echo -e "${GREEN}Success${NC} (HTTP Status: $STATUS)"
    else
        echo -e "${RED}Failed${NC}"
    fi
else
    echo -e "${RED}curl command not available${NC}"
fi

# Check firewall status
echo -e "\n${YELLOW}Checking firewall status:${NC}"
if command -v ufw >/dev/null 2>&1; then
    UFW_STATUS=$(ufw status)
    echo -e "UFW Firewall Status:"
    echo -e "$UFW_STATUS"
    
    if echo "$UFW_STATUS" | grep -q "Status: active"; then
        if echo "$UFW_STATUS" | grep -q "$PORT/tcp"; then
            echo -e "${GREEN}✅ Port $PORT is allowed in the firewall${NC}"
        else
            echo -e "${RED}⚠️ Port $PORT is not explicitly allowed in the firewall${NC}"
            echo -e "You may need to add a rule: sudo ufw allow $PORT/tcp"
        fi
    fi
elif command -v iptables >/dev/null 2>&1; then
    echo -e "IPTables Rules for port $PORT:"
    iptables -L -n | grep -i "$PORT" || echo "No specific rules found for port $PORT"
else
    echo -e "${YELLOW}Could not determine firewall status${NC}"
fi

echo -e "\n${YELLOW}Recommendations:${NC}"
echo -e "1. If the MCP server is only listening on 127.0.0.1, restart it with:"
echo -e "   ${BLUE}python your_mcp_server.py --host 0.0.0.0 --port $PORT${NC}"
echo -e "   or for FastAPI/Uvicorn:"
echo -e "   ${BLUE}uvicorn main:app --host 0.0.0.0 --port $PORT${NC}"
echo -e "2. Check that port $PORT is not blocked by firewall"
echo -e "3. In your Docker configuration, use your host's actual IP instead of localhost:"
echo -e "   ${BLUE}$(hostname -I | awk '{print $1}'):$PORT${NC}"

echo -e "\n${BLUE}==============================================${NC}"
echo -e "${BLUE}=              CHECK COMPLETE               =${NC}"
echo -e "${BLUE}==============================================${NC}" 