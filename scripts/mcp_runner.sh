#!/bin/bash
# MCP Runner - Unified Test and Runner Script
# This script provides a user-friendly interface to run all MCP tests and tools

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
# Go to the project root directory (parent of scripts directory)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Set up logging
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
API_LOG_FILE="$LOG_DIR/mcp_api.log"

# Redirect MCP server API logs when running in menu mode
redirect_api_logs() {
  if [ -n "$MCP_API_LOG_FILE" ]; then
    # Create or truncate the log file
    > "$MCP_API_LOG_FILE"
    # Set up Python to redirect API logs
    export PYTHONUNBUFFERED=1
    export MCP_API_LOGGING=file
    export MCP_API_LOG_FILE="$MCP_API_LOG_FILE"
    export MCP_HIDE_API_LOGS=1  # Set this flag to hide API logs from console output
    
    # Note: curl redirections are handled by the mcp_curl function
    # which will both log and output the results
  else
    unset MCP_API_LOGGING
    unset MCP_API_LOG_FILE
    unset MCP_HIDE_API_LOGS  # Unset the flag to allow logs to appear in console
  fi
}

# Function to execute curl with proper log redirection
mcp_curl() {
  # This function runs curl and respects log redirection settings
  if [ -n "$MCP_API_LOG_FILE" ]; then
    # Log stderr to the log file but keep stdout for output
    # This preserves the ability to redirect or pipe the result
    curl "$@" 2>> "$MCP_API_LOG_FILE"
    return $?
  else
    # Normal operation - no redirection
    curl "$@"
    return $?
  fi
}

# Improve get_cached_status to use mcp_curl
get_cached_status() {
  local service="$1"
  local cache_file="$PROJECT_ROOT/.status/$service"
  
  if [ -f "$cache_file" ]; then
    # Use cache if it's recent (less than 10 seconds old)
    if [ $(($(date +%s) - $(stat -c %Y "$cache_file"))) -lt 10 ]; then
      cat "$cache_file"
      return
    fi
  fi
  
  # Cache miss or old cache - actually check the service
  mkdir -p "$PROJECT_ROOT/.status"
  
  # Perform the appropriate check based on service type
  if [ "$service" = "mcp" ]; then
    if check_mcp_api > /dev/null 2>&1; then
      echo "running" > "$cache_file"
      echo "running"
    else
      echo "stopped" > "$cache_file"
      echo "stopped"
    fi
  elif [ "$service" = "langflow" ]; then
    if check_langflow > /dev/null 2>&1; then
      echo "running" > "$cache_file"
      echo "running"
    else
      echo "stopped" > "$cache_file"
      echo "stopped"
    fi
  elif [ "$service" = "prometheus" ]; then
    if check_prometheus > /dev/null 2>&1; then
      echo "running" > "$cache_file"
      echo "running"
    else
      echo "stopped" > "$cache_file"
      echo "stopped"
    fi
  elif [ "$service" = "grafana" ]; then
    if mcp_curl -s --connect-timeout 1 --max-time 1 "http://localhost:3000/api/health" >/dev/null; then
      echo "running" > "$cache_file"
      echo "running"
    else
      echo "stopped" > "$cache_file"
      echo "stopped"
    fi
  else
    echo "unknown" > "$cache_file"
    echo "unknown"
  fi
}

# Determine if we're running in menu mode or direct command mode
if [ "$1" == "" ] || [ "$1" == "menu" ]; then
  # Running in menu mode - redirect API logs
  MCP_API_LOG_FILE="$API_LOG_FILE"
  redirect_api_logs
  echo "API logs redirected to $API_LOG_FILE"
else
  # Running in direct command mode - don't redirect logs
  unset MCP_API_LOG_FILE
fi

# Set environment variables for OpenAI models if needed
export OPENAI_CHAT_MODEL="${OPENAI_CHAT_MODEL:-gpt-4o-mini}"
export OPENAI_COMPLETION_MODEL="${OPENAI_COMPLETION_MODEL:-gpt-3.5-turbo-instruct}"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Create an array to track background processes
BACKGROUND_PIDS=()

# Function to pre-cache service status in background (completely revised version)
precache_service_status() {
  # Create status directory
  mkdir -p "$PROJECT_ROOT/.status"
  
  # Use the new mcp_curl function for all service checks
  (mcp_curl -s --connect-timeout 1 --max-time 1 "http://localhost:8000/v1/models" >/dev/null && 
   echo "running" > "$PROJECT_ROOT/.status/mcp" || 
   echo "stopped" > "$PROJECT_ROOT/.status/mcp") &
   
  (mcp_curl -s --connect-timeout 1 --max-time 1 "http://localhost:9090/api/v1/query?query=up" >/dev/null && 
   echo "running" > "$PROJECT_ROOT/.status/prometheus" || 
   echo "stopped" > "$PROJECT_ROOT/.status/prometheus") &
   
  (mcp_curl -s --connect-timeout 1 --max-time 1 "http://localhost:3000/api/health" >/dev/null && 
   echo "running" > "$PROJECT_ROOT/.status/grafana" || 
   echo "stopped" > "$PROJECT_ROOT/.status/grafana") &
   
  (mcp_curl -s --connect-timeout 1 --max-time 1 "http://localhost:7860/health" >/dev/null && 
   echo "running" > "$PROJECT_ROOT/.status/langflow" || 
   echo "stopped" > "$PROJECT_ROOT/.status/langflow") &
}

# Start pre-caching service status as soon as the script starts
precache_service_status

# Handle SIGINT (Ctrl+C) gracefully
cleanup() {
  echo -e "\n\nInterrupt received, cleaning up background processes..."
  
  # Track which processes we're cleaning up
  local cleaned_up=()
  
  # Check if we're running langflow test and terminate any test processes
  TEMP_SCRIPT_PIDS=$(ps aux | grep "test_mcp_component" | grep -v grep | awk '{print $2}')
  if [ -n "$TEMP_SCRIPT_PIDS" ]; then
    for pid in $TEMP_SCRIPT_PIDS; do
      echo "Stopping test script (PID: $pid)"
      kill $pid 2>/dev/null
      cleaned_up+=("test_script:$pid")
    done
  fi
  
  # Kill any background processes we started EXCEPT Langflow
  # This allows Langflow to keep running after the script exits
  for pid in "${BACKGROUND_PIDS[@]}"; do
    # Check if the process is still running
    if kill -0 $pid 2>/dev/null; then
      # Skip Langflow processes - we want them to keep running in the background
      if ! ps -p $pid -o command= | grep -q "langflow"; then
        echo "Stopping process with PID: $pid"
        kill $pid 2>/dev/null
        cleaned_up+=("process:$pid")
      else
        echo "Keeping Langflow running in the background (PID: $pid)"
        echo "To stop Langflow later, use 'mcp_run langflow stop' or option 2 in the Langflow menu"
      fi
    fi
  done
  
  # If we didn't clean up anything, let the user know
  if [ ${#cleaned_up[@]} -eq 0 ]; then
    echo "No active processes to clean up."
  else
    echo "Cleaned up ${#cleaned_up[@]} processes."
  fi
  
  echo "Exiting MCP Runner. Goodbye!"
  exit 1
}

# Set trap for Ctrl+C
trap cleanup SIGINT

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
check_mcp_api() {
  if mcp_curl -s --connect-timeout 1 --max-time 2 "http://localhost:8000/v1/models" >/dev/null; then
    echo -e "${GREEN}MCP server is running${NC}"
    return 0
  else
    echo -e "${RED}MCP server is not running${NC}"
    return 1
  fi
}

# Function to check if Prometheus is running
check_prometheus() {
  if mcp_curl -s --connect-timeout 1 --max-time 2 "http://localhost:9090/api/v1/query?query=up" >/dev/null; then
    echo -e "${GREEN}Prometheus is running${NC}"
    return 0
  else
    echo -e "${RED}Prometheus is not running${NC}"
    return 1
  fi
}

# Function to check if Grafana is running
check_grafana() {
  if mcp_curl -s --connect-timeout 1 --max-time 2 "http://localhost:3000/api/health" >/dev/null; then
    echo -e "${GREEN}Grafana is running${NC}"
    return 0
  else
    echo -e "${RED}Grafana is not running${NC}"
    return 1
  fi
}

# Function to check if MCP-Grafana is running
check_mcp_grafana() {
  if mcp_curl -s --connect-timeout 1 --max-time 2 "http://localhost:8085/health" >/dev/null; then
    echo -e "${GREEN}MCP-Grafana is running${NC}"
    return 0
  else
    echo -e "${RED}MCP-Grafana is not running${NC}"
    return 1
  fi
}

# Function to check if Langflow is running
check_langflow() {
  # Check if the Docker container is running
  if docker ps --filter "name=langflow" --format "{{.Names}}" | grep -q "langflow"; then
    # Container exists, now check if it's responding
    if mcp_curl -s --connect-timeout 1 --max-time 2 "http://localhost:7860/health" > /dev/null 2>&1; then
      echo -e "${GREEN}Langflow is running${NC}"
      return 0
    fi
    
    # Container exists but isn't responding, might be starting up
    echo -e "${YELLOW}Langflow container exists but not responding yet${NC}"
    return 0
  fi
  
  # Container check failed, now try direct HTTP check
  # Try up to 3 times with short delays to avoid temporary network issues
  for i in {1..3}; do
    if mcp_curl -s --connect-timeout 1 --max-time 2 "http://localhost:7860/health" > /dev/null 2>&1; then
      echo -e "${GREEN}Langflow is running${NC}"
      return 0
    fi
    sleep 0.5
  done
  
  echo -e "${RED}Langflow is not running${NC}"
  return 1
}

# Function to display Langflow status in detail
detailed_langflow_status() {
  echo -e "${BLUE}Checking Langflow status in detail...${NC}"
  
  # Check if Docker is running
  if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed or not in PATH${NC}"
    return 1
  fi
  
  if ! docker info &> /dev/null; then
    echo -e "${RED}Docker daemon is not running${NC}"
    return 1
  fi
  
  # Check if the Langflow container exists
  if docker ps -a --filter "name=langflow" --format "{{.Names}}" | grep -q "langflow"; then
    # Container exists, check if it's running
    if docker ps --filter "name=langflow" --format "{{.Names}}" | grep -q "langflow"; then
      echo -e "${GREEN}Langflow container is running${NC}"
      
      # Show container details
      docker_info=$(docker inspect langflow)
      container_id=$(echo "$docker_info" | grep -o '"Id": "[^"]*' | cut -d'"' -f4 | head -1)
      status=$(docker ps --filter "name=langflow" --format "{{.Status}}" | head -1)
      image=$(docker ps --filter "name=langflow" --format "{{.Image}}" | head -1)
      
      echo "Container ID: $container_id"
      echo "Status: $status"
      echo "Image: $image"
      echo "Port: 7860 (mapped to host)"
      
      # Check HTTP connectivity
      if mcp_curl -s --connect-timeout 1 --max-time 2 "http://localhost:7860/health" > /dev/null 2>&1; then
        echo -e "${GREEN}HTTP endpoint is responsive${NC}"
      else
        echo -e "${YELLOW}HTTP endpoint is not responding, but container is running${NC}"
      fi
    else
      echo -e "${YELLOW}Langflow container exists but is not running${NC}"
      status=$(docker ps -a --filter "name=langflow" --format "{{.Status}}" | head -1)
      echo "Status: $status"
      echo -e "${BLUE}You can start it with:${NC} mcp_run langflow start"
    fi
  else
    echo -e "${RED}Langflow container does not exist${NC}"
    echo -e "${BLUE}You can create and start it with:${NC} mcp_run langflow start"
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
  check_mcp_api

  # Check if Prometheus is running
  check_prometheus

  # Check if Grafana is running
  check_grafana

  # Check if MCP-Grafana is running
  check_mcp_grafana

  # Check if Langflow is running
  check_langflow

  echo ""
}

# Function to start MCP server
start_mcp_server() {
  echo -e "${BLUE}Starting MCP server...${NC}"
  if check_mcp_api; then
    echo "MCP server already running"
  else
    echo "Starting MCP server in the background..."
    uv run scripts/start_mcp_server.py --prometheus-url "http://localhost:9090" --debug &
    MCP_PID=$!

    # Track this PID for clean shutdown
    BACKGROUND_PIDS+=($MCP_PID)

    echo "Waiting for server to start..."
    sleep 5

    if check_mcp_api; then
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

# Function to generate langflow component
generate_langflow_component() {
  display_header
  echo -e "${BLUE}Generating Langflow Component from MCP Models${NC}"

  # Check if MCP server is running
  if ! check_mcp_api; then
    echo -e "${RED}MCP server is not running. Please start it first.${NC}"
    read -p "Would you like to start the MCP server now? (y/n): " start_server_choice
    if [ "$start_server_choice" == "y" ]; then
      start_mcp_server
      if ! check_mcp_api; then
        echo -e "${RED}Failed to start MCP server. Cannot generate component.${NC}"
        read -p "Press Enter to return to the menu..."
        return
      fi
    else
      echo -e "${RED}Cannot generate component without MCP server.${NC}"
      read -p "Press Enter to return to the menu..."
      return
    fi
  fi

  # Ask for output directory
  read -p "Enter the output directory (defaults to current directory): " output_dir
  output_dir=${output_dir:-$(pwd)}

  # Resolve to absolute path if relative
  if [[ "$output_dir" != /* ]]; then
    output_dir="$(pwd)/$output_dir"
  fi

  # Create output directory if it doesn't exist
  if [ ! -d "$output_dir" ]; then
    echo -e "Output directory doesn't exist. Creating it now..."
    mkdir -p "$output_dir" || {
      echo -e "${RED}Failed to create output directory $output_dir${NC}"
      read -p "Press Enter to return to the menu..."
      return 1
    }
  fi

  # Generate the component
  echo -e "\n${BLUE}Fetching models from MCP server...${NC}"
  
  # Check if the generator script exists
  GENERATOR_SCRIPT="$SCRIPT_DIR/generate_langflow_component.py"
  if [ ! -f "$GENERATOR_SCRIPT" ]; then
    echo -e "${RED}Error: Could not find the generator script at $GENERATOR_SCRIPT${NC}"
    read -p "Press Enter to return to the menu..."
    return 1
  fi
  
  # Run the generator script with uv
  uv run "$GENERATOR_SCRIPT" --output-dir "$output_dir"
  
  status=$?
  if [ $status -eq 0 ]; then
    echo -e "\n${GREEN}Langflow component generated successfully!${NC}"
    echo -e "Component files are available in: ${YELLOW}$output_dir${NC}"
    
    # Export the output_dir for other functions to use
    export output_dir
    
    # Check if component file was actually created
    if [ ! -f "$output_dir/mcp_component.py" ]; then
      echo -e "${RED}Warning: Component file not found at $output_dir/mcp_component.py${NC}"
      echo -e "Generator script completed but the component file was not created."
      unset output_dir
      read -p "Press Enter to return to the menu..."
      return 1
    fi
    
    # Add a helpful next step message
    echo -e "\n${BLUE}Next steps:${NC}"
    echo -e "1. Install the component in Langflow (Option 6)"
    echo -e "2. Test the component functionality (Option 7)"
  else
    echo -e "\n${RED}Failed to generate Langflow component (exit code: $status).${NC}"
    unset output_dir
    read -p "Press Enter to return to the menu..."
    return 1
  fi

  read -p "Press Enter to return to the menu..."
}

# Function to start Langflow
start_langflow() {
  echo -e "${BLUE}Starting Langflow server...${NC}"
  if check_langflow; then
    echo "Langflow is already running"
  else
    echo "Starting Langflow with Docker Compose..."
    
    # Check if Docker is installed and running
    if ! command_exists docker || ! docker info > /dev/null 2>&1; then
      echo -e "${RED}Error: Docker is not installed or not running.${NC}"
      echo -e "${YELLOW}Please install Docker and Docker Compose to use this feature.${NC}"
      return 1
    fi
    
    # Start Langflow container using docker compose
    echo -e "${YELLOW}Starting Langflow container...${NC}"
    cd "$PROJECT_ROOT" && docker compose up -d langflow
    
    # Track service start for logging
    mkdir -p "$PROJECT_ROOT/logs"
    echo "Started Langflow via Docker at $(date)" >> "$PROJECT_ROOT/logs/services.log"
    
    echo "Waiting for server to start..."
    
    # More robust waiting logic with progress indicator
    MAX_WAIT=30  # Maximum wait time in seconds
    for i in $(seq 1 $MAX_WAIT); do
      if mcp_curl -s --connect-timeout 1 --max-time 1 "http://localhost:7860/health" > /dev/null 2>&1; then
        echo -e "\n${GREEN}Langflow server started successfully!${NC}"
        echo -e "Access Langflow at: ${BLUE}http://localhost:7860${NC}"
        return 0
      fi
      
      # Show progress
      if [ $((i % 5)) -eq 0 ]; then
        echo -e "${YELLOW}Waiting for Langflow to start...${NC}"
      fi
      
      sleep 1
    done
    
    # If we got here, starting the server failed or it's taking too long
    echo -e "${RED}Failed to start Langflow server within ${MAX_WAIT} seconds.${NC}"
    echo -e "${YELLOW}Check Docker logs with: docker logs langflow${NC}"
    return 1
  fi
}

# Function to stop Langflow
stop_langflow() {
  echo -e "${BLUE}Stopping Langflow server...${NC}"

  if check_langflow; then
    # Stop Langflow container using docker compose
    echo "Stopping Langflow Docker container..."
    cd "$PROJECT_ROOT" && docker compose stop langflow
    
    # Wait a moment to ensure it's actually stopping
    sleep 2
    
    # Verify it has stopped
    if ! check_langflow; then
      echo -e "${GREEN}Langflow server stopped${NC}"
      # Track service stop for logging
      echo "Stopped Langflow via Docker at $(date)" >> "$PROJECT_ROOT/logs/services.log"
    else
      echo -e "${YELLOW}Langflow is still running, trying to force stop...${NC}"
      cd "$PROJECT_ROOT" && docker compose down langflow
      sleep 2
      echo -e "${GREEN}Langflow shutdown complete${NC}"
    fi
  else
    echo -e "${YELLOW}Langflow server is not running${NC}"
  fi
}

# Function to install MCP component in Langflow
install_mcp_component() {
  display_header
  echo -e "${BLUE}Installing MCP Component in Langflow Docker Container...${NC}"
  
  # First check if Langflow container is running
  if ! check_langflow; then
    echo -e "${RED}Error: Langflow container is not running.${NC}"
    echo -e "${YELLOW}Please start Langflow first with 'mcp_run langflow start'${NC}"
    read -p "Press Enter to return to the menu..."
    return 1
  fi
  
  # Locate the MCP component file
  component_dir="$PROJECT_ROOT"
  if [ ! -f "$component_dir/mcp_component.py" ]; then
    echo -e "${RED}Error: MCP component file not found at $component_dir/mcp_component.py${NC}"
    read -p "Press Enter to return to the menu..."
    return 1
  fi
  
  # Make sure custom_components directory exists
  mkdir -p "$PROJECT_ROOT/custom_components"
  
  # Copy the component file to the custom_components directory
  echo -e "${BLUE}Copying MCP component to custom_components directory...${NC}"
  cp "$component_dir/mcp_component.py" "$PROJECT_ROOT/custom_components/" || {
    echo -e "${RED}Error: Failed to copy component file to $PROJECT_ROOT/custom_components/${NC}"
    read -p "Press Enter to return to the menu..."
    return 1
  }
  
  # Create or update the __init__.py file to import the component
  INIT_FILE="$PROJECT_ROOT/custom_components/__init__.py"
  
  # Check if the import already exists
  if [ -f "$INIT_FILE" ] && grep -q "from .mcp_component import MCPComponent" "$INIT_FILE"; then
    echo -e "${GREEN}Component import already exists in $INIT_FILE${NC}"
  else
    # Add the import statement to the init file
    echo -e "${BLUE}Updating $INIT_FILE with component import...${NC}"
    
    # Create the file if it doesn't exist
    if [ ! -f "$INIT_FILE" ]; then
      echo "# Langflow custom components" > "$INIT_FILE" || {
        echo -e "${RED}Error: Failed to create $INIT_FILE${NC}"
        read -p "Press Enter to return to the menu..."
        return 1
      }
    fi
    
    # Add the import statement to the init file
    echo -e "\n# MCP Component import\nfrom .mcp_component import MCPComponent\n" >> "$INIT_FILE" || {
      echo -e "${RED}Error: Failed to update $INIT_FILE${NC}"
      read -p "Press Enter to return to the menu..."
      return 1
    }
    echo -e "${GREEN}Added component import to $INIT_FILE${NC}"
  fi
  
  echo -e "\n${GREEN}✅ MCP Component installed successfully!${NC}"
  
  # Always restart Langflow for the changes to take effect
  echo -e "${YELLOW}Langflow needs to be restarted for the changes to take effect.${NC}"
  
  # Check if Langflow is currently running
  langflow_running=false
  if check_langflow; then
    langflow_running=true
    echo -e "${BLUE}Langflow is currently running and will be restarted.${NC}"
  fi
  
  if [ "$langflow_running" = true ]; then
    echo -e "${BLUE}Stopping Langflow server...${NC}"
    stop_langflow
    # Wait for it to fully stop
    sleep 3
  fi
  
  echo -e "${BLUE}Starting Langflow server with the new component...${NC}"
  start_langflow
  
  # Wait for Langflow to start
  echo -e "${BLUE}Waiting for Langflow to start...${NC}"
  for i in {1..20}; do
    if check_langflow; then
      echo -e "${GREEN}✅ Langflow server started successfully!${NC}"
      echo -e "Access Langflow at: ${BLUE}http://localhost:7860${NC}"
      echo -e "The MCP component should now be available in the Components panel."
      break
    fi
    echo -n "."
    sleep 2
    if [ $i -eq 20 ]; then
      echo -e "\n${YELLOW}Langflow is taking longer than expected to start.${NC}"
      echo -e "You can check its status later with option 3 'Check Langflow Status'"
    fi
  done
  
  read -p "Press Enter to continue..."
}

# Function to test the component with all capabilities
test_mcp_component() {
  display_header
  echo -e "${BLUE}Testing MCP Component Functionality...${NC}"

  # First check if Langflow is running
  if ! check_langflow; then
    echo -e "${YELLOW}Langflow is not running. The component should be installed in Langflow first.${NC}"
    read -p "Would you like to start Langflow and install the component now? (y/n): " start_install
    if [ "$start_install" == "y" ]; then
      # Check if component already exists
      component_path=""
      read -p "Enter the path to the MCP component file: " component_path
      component_path=${component_path:-"./mcp_component.py"}

      if [ ! -f "$component_path" ]; then
        echo -e "${YELLOW}Component file not found at $component_path${NC}"
        read -p "Would you like to generate it first? (y/n): " generate_first
        if [ "$generate_first" == "y" ]; then
          generate_langflow_component
          # Get the component path from the output directory
          component_dir=${output_dir:-"."}
          component_path="$component_dir/mcp_component.py"
        else
          echo -e "${RED}Cannot test without a component file.${NC}"
          read -p "Press Enter to return to the menu..."
          return 1
        fi
      fi

      # Start Langflow
      start_langflow

      # Install the component
      COMPONENT_DIR=$(dirname "$component_path")
      install_mcp_component
    else
      echo -e "${RED}Cannot test component without Langflow running.${NC}"
      read -p "Press Enter to return to the menu..."
      return 1
    fi
  fi

  # Make sure MCP server is running
  if ! check_mcp_api; then
    echo -e "${RED}MCP server is not running. Please start it first.${NC}"
    read -p "Would you like to start the MCP server now? (y/n): " start_server_choice
    if [ "$start_server_choice" == "y" ]; then
      start_mcp_server
      if ! check_mcp_api; then
        echo -e "${RED}Failed to start MCP server. Cannot test component.${NC}"
        read -p "Press Enter to return to the menu..."
        return 1
      fi
    else
      echo -e "${RED}Cannot test component without MCP server.${NC}"
      read -p "Press Enter to return to the menu..."
      return 1
    fi
  fi

  # Get component path from environment or ask the user
  component_path="${COMPONENT_PATH:-}"
  if [ -z "$component_path" ]; then
    read -p "Enter the path to the MCP component file: " component_path
    component_path=${component_path:-"./mcp_component.py"}
  fi

  # Make sure the component exists
  if [ ! -f "$component_path" ]; then
    echo -e "${RED}Error: Component file not found at $component_path${NC}"
    echo -e "Please generate the component first using option 5 'Generate MCP Component for Langflow'"
    read -p "Press Enter to return to the menu..."
    return 1
  fi

  # Check if the component is installed in the custom_components directory
  CUSTOM_COMPONENTS_DIR="$PROJECT_ROOT/custom_components"
  CUSTOM_COMPONENT_FILE="$CUSTOM_COMPONENTS_DIR/mcp_component.py"

  if [ ! -f "$CUSTOM_COMPONENT_FILE" ]; then
    echo -e "${YELLOW}Component not found in custom_components directory.${NC}"
    read -p "Would you like to install it now? (y/n): " install_now
    if [ "$install_now" == "y" ]; then
      COMPONENT_DIR=$(dirname "$component_path")
      install_mcp_component
    else
      echo -e "${RED}Cannot test without installing the component.${NC}"
      read -p "Press Enter to return to the menu..."
      return 1
    fi
  fi

  # Create a temporary test script
  TEMP_SCRIPT=$(mktemp)

  # Create a test script that imports the component and tests all capabilities
  cat >"$TEMP_SCRIPT" <<EOF
#!/usr/bin/env python3
import sys
import json
import requests
from importlib.util import spec_from_file_location, module_from_spec

def import_module_from_path(module_name, file_path):
    spec = spec_from_file_location(module_name, file_path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_component(component_path):
    try:
        # Import the component from the given path
        mcp_module = import_module_from_path("mcp_component", component_path)
        
        # Create an instance of the component
        print("Initializing MCPComponent...")
        mcp = mcp_module.MCPComponent(mcp_server_url="http://localhost:8000")
        
        # List available models using the component
        print("\nAvailable models:")
        models = mcp.list_models()
        
        # Group models by capability for testing
        capabilities = {
            "chat": [],
            "completion": [],
            "git": [],
            "filesystem": [],
            "prometheus": []
        }
        
        for model in models:
            model_id = model.get('id', '')
            model_name = model.get('name', model_id)
            model_capabilities = model.get('capabilities', [])
            
            for capability in model_capabilities:
                if capability in capabilities:
                    capabilities[capability].append(model_id)
                    print(f"- {model_id}: {model_name} (has {capability} capability)")
        
        # Track overall test results
        test_results = []
        
        # Test 1: Chat capability
        if capabilities["chat"]:
            print("\n=== Testing Chat Capability ===")
            chat_model = capabilities["chat"][0]
            print(f"Using model: {chat_model}")
            
            try:
                chat_response = mcp.chat(
                    model_id=chat_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Tell me a short joke about programming."}
                    ],
                    max_tokens=100,
                    temperature=0.7
                )
                
                if chat_response and not chat_response.get('error'):
                    print("✅ Chat test successful")
                    # Extract the content from the response
                    if "choices" in chat_response and chat_response["choices"]:
                        content = chat_response["choices"][0].get("message", {}).get("content", "")
                        if content:
                            print(f"Response: {content}")
                    test_results.append(True)
                else:
                    print("❌ Chat test failed")
                    print(f"Error: {chat_response.get('error', 'Unknown error')}")
                    test_results.append(False)
            except Exception as e:
                print(f"❌ Chat test error: {e}")
                test_results.append(False)
        else:
            print("\n⚠️ No chat models available, skipping chat test")
            
        # Test 2: Completion capability
        if capabilities["completion"]:
            print("\n=== Testing Completion Capability ===")
            completion_model = capabilities["completion"][0]
            print(f"Using model: {completion_model}")
            
            try:
                completion_response = mcp.completion(
                    model_id=completion_model,
                    prompt="Write a one-sentence Python function that calculates the factorial:",
                    max_tokens=100,
                    temperature=0.7
                )
                
                if completion_response and not completion_response.get('error'):
                    print("✅ Completion test successful")
                    # Extract the content from the response
                    if "choices" in completion_response and completion_response["choices"]:
                        content = completion_response["choices"][0].get("text", "")
                        if content:
                            print(f"Response: {content}")
                    test_results.append(True)
                else:
                    print("❌ Completion test failed")
                    print(f"Error: {completion_response.get('error', 'Unknown error')}")
                    test_results.append(False)
            except Exception as e:
                print(f"❌ Completion test error: {e}")
                test_results.append(False)
        else:
            print("\n⚠️ No completion models available, skipping completion test")
        
        # Test 3: Git capability
        if capabilities["git"]:
            print("\n=== Testing Git Capability ===")
            git_model = capabilities["git"][0]
            print(f"Using model: {git_model}")
            
            try:
                git_response = mcp.git(
                    model_id=git_model,
                    repo_url="https://github.com/openai/openai-python"  # Example repo
                )
                
                if git_response and not git_response.get('error'):
                    print("✅ Git test successful")
                    print(f"Response type: {type(git_response)}")
                    test_results.append(True)
                else:
                    print("❌ Git test failed")
                    print(f"Error: {git_response.get('error', 'Unknown error')}")
                    test_results.append(False)
            except Exception as e:
                print(f"❌ Git test error: {e}")
                test_results.append(False)
        else:
            print("\n⚠️ No git models available, skipping git test")
            
        # Test 4: Filesystem capability
        if capabilities["filesystem"]:
            print("\n=== Testing Filesystem Capability ===")
            fs_model = capabilities["filesystem"][0]
            print(f"Using model: {fs_model}")
            
            try:
                fs_response = mcp.filesystem(
                    model_id=fs_model,
                    path=".",  # Current directory
                    operation="list"
                )
                
                if fs_response and not fs_response.get('error'):
                    print("✅ Filesystem test successful")
                    print(f"Found {len(fs_response.get('files', []))} files/directories")
                    test_results.append(True)
                else:
                    print("❌ Filesystem test failed")
                    print(f"Error: {fs_response.get('error', 'Unknown error')}")
                    test_results.append(False)
            except Exception as e:
                print(f"❌ Filesystem test error: {e}")
                test_results.append(False)
        else:
            print("\n⚠️ No filesystem models available, skipping filesystem test")
            
        # Test 5: Prometheus capability
        if capabilities["prometheus"]:
            print("\n=== Testing Prometheus Capability ===")
            prom_model = capabilities["prometheus"][0]
            print(f"Using model: {prom_model}")
            
            try:
                prom_response = mcp.prometheus(
                    model_id=prom_model,
                    query="up"  # Simple uptime check
                )
                
                if prom_response and not prom_response.get('error'):
                    print("✅ Prometheus test successful")
                    test_results.append(True)
                else:
                    print("❌ Prometheus test failed")
                    print(f"Error: {prom_response.get('error', 'Unknown error')}")
                    test_results.append(False)
            except Exception as e:
                print(f"❌ Prometheus test error: {e}")
                test_results.append(False)
        else:
            print("\n⚠️ No prometheus models available, skipping prometheus test")
            
        # Test 6: Process method
        print("\n=== Testing Process Method ===")
        try:
            # Test process method with chat
            if capabilities["chat"]:
                process_response = mcp.process(
                    operation="chat",
                    model_id=capabilities["chat"][0],
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "What is 2+2?"}
                    ]
                )
                
                if process_response and not process_response.get('error'):
                    print("✅ Process method test successful")
                    test_results.append(True)
                else:
                    print("❌ Process method test failed")
                    test_results.append(False)
            else:
                # Try another capability if chat is not available
                for cap, models in capabilities.items():
                    if models:
                        print(f"Testing process with {cap} capability")
                        if cap == "completion":
                            process_response = mcp.process(
                                operation=cap,
                                model_id=models[0],
                                prompt="Hello"
                            )
                        else:
                            process_response = mcp.process(
                                operation=cap,
                                model_id=models[0]
                            )
                        
                        if process_response and not process_response.get('error'):
                            print(f"✅ Process method test with {cap} successful")
                            test_results.append(True)
                        else:
                            print(f"❌ Process method test with {cap} failed")
                            test_results.append(False)
                        break
        except Exception as e:
            print(f"❌ Process method test error: {e}")
            test_results.append(False)
            
        # Summarize test results
        print("\n=== Test Summary ===")
        success_count = sum(1 for result in test_results if result)
        total_tests = len(test_results)
        
        if success_count == total_tests and total_tests > 0:
            print(f"✅ All tests passed! ({success_count}/{total_tests})")
            return True
        elif success_count > 0:
            print(f"⚠️ Some tests passed ({success_count}/{total_tests})")
            return total_tests > 0  # Return True if at least one test was run
        else:
            print(f"❌ All tests failed! ({success_count}/{total_tests})")
            return False
    
    except Exception as e:
        print(f"❌ Error testing component: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_script.py <component_path>")
        sys.exit(1)
    
    component_path = sys.argv[1]
    result = test_component(component_path)
    sys.exit(0 if result else 1)
EOF

  # Make the script executable
  chmod +x "$TEMP_SCRIPT"

  # Run the test script
  echo -e "\n${BLUE}Running component test...${NC}"
  echo -e "${YELLOW}Testing component at: ${NC}$component_path"
  echo -e "${YELLOW}This will test if the component can connect to the MCP server and use all capabilities${NC}"
  echo -e "${BLUE}==================================================================${NC}"

  uv run python "$TEMP_SCRIPT" "$component_path"
  TEST_RESULT=$?

  # Clean up
  rm "$TEMP_SCRIPT"

  if [ $TEST_RESULT -eq 0 ]; then
    echo -e "\n${GREEN}✅ Component test completed successfully!${NC}"
    echo -e "The component can now be used in Langflow UI at: ${BLUE}http://localhost:7860${NC}"
  else
    echo -e "\n${RED}❌ Component test had issues.${NC}"
    echo -e "Please check the output above for details on what went wrong."
    echo -e "You may need to update the component code or check the MCP server."
  fi

  echo -e "\n${GREEN}Press Enter to continue...${NC}"
  read
}

# Function to display app status in main menu
check_all_services() {
  local services_running=0
  local services_total=0
  
  echo -e "${BLUE}Services status:${NC}"
  
  # Check MCP Server
  services_total=$((services_total+1))
  local mcp_status=$(get_cached_status "mcp")
  if [ "$mcp_status" = "running" ] || check_mcp_api > /dev/null; then
    echo -e "  ${GREEN}✓ MCP Server${NC} is running"
    services_running=$((services_running+1))
  else
    echo -e "  ${RED}✗ MCP Server${NC} is not running"
  fi
  
  # Check Langflow
  services_total=$((services_total+1))
  local langflow_status=$(get_cached_status "langflow")
  if [ "$langflow_status" = "running" ] || check_langflow > /dev/null; then
    echo -e "  ${GREEN}✓ Langflow${NC} is running (http://localhost:7860)"
    services_running=$((services_running+1))
    
    # Show how to stop Langflow if it's running
    echo -e "    To stop Langflow: ${YELLOW}./mcp_run langflow stop${NC}"
  else
    echo -e "  ${RED}✗ Langflow${NC} is not running"
  fi
  
  # Check Prometheus
  services_total=$((services_total+1))
  local prometheus_status=$(get_cached_status "prometheus")
  if [ "$prometheus_status" = "running" ] || check_prometheus > /dev/null; then
    echo -e "  ${GREEN}✓ Prometheus${NC} is running"
    services_running=$((services_running+1))
  else
    echo -e "  ${RED}✗ Prometheus${NC} is not running"
  fi
  
  # Check Grafana
  services_total=$((services_total+1))
  local grafana_status=$(get_cached_status "grafana")
  if [ "$grafana_status" = "running" ] || check_grafana > /dev/null; then
    echo -e "  ${GREEN}✓ Grafana${NC} is running"
    services_running=$((services_running+1))
  else
    echo -e "  ${RED}✗ Grafana${NC} is not running"
  fi
  
  # Summary
  echo -e "\n  ${services_running}/${services_total} services running"
  echo ""
  
  # Update cache for next time
  precache_service_status
}

# Function to display main menu
display_main_menu() {
  display_header
  check_all_services

  echo -e "${BLUE}Select a category:${NC}"
  echo -e "${YELLOW}1)${NC} Filesystem Tests"
  echo -e "${YELLOW}2)${NC} Git Integration Tests"
  echo -e "${YELLOW}3)${NC} Memory Analysis Tools"
  echo -e "${YELLOW}4)${NC} Prometheus Tests & Memory Stress"
  echo -e "${YELLOW}5)${NC} MCP Server Management"
  echo -e "${YELLOW}6)${NC} Environment Setup"
  echo -e "${YELLOW}7)${NC} Grafana Dashboards"
  echo ""
  echo -e "${BLUE}Langflow Integration:${NC}"
  echo -e "${YELLOW}8)${NC} Langflow Management & MCP Component Integration"
  echo ""
  echo -e "${YELLOW}0)${NC} Exit"
  echo ""
  read -p "Enter your choice (0-8): " main_choice

  case $main_choice in
  1) filesystem_menu ;;
  2) git_menu ;;
  3) memory_analysis_menu ;;
  4) prometheus_menu ;;
  5) mcp_server_menu ;;
  6) environment_setup_menu ;;
  7) grafana_menu ;;
  8) langflow_menu ;;
  0) 
    echo -e "\n${BLUE}Exiting MCP Runner...${NC}"
    # Check if Langflow is running
    if check_langflow > /dev/null; then
      echo -e "${YELLOW}Note: Langflow is still running in the background.${NC}"
      echo -e "To stop it later, use: ${GREEN}./mcp_run langflow stop${NC}"
    fi
    exit 0 
    ;;
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
    if mcp_curl -s "http://localhost:9090/api/v1/query?query=up" >/dev/null; then
      echo -e "${GREEN}Accessible${NC}"
    else
      echo -e "${RED}Not accessible${NC}"
    fi

    echo -e "\n${PURPLE}Current alerts:${NC}"
    alerts=$(mcp_curl -s "http://localhost:9090/api/v1/alerts" | grep -o '"name":"[^"]*"' | sed 's/"name":"//g' | sed 's/"//g')

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

    # Update Prometheus configuration to access the metrics from the Docker container
    echo -e "${BLUE}Updating Prometheus configuration to access the metrics...${NC}"
    uv run scripts/update_prometheus_config.py --port $http_port

    # Ask user if they want to restart Prometheus
    read -p "Do you want to restart Prometheus to apply the configuration? (y/n, default: y): " restart_prometheus
    restart_prometheus=${restart_prometheus:-y}

    if [[ "$restart_prometheus" =~ ^[Yy]$ ]]; then
      echo -e "${BLUE}Restarting Prometheus...${NC}"
      docker compose restart prometheus
      echo -e "${GREEN}Prometheus restarted${NC}"
      sleep 2 # Give Prometheus a moment to initialize
    else
      echo -e "${YELLOW}Remember that you'll need to restart Prometheus for changes to take effect:${NC}"
      echo -e "${YELLOW}  docker compose restart prometheus${NC}"
    fi

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

      uv run scripts/k8s_dummy_data_generator.py --pods $pod_count --http-port $http_port --interval $interval $ANOMALY_FLAG >"$LOGFILE" 2>&1 &
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
        if command -v less &>/dev/null; then
          less "$LATEST_REPORT"
        elif command -v more &>/dev/null; then
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

    if check_mcp_api; then
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

    if check_mcp_api; then
      echo -e "${GREEN}MCP server is running${NC}"

      # Find MCP server process
      MCP_PID=$(ps aux | grep "start_mcp_server.py" | grep -v grep | awk '{print $2}')

      if [ -n "$MCP_PID" ]; then
        echo "PID: $MCP_PID"
      fi

      # Show available models
      echo -e "\n${PURPLE}Available Models:${NC}"
      mcp_curl -s "http://localhost:8000/v1/models" | python3 -m json.tool || echo "Could not retrieve model list"
    else
      echo -e "${RED}MCP server is not running${NC}"
    fi

    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  4)
    echo -e "\n${BLUE}Running MCP Client Test...${NC}"

    if check_mcp_api; then
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
      mcp_curl -s "http://localhost:8085/version" | python3 -m json.tool || echo "Could not retrieve version information"

      echo -e "\n${BLUE}MCP-Grafana Health Check:${NC}"
      mcp_curl -s "http://localhost:8085/health" | python3 -m json.tool || echo "Could not retrieve health information"

      # List available dashboards
      echo -e "\n${BLUE}Available Dashboards:${NC}"
      mcp_curl -s "http://localhost:8085/grafana/dashboards" | python3 -m json.tool || echo "Could not retrieve dashboard list"
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

# Langflow Menu
langflow_menu() {
  display_header
  echo -e "${BLUE}Langflow Management:${NC}"
  echo -e "${YELLOW}1)${NC} Start Langflow Server"
  echo -e "${YELLOW}2)${NC} Stop Langflow Server"
  echo -e "${YELLOW}3)${NC} Check Langflow Status"
  echo -e "${YELLOW}4)${NC} Open Langflow in Browser"
  echo -e "${BLUE}---------- MCP Component Integration Workflow ----------${NC}"
  echo -e "${YELLOW}5)${NC} Generate MCP Component for Langflow       ${GREEN}[Step 1]${NC}"
  echo -e "${YELLOW}6)${NC} Install MCP Component in Langflow         ${GREEN}[Step 2]${NC}"
  echo -e "${YELLOW}7)${NC} Test MCP Component Chat Functionality     ${GREEN}[Step 3]${NC}"
  echo -e "${BLUE}----------------------------------------------------${NC}"
  echo -e "${YELLOW}8)${NC} Return to Main Menu"
  echo ""
  
  # Check and display component status
  component_status="Unknown"
  component_path=""
  
  # Try to find component in current directory
  if [ -f "./mcp_component.py" ]; then
    component_path="./mcp_component.py"
    component_status="Generated (not yet installed)"
  fi
  
  # Check if it's installed in Langflow - use timeout for faster checking
  local found_langflow=0
  timeout 2 python3 -c "
import sys
try:
    import langflow
    print('found')
    sys.exit(0)
except ImportError:
    print('notfound')
    sys.exit(1)
except Exception:
    print('error')
    sys.exit(2)
" 2>/dev/null | grep -q "found" && found_langflow=1
  
  if [ $found_langflow -eq 1 ]; then
    LANGFLOW_DIR=$(python3 -c "import langflow 2>/dev/null; import os; print(os.path.dirname(langflow.__file__)) if 'langflow' in locals() else ''" 2>/dev/null)
    if [ -n "$LANGFLOW_DIR" ]; then
      COMPONENTS_DIR="$LANGFLOW_DIR/components/custom"
      if [ -f "$COMPONENTS_DIR/mcp_component.py" ]; then
        component_status="Installed in Langflow"
        if [ -z "$component_path" ]; then
          component_path="$COMPONENTS_DIR/mcp_component.py"
        fi
      fi
    fi
  fi
  
  # Display status information
  echo -e "${BLUE}Component Status:${NC} $component_status"
  if [ -n "$component_path" ]; then
    echo -e "${BLUE}Component Path:${NC} $component_path"
  fi
  
  # Display Langflow status - use cached status for faster display
  local langflow_status=$(get_cached_status "langflow")
  if [ "$langflow_status" = "running" ] || check_langflow > /dev/null; then
    echo -e "${BLUE}Langflow Status:${NC} ${GREEN}Running${NC} (http://localhost:7860)"
  else
    echo -e "${BLUE}Langflow Status:${NC} ${RED}Not Running${NC}"
  fi
  
  # Update cache in background
  precache_service_status &
  
  echo ""
  read -p "Enter your choice (1-8): " lf_choice

  case $lf_choice in
  1)
    start_langflow
    # Update service status cache after starting
    precache_service_status
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  2)
    stop_langflow
    # Update service status cache after stopping
    precache_service_status
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  3)
    echo -e "\n${BLUE}Langflow Status:${NC}"
    detailed_langflow_status
    
    if check_langflow; then
      echo -e "Langflow UI is available at: ${BLUE}http://localhost:7860${NC}"
      
      # Show Docker logs option
      echo -e "\nYou can view Langflow logs with: ${YELLOW}docker logs langflow${NC}"
    fi
    
    echo -e "\nLangflow controls:"
    echo -e "  ${YELLOW}mcp_run langflow start${NC} - Start Langflow"
    echo -e "  ${YELLOW}mcp_run langflow stop${NC}  - Stop Langflow"
    echo -e "  ${YELLOW}mcp_run langflow status${NC} - Check status"
    
    # Update service status cache
    precache_service_status
    
    read -p "Press Enter to continue..."
    ;;
  4)
    echo -e "\n${BLUE}Opening Langflow in Browser...${NC}"
    
    # Use cached status first for faster check
    local langflow_status=$(get_cached_status "langflow")
    if [ "$langflow_status" = "running" ] || check_langflow; then
      echo "Opening Langflow UI..."
      if command_exists xdg-open; then
        xdg-open "http://localhost:7860" &
      elif command_exists open; then
        open "http://localhost:7860" &
      else
        echo -e "${YELLOW}Cannot automatically open browser.${NC}"
        echo -e "Please manually navigate to: ${BLUE}http://localhost:7860${NC}"
      fi
    else
      echo -e "${RED}Langflow is not running.${NC}"
      read -p "Would you like to start Langflow now? (y/n): " start_lf
      if [ "$start_lf" == "y" ]; then
        start_langflow
        # Update cache after starting
        precache_service_status
        
        # Use cached status first for faster check
        local langflow_status=$(get_cached_status "langflow")
        if [ "$langflow_status" = "running" ] || check_langflow; then
          echo "Opening Langflow UI..."
          if command_exists xdg-open; then
            xdg-open "http://localhost:7860" &
          elif command_exists open; then
            open "http://localhost:7860" &
          else
            echo -e "${YELLOW}Cannot automatically open browser.${NC}"
            echo -e "Please manually navigate to: ${BLUE}http://localhost:7860${NC}"
          fi
        fi
      fi
    fi
    
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
    ;;
  5)
    # Generate component
    echo -e "\n${BLUE}[Step 1] Generate MCP Component for Langflow${NC}"
    
    # Check if MCP server is running - use cached status first
    local mcp_status=$(get_cached_status "mcp")
    if [ "$mcp_status" != "running" ] && ! check_mcp_api; then
      echo -e "${RED}MCP server is not running.${NC}"
      echo -e "The MCP server must be running to fetch model information for the component."
      read -p "Would you like to start the MCP server now? (y/n): " start_mcp
      if [ "$start_mcp" == "y" ]; then
        start_mcp_server
        # Update cache after starting
        precache_service_status
        
        if ! check_mcp_api; then
          echo -e "${RED}Failed to start MCP server. Cannot generate component.${NC}"
          read -p "Press Enter to continue..."
          return
        fi
      else
        echo -e "${RED}Cannot generate component without MCP server.${NC}"
        read -p "Press Enter to continue..."
        return
      fi
    fi
    
    generate_langflow_component
    
    # Prompt for next step
    if [ -f "./mcp_component.py" ]; then
      echo -e "\n${GREEN}Component generation successful!${NC}"
      echo -e "${YELLOW}Next Step:${NC} Install the component in Langflow (Option 6)"
      read -p "Would you like to install the component now? (y/n): " install_now
      if [ "$install_now" == "y" ]; then
        install_mcp_component
        # Update cache after installation
        precache_service_status
      fi
    fi
    ;;
  6)
    # Install component
    echo -e "\n${BLUE}[Step 2] Install MCP Component in Langflow${NC}"
    
    # First check if the component exists
    if [ ! -f "./mcp_component.py" ]; then
      echo -e "${YELLOW}Component file not found in current directory.${NC}"
      read -p "Would you like to generate it first? (y/n): " generate_first
      if [ "$generate_first" == "y" ]; then
        generate_langflow_component
      else
        read -p "Enter the path to the existing component file: " existing_component
        if [ -z "$existing_component" ] || [ ! -f "$existing_component" ]; then
          echo -e "${RED}Invalid component path. Cannot proceed with installation.${NC}"
          read -p "Press Enter to continue..."
          return
        fi
        # Set the component directory for installation
        COMPONENT_DIR=$(dirname "$existing_component")
      fi
    fi
    
    install_mcp_component
    # Update cache after installation and starting Langflow
    precache_service_status
    
    # Prompt for next step
    echo -e "\n${YELLOW}Next Step:${NC} Test the component functionality (Option 7)"
    read -p "Would you like to test the component now? (y/n): " test_now
    if [ "$test_now" == "y" ]; then
      test_mcp_component
    fi
    ;;
  7)
    # Test component
    echo -e "\n${BLUE}[Step 3] Test MCP Component Chat Functionality${NC}"
    test_mcp_component
    # Update cache after testing
    precache_service_status
    ;;
  8)
    display_main_menu
    return
    ;;
  *)
    echo -e "${RED}Invalid choice. Press Enter to try again.${NC}"
    read
    langflow_menu
    ;;
  esac

  langflow_menu
}

# Restore the ai_analyze function that was inadvertently removed during the previous edit
# Runs the AI anomaly analysis
ai_analyze() {
  # Check if the AI analysis script exists
  if [ ! -f "$PROJECT_ROOT/scripts/ai_anomaly_analysis.py" ]; then
    echo -e "${RED}Error: AI anomaly analysis script not found at $PROJECT_ROOT/scripts/ai_anomaly_analysis.py${NC}"
    return 1
  fi

  # Process arguments
  local TIMEFRAME="1h" # Default timeframe
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

# Direct commands for Langflow
if [[ "$1" == "start_langflow" ]]; then
  start_langflow
  exit $?
elif [[ "$1" == "stop_langflow" ]]; then
  stop_langflow
  exit $?
elif [[ "$1" == "check_langflow" ]]; then
  # Check status and show detailed information
  detailed_langflow_status
  
  if check_langflow; then
    echo -e "Langflow UI is available at: ${BLUE}http://localhost:7860${NC}"
  fi

  exit $?
elif [[ "$1" == "install_mcp_component" ]]; then
  # Process optional arguments
  shift
  component_dir="."

  while [[ $# -gt 0 ]]; do
    case $1 in
    --component-dir=*)
      component_dir="${1#*=}"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      shift
      ;;
    esac
  done

  # Run the installation with the specified component directory
  COMPONENT_DIR="$component_dir" install_mcp_component
  exit $?
elif [[ "$1" == "test_mcp_component" ]]; then
  # Process optional arguments
  shift
  component_path="./mcp_component.py"

  while [[ $# -gt 0 ]]; do
    case $1 in
    --component-path=*)
      component_path="${1#*=}"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      shift
      ;;
    esac
  done

  # Run the test with the specified component path
  COMPONENT_PATH="$component_path" test_mcp_component
  exit $?
elif [[ "$1" == "generate_langflow_component" ]]; then
  # Initialize directory from arguments or use current directory
  output_dir="."
  server_url="http://localhost:8000"
  use_ai="true"

  # Process arguments
  shift
  while [[ $# -gt 0 ]]; do
    case $1 in
    --output-dir=*)
      output_dir="${1#*=}"
      shift
      ;;
    --server-url=*)
      server_url="${1#*=}"
      shift
      ;;
    --no-ai)
      use_ai="false"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      shift
      ;;
    esac
  done

  # Set up AI flag
  ai_flag=""
  if [ "$use_ai" == "false" ]; then
    ai_flag="--no-ai"
  fi

  # Run the component generator directly
  python "$SCRIPT_DIR/generate_langflow_component.py" --output-dir "$output_dir" --server-url "$server_url" $ai_flag
  exit $?
fi

# If no command provided, show the menu
display_main_menu
