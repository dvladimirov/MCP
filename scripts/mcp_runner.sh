#!/bin/bash
# MCP Runner - Unified Test and Runner Script
# This script provides a user-friendly interface to run all MCP tests and tools

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
# Go to the project root directory (parent of scripts directory)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Set environment variables for OpenAI models if needed
export OPENAI_CHAT_MODEL="${OPENAI_CHAT_MODEL:-gpt-4o-mini}"
export OPENAI_COMPLETION_MODEL="${OPENAI_COMPLETION_MODEL:-gpt-3.5-turbo-instruct}"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to display header
display_header() {
  clear
  echo -e "${BLUE}=================================================${NC}"
  echo -e "${GREEN}          MCP Test & Tool Runner${NC}"
  echo -e "${BLUE}=================================================${NC}"
  echo -e "${YELLOW}Working directory: ${NC}$(pwd)"
  echo -e "${YELLOW}Using chat model: ${NC}${OPENAI_CHAT_MODEL}"
  echo -e "${YELLOW}Using completion model: ${NC}${OPENAI_COMPLETION_MODEL}"
  echo ""
}

# Function to check if a command exists
command_exists() {
  command -v "$1" &>/dev/null
}

# Function to check if the MCP server is running
check_mcp_server() {
  if curl -s "http://localhost:8000/v1/models" >/dev/null; then
    echo -e "${GREEN}MCP server is running${NC}"
    return 0
  else
    echo -e "${RED}MCP server is not running${NC}"
    return 1
  fi
}

# Function to check if Prometheus is running
check_prometheus() {
  if curl -s "http://localhost:9090/api/v1/query?query=up" >/dev/null; then
    echo -e "${GREEN}Prometheus is running${NC}"
    return 0
  else
    echo -e "${RED}Prometheus is not running${NC}"
    return 1
  fi
}

# Function to check if Grafana is running
check_grafana() {
  if curl -s "http://localhost:3000/api/health" >/dev/null; then
    echo -e "${GREEN}Grafana is running${NC}"
    return 0
  else
    echo -e "${RED}Grafana is not running${NC}"
    return 1
  fi
}

# Function to check if MCP-Grafana is running
check_mcp_grafana() {
  if curl -s "http://localhost:8085/health" >/dev/null; then
    echo -e "${GREEN}MCP-Grafana is running${NC}"
    return 0
  else
    echo -e "${RED}MCP-Grafana is not running${NC}"
    return 1
  fi
}

# Function to check environment status
check_environment() {
  echo -e "${BLUE}Checking environment status:${NC}"
  # Check if uv is installed
  if command_exists uv; then
    echo -e "${GREEN}✓ uv is installed${NC}"
  else
    echo -e "${RED}✗ uv is not installed - required for running Python scripts${NC}"
  fi

  # Check if docker is installed
  if command_exists docker; then
    echo -e "${GREEN}✓ Docker is installed${NC}"
  else
    echo -e "${RED}✗ Docker is not installed - required for container tests${NC}"
  fi

  # Check if MCP server is running
  check_mcp_server

  # Check if Prometheus is running
  check_prometheus
  
  # Check if Grafana is running
  check_grafana
  
  # Check if MCP-Grafana is running
  check_mcp_grafana

  echo ""
}

# Function to start MCP server
start_mcp_server() {
  echo -e "${BLUE}Starting MCP server...${NC}"
  if check_mcp_server; then
    echo "MCP server already running"
  else
    echo "Starting MCP server in the background..."
    uv run scripts/start_mcp_server.py --prometheus-url "http://localhost:9090" --debug &
    MCP_PID=$!

    echo "Waiting for server to start..."
    sleep 5

    if check_mcp_server; then
      echo -e "${GREEN}MCP server started with PID: $MCP_PID${NC}"
    else
      echo -e "${RED}Failed to start MCP server${NC}"
    fi
  fi
}

# Function to start Prometheus stack
start_prometheus() {
  echo -e "${BLUE}Starting Prometheus stack...${NC}"
  if check_prometheus; then
    echo "Prometheus already running"
  else
    echo "Starting Prometheus services with Docker Compose..."
    docker compose up -d prometheus cadvisor node-exporter

    echo "Waiting for services to start..."
    sleep 10

    if check_prometheus; then
      echo -e "${GREEN}Prometheus services started successfully${NC}"
    else
      echo -e "${RED}Failed to start Prometheus services${NC}"
    fi
  fi
}

# Function to display main menu
display_main_menu() {
  display_header
  check_environment

  echo -e "${BLUE}Select a category:${NC}"
  echo -e "${YELLOW}1)${NC} Filesystem Tests"
  echo -e "${YELLOW}2)${NC} Git Integration Tests"
  echo -e "${YELLOW}3)${NC} Memory Analysis Tools"
  echo -e "${YELLOW}4)${NC} Prometheus Tests & Memory Stress"
  echo -e "${YELLOW}5)${NC} MCP Server Management"
  echo -e "${YELLOW}6)${NC} Environment Setup"
  echo -e "${YELLOW}7)${NC} Grafana Dashboards"
  echo -e "${YELLOW}0)${NC} Exit"
  echo ""
  read -p "Enter your choice (0-7): " main_choice

  case $main_choice in
  1) filesystem_menu ;;
  2) git_menu ;;
  3) memory_analysis_menu ;;
  4) prometheus_menu ;;
  5) mcp_server_menu ;;
  6) environment_setup_menu ;;
  7) grafana_menu ;;
  0) exit 0 ;;
  *)
    echo -e "${RED}Invalid choice. Press Enter to try again.${NC}"
    read
    display_main_menu
    ;;
  esac
}

# Filesystem Tests Menu
filesystem_menu() {
  display_header
  echo -e "${BLUE}Filesystem Tests:${NC}"
  echo -e "${YELLOW}1)${NC} Run Filesystem Test"
  echo -e "${YELLOW}2)${NC} Return to Main Menu"
  echo ""
  read -p "Enter your choice (1-2): " fs_choice

  case $fs_choice in
  1)
    echo -e "\n${BLUE}Running Filesystem Test...${NC}"
    uv run scripts/test_filesystem.py
    echo -e "\n${GREEN}Test completed. Press Enter to continue...${NC}"
    read
    ;;
  2)
    display_main_menu
    return
    ;;
  *)
    echo -e "${RED}Invalid choice. Press Enter to try again.${NC}"
    read
    filesystem_menu
    ;;
  esac

  filesystem_menu
}

# Git Integration Tests Menu
git_menu() {
  display_header
  echo -e "${BLUE}Git Integration Tests:${NC}"
  echo -e "${YELLOW}1)${NC} Run Git Diff Test"
  echo -e "${YELLOW}2)${NC} Run Git Integration Test"
  echo -e "${YELLOW}3)${NC} Return to Main Menu"
  echo ""
  read -p "Enter your choice (1-3): " git_choice

  case $git_choice in
  1)
    echo -e "\n${BLUE}Running Git Diff Test...${NC}"
    read -p "Enter repository URL: " repo_url
    read -p "Enter commit SHA to compare with (or press Enter to skip): " commit_sha
    
    if [ -z "$repo_url" ]; then
      echo -e "${RED}Repository URL is required.${NC}"
      read -p "Press Enter to continue..."
    else
      if [ -z "$commit_sha" ]; then
        # Run without commit SHA
        uv run scripts/test_git_diff.py "$repo_url"
      else
        # Run with commit SHA as a separate parameter
        uv run scripts/test_git_diff.py "$repo_url" "$commit_sha"
      fi
      echo -e "\n${GREEN}Test completed. Press Enter to continue...${NC}"
      read
    fi
    ;;
  2)
    echo -e "\n${BLUE}Running Git Integration Test...${NC}"
    read -p "Enter repository URL (or press Enter for default): " repo_url
    if [ -z "$repo_url" ]; then
      uv run scripts/test_git_integration.py
    else
      uv run scripts/test_git_integration.py "$repo_url"
    fi
    echo -e "\n${GREEN}Test completed. Press Enter to continue...${NC}"
    read
    ;;
  3)
    display_main_menu
    return
    ;;
  *)
    echo -e "${RED}Invalid choice. Press Enter to try again.${NC}"
    read
    git_menu
    ;;
  esac

  git_menu
}

# Memory Analysis Tools Menu
memory_analysis_menu() {
  display_header
  echo -e "${BLUE}Memory Analysis Tools:${NC}"
  echo -e "${YELLOW}1)${NC} AI Memory Diagnostics"
  echo -e "${YELLOW}2)${NC} Memory Dashboard"
  echo -e "${YELLOW}3)${NC} Run All Memory Analysis Tools"
  echo -e "${YELLOW}4)${NC} List Available AI Models"
  echo -e "${YELLOW}5)${NC} Return to Main Menu"
  echo ""
  read -p "Enter your choice (1-5): " mem_choice

  case $mem_choice in
  1)
    echo -e "\n${BLUE}Running AI Memory Diagnostics...${NC}"
    uv run scripts/ai_memory_diagnostics.py
    echo -e "\n${GREEN}Analysis completed. Press Enter to continue...${NC}"
    read
    ;;
  2)
    echo -e "\n${BLUE}Running Memory Dashboard...${NC}"
    read -p "Run once or continuous monitoring? (once/cont): " dashboard_mode
    if [ "$dashboard_mode" == "once" ]; then
      uv run scripts/mcp_memory_dashboard.py --once
    else
      echo "Press Ctrl+C to exit the dashboard when finished"
      uv run scripts/mcp_memory_dashboard.py
    fi
    echo -e "\n${GREEN}Dashboard closed. Press Enter to continue...${NC}"
    read
    ;;
  3)
    echo -e "\n${BLUE}Running all analysis tools...${NC}"

    echo -e "\n${PURPLE}1. Basic Prometheus test with AI recommendations${NC}"
    uv run scripts/test_prometheus.py --quiet

    echo -e "\n${PURPLE}2. AI Memory Diagnostics${NC}"
    uv run scripts/ai_memory_diagnostics.py

    echo -e "\n${PURPLE}3. Memory Dashboard (once)${NC}"
    uv run scripts/mcp_memory_dashboard.py --once

    echo -e "\n${GREEN}All analyses completed. Press Enter to continue...${NC}"
    read
    ;;
  4)
    echo -e "\n${BLUE}Listing available AI models...${NC}"
    uv run scripts/ai_memory_diagnostics.py --list-models
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  5)
    display_main_menu
    return
    ;;
  *)
    echo -e "${RED}Invalid choice. Press Enter to try again.${NC}"
    read
    memory_analysis_menu
    ;;
  esac

  memory_analysis_menu
}

# Prometheus Tests & Memory Stress Menu
prometheus_menu() {
  display_header
  echo -e "${BLUE}Prometheus Tests & Memory Stress:${NC}"
  echo -e "${YELLOW}1)${NC} Run Prometheus Test with AI Recommendations"
  echo -e "${YELLOW}2)${NC} Start Memory Stress Container"
  echo -e "${YELLOW}3)${NC} Stop Memory Stress Container"
  echo -e "${YELLOW}4)${NC} Show Container Status"
  echo -e "${YELLOW}5)${NC} Simulate Memory Pressure"
  echo -e "${YELLOW}6)${NC} Run Kubernetes Metrics Generator (for AI Analysis)"
  echo -e "${YELLOW}7)${NC} Run AI Anomaly Analysis"
  echo -e "${YELLOW}8)${NC} Return to Main Menu"
  echo ""
  read -p "Enter your choice (1-8): " prom_choice

  case $prom_choice in
  1)
    echo -e "\n${BLUE}Running Prometheus Test with AI Recommendations...${NC}"
    uv run scripts/test_prometheus.py --quiet
    echo -e "\n${GREEN}Test completed. Press Enter to continue...${NC}"
    read
    ;;
  2)
    echo -e "\n${BLUE}Starting Memory Stress Container...${NC}"

    # Check if memory-stress container already exists and remove it if it does
    if docker ps -a | grep -q memory-stress; then
      echo "Removing existing memory-stress container..."
      docker rm -f memory-stress
    fi

    # Build and start the memory-stress container
    docker compose up -d --build memory-stress

    echo -e "${GREEN}Memory stress container started.${NC}"
    echo "View Prometheus alerts at: http://localhost:9090/alerts"
    echo "View container metrics at: http://localhost:9090/graph?g0.expr=(container_memory_usage_bytes%7Bcontainer_name%3D%22memory-stress%22%7D%20%2F%20container_spec_memory_limit_bytes%7Bcontainer_name%3D%22memory-stress%22%7D)*100&g0.tab=0"
    echo "View memory stress container logs with: docker logs -f memory-stress"
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  3)
    echo -e "\n${BLUE}Stopping Memory Stress Container...${NC}"

    if docker ps | grep -q memory-stress; then
      docker compose stop memory-stress
      docker compose rm -f memory-stress
      echo -e "${GREEN}Memory stress container stopped and removed.${NC}"
    else
      echo -e "${YELLOW}Memory stress container is not running.${NC}"
    fi

    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  4)
    echo -e "\n${BLUE}Container Status:${NC}"

    echo -e "${PURPLE}Container Status:${NC}"
    docker ps | grep -E 'prometheus|cadvisor|node-exporter|memory-stress' || echo "No monitoring containers found"

    echo -e "\n${PURPLE}Prometheus API:${NC}"
    if curl -s "http://localhost:9090/api/v1/query?query=up" >/dev/null; then
      echo -e "${GREEN}Accessible${NC}"
    else
      echo -e "${RED}Not accessible${NC}"
    fi

    echo -e "\n${PURPLE}Current alerts:${NC}"
    alerts=$(curl -s "http://localhost:9090/api/v1/alerts" | grep -o '"name":"[^"]*"' | sed 's/"name":"//g' | sed 's/"//g')

    if [ -n "$alerts" ]; then
      echo -e "${YELLOW}Found:${NC}"
      echo "$alerts"
    else
      echo "None"
    fi

    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  5)
    echo -e "\n${BLUE}Simulating Memory Pressure...${NC}"

    # Ask for target percentage
    read -p "Enter target memory usage percentage (default: 85): " target_percent
    target_percent=${target_percent:-85}

    # Ask for duration
    read -p "Enter duration in seconds (default: 300): " duration
    duration=${duration:-300}

    # Run the simulation
    echo -e "${YELLOW}Starting memory pressure simulation with target $target_percent% for $duration seconds...${NC}"
    uv run scripts/simulate_memory_pressure.py --target $target_percent --duration $duration

    echo -e "\n${GREEN}Simulation completed. Press Enter to continue...${NC}"
    read
    ;;
  6)
    echo -e "\n${BLUE}Running Kubernetes Metrics Generator...${NC}"
    
    # Check if the metrics generator script exists
    if [ ! -f "$PROJECT_ROOT/scripts/k8s_dummy_data_generator.py" ]; then
      echo -e "${RED}Error: Kubernetes metrics generator script not found at $PROJECT_ROOT/scripts/k8s_dummy_data_generator.py${NC}"
      echo -e "\n${YELLOW}Press Enter to continue...${NC}"
      read
      return
    fi
    
    # Configuration options for the metrics generator
    read -p "Enter number of pods to simulate (default: 20): " pod_count
    pod_count=${pod_count:-20}
    
    read -p "Enter HTTP port for metrics server (default: 9091): " http_port
    http_port=${http_port:-9091}
    
    read -p "Generate intentional anomalies? (y/n, default: n): " generate_anomalies
    if [[ "$generate_anomalies" =~ ^[Yy]$ ]]; then
      ANOMALY_FLAG="--anomalies"
    else
      ANOMALY_FLAG=""
    fi
    
    read -p "Update interval in seconds (default: 5): " interval
    interval=${interval:-5}
    
    read -p "Run in background? (y/n, default: n): " run_background
    
    if [[ "$run_background" =~ ^[Yy]$ ]]; then
      # Run in background with log file
      LOGFILE="$PROJECT_ROOT/logs/k8s_metrics_$(date +%Y%m%d_%H%M%S).log"
      mkdir -p "$PROJECT_ROOT/logs"
      
      echo -e "${BLUE}Starting Kubernetes metrics generator in background...${NC}"
      echo -e "${YELLOW}Log file: $LOGFILE${NC}"
      
      uv run scripts/k8s_dummy_data_generator.py --pods $pod_count --http-port $http_port --interval $interval $ANOMALY_FLAG > "$LOGFILE" 2>&1 &
      GENERATOR_PID=$!
      
      echo -e "${GREEN}Metrics generator started with PID: $GENERATOR_PID${NC}"
      echo -e "${YELLOW}Use ${GREEN}./kill_k8s_generators.sh${YELLOW} to stop it when done${NC}"
      
    else
      # Run in foreground
      echo -e "${BLUE}Starting Kubernetes metrics generator...${NC}"
      echo -e "${YELLOW}Press Ctrl+C to stop when done${NC}"
      
      uv run scripts/k8s_dummy_data_generator.py --pods $pod_count --http-port $http_port --interval $interval $ANOMALY_FLAG
    fi
    
    # After generator completes (if in foreground), ask if user wants to run AI analysis
    if [[ ! "$run_background" =~ ^[Yy]$ ]]; then
      echo -e "\n${YELLOW}Would you like to run AI analysis on the metrics? (y/n)${NC}"
      read -p "> " run_analysis
      
      if [[ "$run_analysis" =~ ^[Yy]$ ]]; then
        if [ -f "$PROJECT_ROOT/scripts/ai_anomaly_analysis.py" ]; then
          echo -e "${BLUE}Running AI anomaly analysis...${NC}"
          uv run scripts/ai_anomaly_analysis.py
        else
          echo -e "${RED}Error: AI analysis script not found at $PROJECT_ROOT/scripts/ai_anomaly_analysis.py${NC}"
        fi
      fi
    fi
    
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  7)
    echo -e "\n${BLUE}Running AI Anomaly Analysis...${NC}"
    
    # Check if the AI analysis script exists
    if [ ! -f "$PROJECT_ROOT/scripts/ai_anomaly_analysis.py" ]; then
      echo -e "${RED}Error: AI anomaly analysis script not found at $PROJECT_ROOT/scripts/ai_anomaly_analysis.py${NC}"
      echo -e "\n${YELLOW}Press Enter to continue...${NC}"
      read
      return
    fi
    
    # Present a submenu for analysis options
    echo -e "${BLUE}AI Anomaly Analysis Options:${NC}"
    echo -e "${YELLOW}1)${NC} Quick Analysis (last 15 minutes)"
    echo -e "${YELLOW}2)${NC} Standard Analysis (last hour)"
    echo -e "${YELLOW}3)${NC} Detailed Analysis (last 6 hours)"
    echo -e "${YELLOW}4)${NC} Custom Timeframe Analysis"
    echo -e "${YELLOW}5)${NC} Real-time Analysis (current state)"
    echo -e "${YELLOW}6)${NC} Compare with Historical Data"
    echo -e "${YELLOW}7)${NC} List Available AI Models"
    echo -e "${YELLOW}8)${NC} Return to Menu"
    echo ""
    read -p "Enter your choice (1-8): " analysis_choice
    
    case $analysis_choice in
    1)
      # Quick Analysis (15 minutes)
      timeframe="15m"
      echo -e "${BLUE}Running quick analysis (last 15 minutes)...${NC}"
      ;;
    2)
      # Standard Analysis (1 hour)
      timeframe="1h"
      echo -e "${BLUE}Running standard analysis (last hour)...${NC}"
      ;;
    3)
      # Detailed Analysis (6 hours)
      timeframe="6h"
      echo -e "${BLUE}Running detailed analysis (last 6 hours)...${NC}"
      ;;
    4)
      # Custom Timeframe
      echo -e "${BLUE}Enter a custom timeframe:${NC}"
      echo -e "${YELLOW}Examples: 30m (30 minutes), 2h (2 hours), 1d (1 day)${NC}"
      read -p "Timeframe: " timeframe
      echo -e "${BLUE}Running analysis with custom timeframe: $timeframe...${NC}"
      ;;
    5)
      # Real-time Analysis
      timeframe="now"
      echo -e "${BLUE}Running real-time analysis (current state)...${NC}"
      ;;
    6)
      # Compare with Historical Data
      echo -e "${BLUE}Enter the current timeframe to analyze:${NC}"
      read -p "Current timeframe (e.g., 15m): " timeframe
      echo -e "${BLUE}Enter the historical timeframe to compare with:${NC}"
      read -p "Historical timeframe (e.g., 1d): " historical_timeframe
      echo -e "${BLUE}Running comparative analysis between now ($timeframe) and past ($historical_timeframe)...${NC}"
      COMPARE_FLAG="--compare-with=$historical_timeframe"
      ;;
    7)
      # List Available Models
      echo -e "${BLUE}Listing available AI models...${NC}"
      uv run scripts/ai_anomaly_analysis.py --list-models
      echo -e "\n${GREEN}Press Enter to continue...${NC}"
      read
      return
      ;;
    8)
      # Return to menu
      return
      ;;
    *)
      echo -e "${RED}Invalid choice. Using default timeframe (1h).${NC}"
      timeframe="1h"
      ;;
    esac
    
    # Get additional options
    read -p "Specify a particular AI model to use (or press Enter to use default): " model_choice
    if [ -n "$model_choice" ]; then
      MODEL_FLAG="--model=$model_choice"
    else
      MODEL_FLAG=""
    fi
    
    # Check if Prometheus is running - metrics are needed for analysis
    if docker compose ps | grep -q prometheus; then
      echo -e "${GREEN}Prometheus is running and collecting metrics.${NC}"
    else
      echo -e "${YELLOW}Warning: Prometheus does not appear to be running.${NC}"
      echo -e "${YELLOW}The analysis may not have access to recent metrics.${NC}"
      
      read -p "Would you like to start Prometheus now? (y/n): " start_prometheus
      if [[ "$start_prometheus" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Starting Prometheus...${NC}"
        docker compose up -d prometheus
        echo -e "${YELLOW}Waiting for Prometheus to initialize...${NC}"
        sleep 5
      fi
    fi
    
    read -p "Enable verbose output? (y/n, default: n): " verbose
    if [[ "$verbose" =~ ^[Yy]$ ]]; then
      VERBOSE_FLAG="--verbose"
    else
      VERBOSE_FLAG=""
    fi
    
    # Check if we need to do a comparison analysis
    if [ -n "$COMPARE_FLAG" ]; then
      echo -e "${BLUE}Starting comparative analysis between timeframes: $timeframe and $historical_timeframe${NC}"
      uv run scripts/ai_anomaly_analysis.py --timeframe="$timeframe" $VERBOSE_FLAG $MODEL_FLAG $COMPARE_FLAG
    else
      # Run the standard analysis
      echo -e "${BLUE}Starting AI anomaly analysis with timeframe: $timeframe${NC}"
      uv run scripts/ai_anomaly_analysis.py --timeframe="$timeframe" $VERBOSE_FLAG $MODEL_FLAG
    fi
    
    # Check if we generated a report file
    LATEST_REPORT=$(find "$PROJECT_ROOT" -name "ai_anomaly_analysis_*.md" -type f -printf "%T@ %p\n" | sort -n | tail -1 | cut -f2- -d" ")
    
    if [ -n "$LATEST_REPORT" ] && [ -f "$LATEST_REPORT" ]; then
      echo -e "\n${GREEN}Analysis report saved to: ${YELLOW}$LATEST_REPORT${NC}"
      
      # Ask if user wants to view the report
      read -p "View the analysis report now? (y/n, default: y): " view_report
      if [[ ! "$view_report" =~ ^[Nn]$ ]]; then
        # Try to find a pager
        if command -v less &> /dev/null; then
          less "$LATEST_REPORT"
        elif command -v more &> /dev/null; then
          more "$LATEST_REPORT"
        else
          # Fall back to cat if no pager is available
          cat "$LATEST_REPORT"
        fi
      fi
      
      # Note: Dashboard update functionality has been deprecated
      echo -e "\n${YELLOW}Note: The K8s dashboard update functionality has been removed.${NC}"
      echo -e "${YELLOW}The AI analysis report is still available at: ${GREEN}$LATEST_REPORT${NC}"
    fi
    
    echo -e "\n${GREEN}Analysis completed. Press Enter to continue...${NC}"
    read
    ;;
  8)
    display_main_menu
    return
    ;;
  *)
    echo -e "${RED}Invalid choice. Press Enter to try again.${NC}"
    read
    prometheus_menu
    ;;
  esac

  prometheus_menu
}

# MCP Server Management Menu
mcp_server_menu() {
  display_header
  echo -e "${BLUE}MCP Server Management:${NC}"
  echo -e "${YELLOW}1)${NC} Start MCP Server"
  echo -e "${YELLOW}2)${NC} Stop MCP Server"
  echo -e "${YELLOW}3)${NC} Check Server Status"
  echo -e "${YELLOW}4)${NC} Run MCP Client Test"
  echo -e "${YELLOW}5)${NC} Return to Main Menu"
  echo ""
  read -p "Enter your choice (1-5): " mcp_choice

  case $mcp_choice in
  1)
    start_mcp_server
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  2)
    echo -e "\n${BLUE}Stopping MCP Server...${NC}"

    if check_mcp_server; then
      # Find MCP server process
      MCP_PID=$(ps aux | grep "start_mcp_server.py" | grep -v grep | awk '{print $2}')

      if [ -n "$MCP_PID" ]; then
        echo "Stopping MCP server (PID: $MCP_PID)..."
        kill $MCP_PID
        echo -e "${GREEN}MCP server stopped${NC}"
      else
        echo -e "${YELLOW}Could not find MCP server process${NC}"
      fi
    else
      echo -e "${YELLOW}MCP server is not running${NC}"
    fi

    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  3)
    echo -e "\n${BLUE}MCP Server Status:${NC}"

    if check_mcp_server; then
      echo -e "${GREEN}MCP server is running${NC}"

      # Find MCP server process
      MCP_PID=$(ps aux | grep "start_mcp_server.py" | grep -v grep | awk '{print $2}')

      if [ -n "$MCP_PID" ]; then
        echo "PID: $MCP_PID"
      fi

      # Show available models
      echo -e "\n${PURPLE}Available Models:${NC}"
      curl -s "http://localhost:8000/v1/models" | python3 -m json.tool || echo "Could not retrieve model list"
    else
      echo -e "${RED}MCP server is not running${NC}"
    fi

    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  4)
    echo -e "\n${BLUE}Running MCP Client Test...${NC}"

    if check_mcp_server; then
      uv run scripts/test_mcp_client.py
    else
      echo -e "${RED}MCP server is not running. Starting server first...${NC}"
      start_mcp_server
      sleep 2
      uv run scripts/test_mcp_client.py
    fi

    echo -e "\n${GREEN}Test completed. Press Enter to continue...${NC}"
    read
    ;;
  5)
    display_main_menu
    return
    ;;
  *)
    echo -e "${RED}Invalid choice. Press Enter to try again.${NC}"
    read
    mcp_server_menu
    ;;
  esac

  mcp_server_menu
}

# Environment Setup Menu
environment_setup_menu() {
  display_header
  echo -e "${BLUE}Environment Setup:${NC}"
  echo -e "${YELLOW}1)${NC} Start Prometheus Stack"
  echo -e "${YELLOW}2)${NC} Stop Prometheus Stack"
  echo -e "${YELLOW}3)${NC} Start Grafana Stack"
  echo -e "${YELLOW}4)${NC} Stop Grafana Stack"
  echo -e "${YELLOW}5)${NC} Start Complete Monitoring Stack"
  echo -e "${YELLOW}6)${NC} Stop Complete Monitoring Stack"
  echo -e "${YELLOW}7)${NC} Change OpenAI Models"
  echo -e "${YELLOW}8)${NC} Return to Main Menu"
  echo ""
  read -p "Enter your choice (1-8): " env_choice

  case $env_choice in
  1)
    start_prometheus
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  2)
    echo -e "\n${BLUE}Stopping Prometheus Stack...${NC}"

    if check_prometheus; then
      echo "Stopping Docker containers..."
      docker compose down prometheus node-exporter cadvisor
      echo -e "${GREEN}Prometheus containers stopped${NC}"
    else
      echo -e "${YELLOW}Prometheus is not running${NC}"
    fi

    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  3)
    echo -e "\n${BLUE}Starting Grafana Stack...${NC}"
    
    if check_grafana && check_mcp_grafana; then
      echo -e "${YELLOW}Grafana stack is already running${NC}"
    else
      echo "Starting Grafana services with Docker Compose..."
      docker compose up -d grafana mcp-grafana
      
      echo "Waiting for services to start..."
      sleep 10
      
      if check_grafana && check_mcp_grafana; then
        echo -e "${GREEN}Grafana services started successfully${NC}"
      else
        echo -e "${RED}Failed to start some Grafana services${NC}"
      fi
    fi
    
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  4)
    echo -e "\n${BLUE}Stopping Grafana Stack...${NC}"

    echo "Stopping Grafana and MCP-Grafana containers..."
    docker compose stop grafana mcp-grafana
    
    echo -e "\n${GREEN}Grafana stack stopped. Press Enter to continue...${NC}"
    read
    ;;
  5)
    echo -e "\n${BLUE}Starting Complete Monitoring Stack...${NC}"
    
    echo "Starting all monitoring services with Docker Compose..."
    docker compose up -d prometheus node-exporter cadvisor grafana mcp-grafana
    
    echo "Waiting for services to start..."
    sleep 15
    
    echo -e "\n${BLUE}Service Status:${NC}"
    check_prometheus
    check_grafana
    check_mcp_grafana
    
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  6)
    echo -e "\n${BLUE}Stopping Complete Monitoring Stack...${NC}"

    echo "Stopping all monitoring containers..."
    docker compose down
    echo -e "${GREEN}All monitoring containers stopped${NC}"
    
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  7)
    echo -e "\n${BLUE}Change OpenAI Models:${NC}"
    echo -e "Current chat model: ${YELLOW}$OPENAI_CHAT_MODEL${NC}"
    echo -e "Current completion model: ${YELLOW}$OPENAI_COMPLETION_MODEL${NC}"
    echo ""

    read -p "Enter new chat model (or press Enter to keep current): " new_chat_model
    if [ -n "$new_chat_model" ]; then
      export OPENAI_CHAT_MODEL="$new_chat_model"
      echo -e "${GREEN}Chat model changed to: $OPENAI_CHAT_MODEL${NC}"
    fi

    read -p "Enter new completion model (or press Enter to keep current): " new_completion_model
    if [ -n "$new_completion_model" ]; then
      export OPENAI_COMPLETION_MODEL="$new_completion_model"
      echo -e "${GREEN}Completion model changed to: $OPENAI_COMPLETION_MODEL${NC}"
    fi

    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  8)
    display_main_menu
    return
    ;;
  *)
    echo -e "${RED}Invalid choice. Press Enter to try again.${NC}"
    read
    environment_setup_menu
    ;;
  esac

  environment_setup_menu
}

# Grafana Management Menu
grafana_menu() {
  display_header
  echo -e "${BLUE}Grafana Dashboards:${NC}"
  echo -e "${YELLOW}1)${NC} Start Grafana Stack"
  echo -e "${YELLOW}2)${NC} Stop Grafana Stack"
  echo -e "${YELLOW}3)${NC} Open Grafana in Browser"
  echo -e "${YELLOW}4)${NC} Show MCP-Grafana Status"
  echo -e "${YELLOW}5)${NC} Import Dashboards to Grafana"
  echo -e "${YELLOW}6)${NC} Return to Main Menu"
  echo ""
  read -p "Enter your choice (1-6): " grafana_choice

  case $grafana_choice in
  1)
    echo -e "\n${BLUE}Starting Grafana Stack...${NC}"
    
    # First check if it's already running
    if check_grafana && check_mcp_grafana; then
      echo -e "${YELLOW}Grafana stack is already running${NC}"
    else
      echo "Starting Grafana services with Docker Compose..."
      docker compose up -d grafana mcp-grafana
      
      echo "Waiting for services to start..."
      sleep 10
      
      if check_grafana; then
        echo -e "${GREEN}Grafana started successfully${NC}"
        echo -e "Access Grafana at: ${BLUE}http://localhost:3000${NC}"
        echo -e "Default credentials: admin/admin"
      else
        echo -e "${RED}Failed to start Grafana${NC}"
      fi
      
      if check_mcp_grafana; then
        echo -e "${GREEN}MCP-Grafana bridge started successfully${NC}"
        echo -e "MCP-Grafana bridge is available at: ${BLUE}http://localhost:8085${NC}"
      else
        echo -e "${RED}Failed to start MCP-Grafana bridge${NC}"
      fi
    fi
    
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  2)
    echo -e "\n${BLUE}Stopping Grafana Stack...${NC}"
    
    echo "Stopping Grafana and MCP-Grafana containers..."
    docker compose stop grafana mcp-grafana
    
    echo -e "\n${GREEN}Grafana stack stopped. Press Enter to continue...${NC}"
    read
    ;;
  3)
    echo -e "\n${BLUE}Opening Grafana in Browser...${NC}"
    
    if check_grafana; then
      echo "Opening Grafana UI..."
      if command_exists xdg-open; then
        xdg-open "http://localhost:3000" &
      elif command_exists open; then
        open "http://localhost:3000" &
      else
        echo -e "${YELLOW}Cannot automatically open browser.${NC}"
        echo -e "Please manually navigate to: ${BLUE}http://localhost:3000${NC}"
      fi
    else
      echo -e "${RED}Grafana is not running.${NC}"
      read -p "Would you like to start Grafana now? (y/n): " start_grafana
      if [ "$start_grafana" == "y" ]; then
        docker compose up -d grafana mcp-grafana
        echo "Waiting for Grafana to start..."
        sleep 10
        
        if check_grafana; then
          echo -e "${GREEN}Grafana started successfully${NC}"
          echo -e "Access Grafana at: ${BLUE}http://localhost:3000${NC}"
          echo -e "Default credentials: admin/admin"
        else
          echo -e "${RED}Failed to start Grafana${NC}"
        fi
      fi
    fi
    
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  4)
    echo -e "\n${BLUE}MCP-Grafana Status:${NC}"
    
    if check_mcp_grafana; then
      echo -e "${GREEN}MCP-Grafana bridge is running${NC}"
      echo -e "MCP-Grafana bridge is available at: ${BLUE}http://localhost:8085${NC}"
      
      # Check if we can get version info
      echo -e "\n${BLUE}MCP-Grafana Version Info:${NC}"
      curl -s "http://localhost:8085/version" | python3 -m json.tool || echo "Could not retrieve version information"
      
      echo -e "\n${BLUE}MCP-Grafana Health Check:${NC}"
      curl -s "http://localhost:8085/health" | python3 -m json.tool || echo "Could not retrieve health information"
      
      # List available dashboards
      echo -e "\n${BLUE}Available Dashboards:${NC}"
      curl -s "http://localhost:8085/grafana/dashboards" | python3 -m json.tool || echo "Could not retrieve dashboard list"
    else
      echo -e "${RED}MCP-Grafana bridge is not running${NC}"
    fi
    
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  5)
    echo -e "\n${BLUE}Importing Dashboards to Grafana...${NC}"
    
    if check_grafana; then
      echo "Ensuring dashboards are properly provisioned..."
      
      # Check if our dashboards directory exists
      if [ -d "./grafana/dashboards" ] && [ "$(ls -A ./grafana/dashboards)" ]; then
        echo -e "${GREEN}Dashboards found in ./grafana/dashboards${NC}"
        echo "Restarting Grafana to pick up dashboards..."
        docker compose restart grafana
        echo -e "${GREEN}Grafana restarted. Dashboards should be available.${NC}"
      else
        echo -e "${YELLOW}No dashboards found in ./grafana/dashboards${NC}"
        echo "Please make sure you have dashboard JSON files in the ./grafana/dashboards directory."
      fi
    else
      echo -e "${RED}Grafana is not running.${NC}"
      echo "Please start Grafana first."
    fi
    
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  6)
    display_main_menu
    ;;
  *)
    echo -e "${RED}Invalid choice. Press Enter to try again.${NC}"
    read
    grafana_menu
    ;;
  esac

  grafana_menu
}

# Runs the AI anomaly analysis
ai_analyze() {
  # Check if the AI analysis script exists
  if [ ! -f "$PROJECT_ROOT/scripts/ai_anomaly_analysis.py" ]; then
    echo -e "${RED}Error: AI anomaly analysis script not found at $PROJECT_ROOT/scripts/ai_anomaly_analysis.py${NC}"
    return 1
  fi

  # Process arguments
  local TIMEFRAME="1h"  # Default timeframe
  local VERBOSE_FLAG=""
  local MODEL_FLAG=""
  
  # Parse command line arguments
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --timeframe=*)
        TIMEFRAME="${1#*=}"
        shift
        ;;
      --timeframe)
        TIMEFRAME="$2"
        shift 2
        ;;
      --verbose)
        VERBOSE_FLAG="--verbose"
        shift
        ;;
      --model=*)
        MODEL_FLAG="--model=${1#*=}"
        shift
        ;;
      --model)
        MODEL_FLAG="--model=$2"
        shift 2
        ;;
      *)
        echo -e "${YELLOW}Ignoring unknown option: $1${NC}"
        shift
        ;;
    esac
  done
  
  echo -e "${BLUE}Running AI Anomaly Analysis with timeframe: $TIMEFRAME${NC}"
  
  # Check if Prometheus is running
  if docker compose ps | grep -q prometheus; then
    echo -e "${GREEN}Prometheus is running and collecting metrics.${NC}"
  else
    echo -e "${YELLOW}Warning: Prometheus does not appear to be running.${NC}"
    echo -e "${YELLOW}Starting Prometheus to ensure metrics are available...${NC}"
    docker compose up -d prometheus
    echo -e "${YELLOW}Waiting for Prometheus to initialize...${NC}"
    sleep 5
  fi
  
  # Run the analysis
  uv run scripts/ai_anomaly_analysis.py --timeframe="$TIMEFRAME" $VERBOSE_FLAG $MODEL_FLAG
  return $?
}

# Main script execution
if [[ "$1" == "ai_analyze" ]]; then
  # Remove the first argument and pass the rest to the ai_analyze function
  shift
  ai_analyze "$@"
  exit $?
fi

# Check for direct commands
if [ "$1" == "update-dashboard" ]; then
  update_dashboard
  exit 0
elif [ "$1" == "run-tests" ]; then
  run_tests
  exit 0
fi

# If no command provided, show the menu
display_main_menu
