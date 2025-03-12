#!/bin/bash
# Script to generate anomalies for testing the Kubernetes performance monitoring dashboard

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}Kubernetes Performance Anomaly Generator${NC}"
echo -e "${BLUE}============================================${NC}"

# Install required Python packages if needed
check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"
    
    # Check if numpy is installed
    if python3 -c "import numpy" 2>/dev/null; then
        echo -e "${GREEN}✓ numpy is installed${NC}"
    else
        echo -e "${RED}× numpy is not installed. Installing...${NC}"
        pip install numpy
    fi
    
    # Check if we can run the script 
    if [ -f "scripts/generate_test_anomalies.py" ]; then
        echo -e "${GREEN}✓ Anomaly generator script found${NC}"
    else
        echo -e "${RED}× Anomaly generator script not found at scripts/generate_test_anomalies.py${NC}"
        exit 1
    fi
    
    # Check Docker
    if command -v docker >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Docker is installed${NC}"
    else
        echo -e "${YELLOW}! Docker is not installed. Some anomaly types will not work.${NC}"
    fi
}

# Show menu of anomaly types
show_menu() {
    echo ""
    echo -e "${BLUE}What type of anomalies would you like to generate?${NC}"
    echo -e "${YELLOW}1)${NC} All anomalies (CPU, Memory, Disk, Network)"
    echo -e "${YELLOW}2)${NC} CPU stress only"
    echo -e "${YELLOW}3)${NC} Memory stress only"
    echo -e "${YELLOW}4)${NC} Disk I/O stress only"
    echo -e "${YELLOW}5)${NC} Network stress only"
    echo -e "${YELLOW}6)${NC} Docker container stress"
    echo -e "${YELLOW}7)${NC} Exit"
    echo ""
}

# Generate anomalies based on user choice
generate_anomalies() {
    local choice=$1
    local duration=$2
    
    case $choice in
        1)
            echo -e "${BLUE}Generating all anomalies for ${duration} seconds...${NC}"
            python3 scripts/generate_test_anomalies.py --all --duration $duration
            ;;
        2)
            echo -e "${BLUE}Generating CPU stress for ${duration} seconds...${NC}"
            python3 scripts/generate_test_anomalies.py --cpu --duration $duration
            ;;
        3)
            echo -e "${BLUE}Generating memory stress for ${duration} seconds...${NC}"
            python3 scripts/generate_test_anomalies.py --memory --duration $duration
            ;;
        4)
            echo -e "${BLUE}Generating disk I/O stress for ${duration} seconds...${NC}"
            python3 scripts/generate_test_anomalies.py --disk --duration $duration
            ;;
        5)
            echo -e "${BLUE}Generating network stress for ${duration} seconds...${NC}"
            python3 scripts/generate_test_anomalies.py --network --duration $duration
            ;;
        6)
            echo -e "${BLUE}Generating Docker container stress for ${duration} seconds...${NC}"
            python3 scripts/generate_test_anomalies.py --docker --duration $duration
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            return 1
            ;;
    esac
    
    # After generating anomalies, give Prometheus time to record the metrics
    echo -e "${YELLOW}Waiting for anomaly metrics to be collected...${NC}"
    sleep 30
    
    # Trigger anomaly detection
    echo -e "${YELLOW}Triggering anomaly detection scan...${NC}"
    curl -s -X POST "http://localhost:8086/api/anomaly/run" \
        -H "Content-Type: application/json" \
        -d '{"node_filter": ".*"}'
    
    echo -e "${GREEN}Anomaly detection scan triggered${NC}"
    echo -e "${YELLOW}Wait 30 seconds for the scan to complete...${NC}"
    sleep 30
    
    # Check for anomalies
    echo -e "${YELLOW}Getting anomaly detection results...${NC}"
    curl -s "http://localhost:8086/api/anomaly/latest" | jq .
}

# Main execution
check_dependencies

# Get duration from command line or ask user
if [ -n "$1" ]; then
    duration=$1
else
    echo -e "${YELLOW}How long should the anomalies run? (seconds)${NC}"
    read -p "> " duration
    # Default to 120 seconds if empty
    duration=${duration:-120}
fi

# Main loop
while true; do
    show_menu
    read -p "Enter your choice (1-7): " choice
    
    if [ "$choice" == "7" ]; then
        echo -e "${GREEN}Exiting. Don't forget to check your dashboards!${NC}"
        break
    fi
    
    generate_anomalies $choice $duration
    
    echo ""
    echo -e "${YELLOW}Would you like to generate more anomalies? (y/n)${NC}"
    read -p "> " continue_choice
    if [ "$continue_choice" != "y" ]; then
        echo -e "${GREEN}Exiting. Don't forget to check your dashboards!${NC}"
        break
    fi
done

echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}Grafana dashboard URL: http://localhost:3000${NC}"
echo -e "${GREEN}Prometheus URL: http://localhost:9090${NC}"
echo -e "${BLUE}============================================${NC}" 