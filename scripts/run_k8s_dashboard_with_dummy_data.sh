#!/bin/bash
# Kubernetes Dashboard With Dummy Data Runner
# This script updates the Grafana dashboard to use dummy data and starts the data generator

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Set environment variables and Python path
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PODS=25
HTTP_PORT=9092
INTERVAL=15
ANOMALIES=""
UPDATE_DASHBOARD="yes"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --pods=*)
      PODS="${1#*=}"
      shift
      ;;
    --port=*)
      HTTP_PORT="${1#*=}"
      shift
      ;;
    --interval=*)
      INTERVAL="${1#*=}"
      shift
      ;;
    --anomalies)
      ANOMALIES="--anomalies"
      shift
      ;;
    --no-dashboard-update)
      UPDATE_DASHBOARD="no"
      shift
      ;;
    --help)
      echo -e "${BLUE}Kubernetes Dashboard With Dummy Data Runner${NC}"
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --pods=N             Number of pods to simulate (default: 25)"
      echo "  --port=N             HTTP port for metrics server (default: 9092)"
      echo "  --interval=N         Update interval in seconds (default: 15)"
      echo "  --anomalies          Generate occasional anomalies"
      echo "  --no-dashboard-update  Skip dashboard update"
      echo "  --help               Show this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}=== Kubernetes Dashboard With Dummy Data ====${NC}"

# Check if docker and docker-compose are running
if ! command -v docker &>/dev/null; then
  echo -e "${RED}Docker is not installed. This script requires Docker to run Prometheus and Grafana.${NC}"
  exit 1
fi

# Check if docker-compose is available
if ! command -v docker compose &>/dev/null; then
  echo -e "${RED}Docker Compose is not installed. This script requires Docker Compose.${NC}"
  exit 1
fi

# Check if services are running
if ! docker compose ps | grep -q prometheus; then
  echo -e "${YELLOW}Prometheus container doesn't appear to be running.${NC}"
  echo -e "Would you like to start the services with 'docker compose up -d'? [y/N] "
  read -r start_services
  if [[ "$start_services" =~ ^[Yy]$ ]]; then
    echo "Starting services..."
    (cd "$PROJECT_ROOT" && docker compose up -d)
  else
    echo -e "${RED}Prometheus is required for this demo. Exiting.${NC}"
    exit 1
  fi
fi

# Update the dashboard if requested
if [ "$UPDATE_DASHBOARD" = "yes" ]; then
  echo -e "\n${BLUE}Updating Kubernetes dashboard to use dummy metrics...${NC}"
  (cd "$PROJECT_ROOT" && python3 -m scripts.k8s_dashboard_data_populator --update --add-datasource)
  
  echo -e "\n${GREEN}Dashboard updated successfully!${NC}"
  
  echo -e "Would you like to restart Grafana to apply changes? [y/N] "
  read -r restart_grafana
  if [[ "$restart_grafana" =~ ^[Yy]$ ]]; then
    echo "Restarting Grafana..."
    (cd "$PROJECT_ROOT" && docker compose restart grafana)
    echo -e "${GREEN}Grafana restarted. Changes should be visible.${NC}"
  fi
fi

# Check if the port is already in use
check_port() {
  local port=$1
  if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
    return 0  # Port is in use
  else
    return 1  # Port is free
  fi
}

# Find an available port starting from the given port
find_available_port() {
  local port=$1
  while check_port $port; do
    echo -e "${YELLOW}Port $port is already in use, trying next port...${NC}"
    port=$((port + 1))
  done
  echo $port
}

# Start the dummy data generator
echo -e "\n${BLUE}Starting Kubernetes metrics generator...${NC}"
echo -e "Generating metrics for ${YELLOW}$PODS${NC} pods"

# Find an available port
HTTP_PORT=$(find_available_port $HTTP_PORT)
echo -e "HTTP server on port ${YELLOW}$HTTP_PORT${NC}"

echo -e "Update interval: ${YELLOW}$INTERVAL${NC} seconds"
if [ -n "$ANOMALIES" ]; then
  echo -e "Anomaly generation: ${YELLOW}enabled${NC}"
else
  echo -e "Anomaly generation: ${YELLOW}disabled${NC}"
fi

# Update Prometheus config with the selected port
if [ "$UPDATE_DASHBOARD" = "yes" ]; then
  echo -e "\n${BLUE}Updating Prometheus configuration to scrape metrics from port $HTTP_PORT...${NC}"
  (cd "$PROJECT_ROOT" && python3 -m scripts.update_prometheus_config --port $HTTP_PORT)
  
  echo -e "\n${GREEN}Prometheus configuration updated!${NC}"
  
  echo -e "Would you like to restart Prometheus to apply changes? [y/N] "
  read -r restart_prometheus
  if [[ "$restart_prometheus" =~ ^[Yy]$ ]]; then
    echo "Restarting Prometheus..."
    (cd "$PROJECT_ROOT" && docker compose restart prometheus)
    echo -e "${GREEN}Prometheus restarted. Changes should be visible.${NC}"
  fi
fi

echo -e "\n${BLUE}Starting generator...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the generator when done${NC}"
(cd "$PROJECT_ROOT" && python3 -m scripts.k8s_dummy_data_generator --pods $PODS --http-port $HTTP_PORT --interval $INTERVAL $ANOMALIES) 