#!/bin/bash
# Script to set up proper permissions for Prometheus configuration files
# This works regardless of which user account is running it

# Color formatting
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up Prometheus file permissions...${NC}"

# Make sure the prometheus directory exists
if [ ! -d "./prometheus" ]; then
    echo -e "${RED}Error: ./prometheus directory not found!${NC}"
    echo "Please run this script from the root of your project directory."
    exit 1
fi

# Create prometheus.yml if it doesn't exist
if [ ! -f "./prometheus/prometheus.yml" ]; then
    echo -e "${YELLOW}prometheus.yml not found. Creating a basic configuration...${NC}"
    mkdir -p ./prometheus
    cat > ./prometheus/prometheus.yml << 'EOL'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          # - alertmanager:9093

rule_files:
  - "memory_alerts.yml"

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
  
  - job_name: "node"
    static_configs:
      - targets: ["node-exporter:9100"]
  
  - job_name: "cadvisor"
    static_configs:
      - targets: ["cadvisor:8080"]
EOL
fi

# Create memory_alerts.yml if it doesn't exist
if [ ! -f "./prometheus/memory_alerts.yml" ]; then
    echo -e "${YELLOW}memory_alerts.yml not found. Creating a basic alerts configuration...${NC}"
    cat > ./prometheus/memory_alerts.yml << 'EOL'
groups:
- name: memory_alerts
  rules:
  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High Memory Usage on {{ $labels.instance }}"
      description: "Memory usage is above 80% for 5 minutes.\n  VALUE = {{ $value }}%\n  LABELS: {{ $labels }}"
  
  - alert: CriticalMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 95
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Critical Memory Usage on {{ $labels.instance }}"
      description: "Memory usage is above 95% for 1 minute.\n  VALUE = {{ $value }}%\n  LABELS: {{ $labels }}"
EOL
fi

# Get the user running the script
CURRENT_USER=$(id -u)
CURRENT_GROUP=$(id -g)
CURRENT_USER_NAME=$(id -un)

# Method 1: Set file ownership to the current user
echo -e "${YELLOW}Method 1: Setting file ownership to your user (${CURRENT_USER_NAME})${NC}"
sudo chown -v $CURRENT_USER:$CURRENT_GROUP ./prometheus ./prometheus/*.yml

# Method 2: Set world-readable permissions
echo -e "${YELLOW}Method 2: Setting world-readable permissions${NC}"
sudo chmod -v 755 ./prometheus
sudo chmod -v 644 ./prometheus/*.yml

# Reset the Prometheus data volume if it exists
echo -e "${YELLOW}Would you like to reset the Prometheus data volume? (fixes query permission issues)${NC}"
echo -e "${YELLOW}Note: This will delete all Prometheus metrics history${NC}"
read -p "Reset data volume? (y/n): " RESET_VOLUME

if [[ $RESET_VOLUME == "y" || $RESET_VOLUME == "Y" ]]; then
    echo -e "${YELLOW}Stopping Prometheus container...${NC}"
    docker compose stop prometheus
    
    echo -e "${YELLOW}Removing Prometheus data volume...${NC}"
    docker volume rm prometheus_data 2>/dev/null || true
    
    echo -e "${GREEN}Prometheus data volume has been reset.${NC}"
    echo -e "${YELLOW}You can now restart Prometheus with:${NC}"
    echo -e "  docker compose up -d prometheus"
fi

# Option to use working configuration without volumes
echo -e "${YELLOW}Would you like to switch to a simpler configuration without persistent volumes?${NC}"
echo -e "${YELLOW}This is more like your original working setup.${NC}"
read -p "Use simpler configuration? (y/n): " USE_SIMPLE

if [[ $USE_SIMPLE == "y" || $USE_SIMPLE == "Y" ]]; then
    # Create a temporary file
    TMP_FILE=$(mktemp)
    
    # Update the docker-compose.yml file to use a simpler configuration
    awk '
    /prometheus_data:\/prometheus/ {
        next;  # Skip this line
    }
    {print}' docker-compose.yml > "$TMP_FILE"
    
    # Replace the original file
    mv "$TMP_FILE" docker-compose.yml
    
    echo -e "${GREEN}Updated docker-compose.yml to use a simpler configuration without volumes.${NC}"
    echo -e "${YELLOW}You may need to rebuild your Prometheus container:${NC}"
    echo -e "  docker compose up -d --force-recreate prometheus"
fi

echo -e "${GREEN}Setup complete! Prometheus configuration files should now have the correct permissions.${NC}"
echo -e "${YELLOW}You can now run:${NC}"
echo -e "  docker compose up -d"
echo -e "  or"
echo -e "  docker compose restart prometheus" 