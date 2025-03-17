#!/bin/bash
# Docker-to-Host Connectivity Test Script for MCP
# Run this inside your Docker container to diagnose connection issues

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'

# Configuration
PORT=8000
HOSTS=("localhost" "127.0.0.1" "host.docker.internal" "172.17.0.1" "192.168.1.7")
TIMEOUT=2

echo -e "${BLUE}==============================================${NC}"
echo -e "${BLUE}= Docker-to-Host MCP Connection Test Script =${NC}"
echo -e "${BLUE}==============================================${NC}"
echo ""

# Make sure we have sudo or root access
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${YELLOW}Notice: Script not running as root. Some commands might fail.${NC}"
    # Checking if sudo is available
    if command -v sudo >/dev/null 2>&1; then
        USE_SUDO=true
        echo -e "${GREEN}Will use sudo for privileged commands.${NC}"
    else
        USE_SUDO=false
        echo -e "${YELLOW}Sudo not available. Will attempt to continue without it.${NC}"
    fi
else
    USE_SUDO=false
fi

# Function to run a command with sudo if needed
run_cmd() {
    if [ "$USE_SUDO" = true ]; then
        sudo "$@"
    else
        "$@"
    fi
}

# Install necessary tools based on the available package manager
echo -e "${YELLOW}Installing required tools...${NC}"
if command -v apt-get >/dev/null 2>&1; then
    echo -e "Using apt-get package manager..."
    if [ "$USE_SUDO" = true ]; then
        sudo apt-get update -y >/dev/null 2>&1
        sudo apt-get install -y iputils-ping curl wget netcat-openbsd net-tools iproute2 traceroute >/dev/null 2>&1
    else
        apt-get update -y >/dev/null 2>&1
        apt-get install -y iputils-ping curl wget netcat-openbsd net-tools iproute2 traceroute >/dev/null 2>&1
    fi
elif command -v yum >/dev/null 2>&1; then
    echo -e "Using yum package manager..."
    if [ "$USE_SUDO" = true ]; then
        sudo yum install -y iputils curl wget nc net-tools iproute traceroute >/dev/null 2>&1
    else
        yum install -y iputils curl wget nc net-tools iproute traceroute >/dev/null 2>&1
    fi
elif command -v apk >/dev/null 2>&1; then
    echo -e "Using apk package manager (Alpine Linux)..."
    if [ "$USE_SUDO" = true ]; then
        sudo apk add --no-cache iputils curl wget netcat-openbsd net-tools iproute2 traceroute >/dev/null 2>&1
    else
        apk add --no-cache iputils curl wget netcat-openbsd net-tools iproute2 traceroute >/dev/null 2>&1
    fi
else
    echo -e "${RED}No supported package manager found. Will try to use existing tools.${NC}"
fi
echo -e "${GREEN}Done with tool installation!${NC}"
echo ""

# Verify critical tools are available
echo -e "${YELLOW}Checking for required tools:${NC}"
MISSING_TOOLS=()
for tool in ping curl nc wget ip hostname netstat traceroute; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        MISSING_TOOLS+=("$tool")
        echo -e "${RED}✗ $tool not found${NC}"
    else
        echo -e "${GREEN}✓ $tool available${NC}"
    fi
done

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo -e "${YELLOW}Some tools are missing. Test results may be incomplete.${NC}"
fi
echo ""

# Get container network info - use fallbacks for critical commands
echo -e "${YELLOW}Container Network Information:${NC}"

# Get container IP
if command -v hostname >/dev/null 2>&1; then
    if hostname -I >/dev/null 2>&1; then
        CONTAINER_IP=$(hostname -I | awk '{print $1}')
    else
        # Fallback if hostname -I doesn't work
        CONTAINER_IP=$(ip -4 addr show scope global | grep inet | awk '{print $2}' | cut -d/ -f1 | head -n 1)
    fi
else
    CONTAINER_IP="unknown"
fi
echo -e "Container IP: ${CONTAINER_IP}"

# Get container hostname
if command -v hostname >/dev/null 2>&1; then
    CONTAINER_HOSTNAME=$(hostname)
else
    CONTAINER_HOSTNAME="unknown"
fi
echo -e "Container hostname: ${CONTAINER_HOSTNAME}"

# Get default gateway
if command -v ip >/dev/null 2>&1; then
    DEFAULT_GATEWAY=$(ip route | grep default | awk '{print $3}' | head -n 1)
    if [ -z "$DEFAULT_GATEWAY" ]; then
        DEFAULT_GATEWAY="unknown"
    fi
else
    DEFAULT_GATEWAY="unknown"
fi
echo -e "Default gateway: ${DEFAULT_GATEWAY}"
echo ""

# Try to resolve host.docker.internal - with fallbacks
echo -ne "host.docker.internal resolves to: "
if command -v getent >/dev/null 2>&1; then
    DOCKER_INTERNAL_IP=$(getent hosts host.docker.internal | awk '{ print $1 }')
elif command -v dig >/dev/null 2>&1; then
    DOCKER_INTERNAL_IP=$(dig +short host.docker.internal)
elif command -v nslookup >/dev/null 2>&1; then
    DOCKER_INTERNAL_IP=$(nslookup host.docker.internal | grep -A2 Name | grep Address | awk '{print $2}')
else
    # Try ping as last resort
    DOCKER_INTERNAL_IP=$(ping -c 1 host.docker.internal 2>/dev/null | grep PING | awk -F'[()]' '{print $2}')
fi

if [ -z "$DOCKER_INTERNAL_IP" ]; then
    echo -e "${RED}Not resolving${NC}"
    # If we can't resolve, add likely host gateway as a test target
    if [ "$DEFAULT_GATEWAY" != "unknown" ]; then
        HOSTS+=("$DEFAULT_GATEWAY")
        echo -e "Adding default gateway ${DEFAULT_GATEWAY} to test targets"
    fi
else
    echo -e "${GREEN}$DOCKER_INTERNAL_IP${NC}"
    # Add to hosts list if not already there
    if [[ ! " ${HOSTS[@]} " =~ " ${DOCKER_INTERNAL_IP} " ]]; then
        HOSTS+=("$DOCKER_INTERNAL_IP")
    fi
fi
echo ""

# Test connectivity to each host (ping)
echo -e "${YELLOW}Testing ping connectivity:${NC}"
if command -v ping >/dev/null 2>&1; then
    for host in "${HOSTS[@]}"; do
        echo -ne "Ping to $host: "
        if ping -c 1 -W $TIMEOUT $host > /dev/null 2>&1; then
            echo -e "${GREEN}Success${NC}"
        else
            echo -e "${RED}Failed${NC}"
        fi
    done
else
    echo -e "${RED}Ping command not available${NC}"
fi
echo ""

# Test TCP connectivity to port
echo -e "${YELLOW}Testing port connectivity (TCP/$PORT):${NC}"
if command -v nc >/dev/null 2>&1; then
    for host in "${HOSTS[@]}"; do
        echo -ne "TCP connection to $host:$PORT: "
        if nc -z -w $TIMEOUT $host $PORT > /dev/null 2>&1; then
            echo -e "${GREEN}Success${NC} (Port is open)"
        else
            echo -e "${RED}Failed${NC} (Port is closed or unreachable)"
        fi
    done
else
    echo -e "${RED}nc (netcat) command not available${NC}"
fi
echo ""

# Test HTTP connectivity
echo -e "${YELLOW}Testing HTTP connectivity:${NC}"
if command -v curl >/dev/null 2>&1; then
    for host in "${HOSTS[@]}"; do
        echo -ne "HTTP request to http://$host:$PORT: "
        HTTP_STATUS=$(curl --connect-timeout $TIMEOUT -s -o /dev/null -w "%{http_code}" http://$host:$PORT 2>/dev/null)
        if [ $? -eq 0 ] && [ "$HTTP_STATUS" != "000" ]; then
            echo -e "${GREEN}Success${NC} (HTTP Status: $HTTP_STATUS)"
        else
            echo -e "${RED}Failed${NC}"
        fi
    done
else
    echo -e "${RED}curl command not available${NC}"
fi
echo ""

# Check route to host.docker.internal
echo -e "${YELLOW}Tracing route to host.docker.internal:${NC}"
if command -v traceroute > /dev/null 2>&1; then
    traceroute -m 5 -w 2 host.docker.internal
else
    echo -e "${RED}Traceroute not available${NC}"
fi
echo ""

# Analyze and recommend
echo -e "${YELLOW}Analysis and Recommendations:${NC}"

# Check if any host was reachable
REACHABLE=false
WORKING_HOST=""
if command -v nc >/dev/null 2>&1; then
    for host in "${HOSTS[@]}"; do
        if nc -z -w $TIMEOUT $host $PORT > /dev/null 2>&1; then
            REACHABLE=true
            WORKING_HOST=$host
            break
        fi
    done
elif command -v curl >/dev/null 2>&1; then
    # Fallback to curl if nc not available
    for host in "${HOSTS[@]}"; do
        if curl --connect-timeout $TIMEOUT -s http://$host:$PORT > /dev/null 2>&1; then
            REACHABLE=true
            WORKING_HOST=$host
            break
        fi
    done
fi

if [ "$REACHABLE" = true ]; then
    echo -e "${GREEN}✅ MCP server is reachable through $WORKING_HOST:$PORT${NC}"
    echo -e "- Use this host in your MCP component configuration"
else
    echo -e "${RED}❌ MCP server is not reachable from this container${NC}"
    echo -e "Possible causes and solutions:"
    echo -e "1. MCP server is not running - Start the server"
    echo -e "2. MCP server is listening only on 127.0.0.1 - Restart with '--host 0.0.0.0'"
    echo -e "3. Firewall is blocking connections - Check firewall settings"
    
    # Check if host.docker.internal is properly configured
    if [ -z "$DOCKER_INTERNAL_IP" ]; then
        echo -e "4. host.docker.internal is not resolving - Add '--add-host=host.docker.internal:host-gateway' to docker-compose.yml"
    fi
    
    # Suggestion to try the host's IP address
    echo -e "5. Try using your host machine's actual IP address: 192.168.1.7:$PORT"
fi

# Additional diagnostics with more fallbacks
echo -e "\n${YELLOW}Additional diagnostics for troubleshooting:${NC}"

# Network interfaces
echo -e "- Docker network interfaces:"
if command -v ifconfig >/dev/null 2>&1; then
    ifconfig | grep -A 1 eth0
elif command -v ip >/dev/null 2>&1; then
    ip addr show | grep -A 2 eth0
else
    echo -e "${RED}Network interface commands not available${NC}"
fi

# Active connections
echo -e "- Active network connections:"
if command -v netstat >/dev/null 2>&1; then
    netstat -tulpn | grep -E "$PORT|LISTEN"
elif command -v ss >/dev/null 2>&1; then
    ss -tulpn | grep -E "$PORT|LISTEN"
else
    echo -e "${RED}Network connection commands not available${NC}"
fi

# Routing
echo -e "- Docker network routing:"
if command -v ip >/dev/null 2>&1; then
    ip route
elif command -v route >/dev/null 2>&1; then
    route -n
else
    echo -e "${RED}Routing commands not available${NC}"
fi

echo -e "\n${BLUE}==============================================${NC}"
echo -e "${BLUE}=                 TEST COMPLETE               =${NC}"
echo -e "${BLUE}==============================================${NC}" 