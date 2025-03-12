#!/bin/bash
#
# Kubernetes Metrics Generator Runner
# This script provides a user-friendly way to run the Kubernetes metrics generator
# for use with the AI Anomaly Analysis system.
#
# Note: This script is primarily intended for generating metrics that can be analyzed
# by the AI Anomaly Analysis system. The direct dashboard visualization functionality
# has been deprecated.

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# Set environment variables and Python path
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
HTTP_PORT=8085
PODS=50
INTERVAL=5
ANOMALIES=""
BACKGROUND=false

# Banner
echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}      Kubernetes Metrics Generator Runner${NC}"
echo -e "${BLUE}==================================================${NC}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --pods)
      PODS="$2"
      shift 2
      ;;
    --pods=*)
      PODS="${1#*=}"
      shift
      ;;
    --port)
      HTTP_PORT="$2"
      shift 2
      ;;
    --port=*)
      HTTP_PORT="${1#*=}"
      shift
      ;;
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    --interval=*)
      INTERVAL="${1#*=}"
      shift
      ;;
    --anomalies)
      ANOMALIES="--anomalies"
      shift
      ;;
    --background)
      BACKGROUND=true
      shift
      ;;
    --help)
      echo -e "\n${YELLOW}Usage:${NC}"
      echo -e "  $0 [options]"
      echo -e "\n${YELLOW}Options:${NC}"
      echo -e "  --pods N            Number of pods to simulate (default: 50)"
      echo -e "  --port N            HTTP port for metrics server (default: 8085)"
      echo -e "  --interval N        Update interval in seconds (default: 5)"
      echo -e "  --anomalies         Generate occasional anomalies in metrics"
      echo -e "  --background        Run in the background"
      echo -e "  --help              Display this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo -e "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Find an available port
port_available() {
  ! netstat -tuln | grep -q ":$1 "
}

# If the specified port is already in use, find the next available port
if ! port_available $HTTP_PORT; then
  echo -e "${YELLOW}Port $HTTP_PORT is already in use. Finding an available port...${NC}"
  while ! port_available $HTTP_PORT; do
    HTTP_PORT=$((HTTP_PORT + 1))
  done
  echo -e "${GREEN}Using port $HTTP_PORT${NC}"
fi

# Construct the command
cmd="python3 scripts/k8s_dummy_data_generator.py --pods $PODS --http-port $HTTP_PORT --interval $INTERVAL"

# Add optional arguments
if [ -n "$ANOMALIES" ]; then
  cmd="$cmd $ANOMALIES"
  echo -e "${YELLOW}Anomaly generation is enabled.${NC}"
fi

# Print information
echo -e "\n${BLUE}Generator Configuration:${NC}"
echo -e "  Number of pods: ${GREEN}$PODS${NC}"
echo -e "  HTTP port: ${GREEN}$HTTP_PORT${NC}"
echo -e "  Update interval: ${GREEN}$INTERVAL${NC} seconds"

# Run in background if requested
if [ "$BACKGROUND" = true ]; then
  echo -e "\n${BLUE}Running generator in the background...${NC}"
  
  # Run the generator and export all output to a log file
  LOGFILE="logs/k8s_metrics_$(date +%Y%m%d_%H%M%S).log"
  mkdir -p logs
  
  # Run in the background
  nohup $cmd > "$LOGFILE" 2>&1 &
  PID=$!
  
  echo -e "${GREEN}Generator started with PID: $PID${NC}"
  echo -e "Log file: ${GREEN}$LOGFILE${NC}"
  echo -e "Run ${YELLOW}tail -f $LOGFILE${NC} to view output"
  echo -e "Use ${YELLOW}./kill_k8s_generators.sh${NC} to stop the generator"
  
  exit 0
fi

# Run in the foreground
echo -e "\n${BLUE}=== Starting Metrics Generator ===${NC}"
echo -e "Running command: ${cmd}"
echo -e "Press Ctrl+C to stop the generator\n"

# Ask if the user wants to run AI analysis after completion
echo -e "${YELLOW}Would you like to run AI analysis on metrics after stopping the generator? [Y/n]${NC}"
read -r run_ai_analysis
run_ai_analysis=${run_ai_analysis:-"y"}

# Run the command
$cmd

# Final message
echo -e "\n${GREEN}Generator stopped.${NC}"
echo -e "If the metrics were collected by Prometheus, you should be able to view them in Grafana."

# Run AI analysis if requested
if [[ "${run_ai_analysis,,}" =~ ^(y|yes)$ ]]; then
  echo -e "\n${BLUE}=== Running AI Anomaly Analysis ===${NC}"
  
  # Check if the AI analysis script exists
  if [ ! -f "scripts/ai_anomaly_analysis.py" ]; then
    echo -e "${RED}AI analysis script not found at scripts/ai_anomaly_analysis.py${NC}"
    exit 1
  fi
  
  # Give Prometheus a moment to ingest the latest metrics
  echo -e "${YELLOW}Waiting 10 seconds for metrics to be processed...${NC}"
  sleep 10
  
  # Run the AI analysis
  echo -e "${GREEN}Running AI analysis...${NC}"
  ./mcp_run ai-analyze --timeframe=1h
fi

