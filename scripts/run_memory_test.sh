#!/bin/bash
# Script to run memory-based Prometheus tests

set -e

echo "========================================================"
echo "Prometheus Memory Test Suite"
echo "========================================================"

# Function to check if a command exists
command_exists() {
  command -v "$1" &>/dev/null
}

# Check if Prometheus is running
echo "Checking if Prometheus is already running..."
if docker ps | grep -q prometheus; then
  echo "Prometheus is already running"
else
  echo "Starting Prometheus services with Docker Compose..."
  docker compose up -d

  # Wait for services to start
  echo "Waiting for services to start..."
  sleep 10
fi

# Verify Prometheus is accessible
echo "Verifying Prometheus is accessible..."
if ! curl -s "http://localhost:9090/api/v1/query?query=up" >/dev/null; then
  echo "Error: Cannot connect to Prometheus. Please check if it's running."
  exit 1
fi

echo "Prometheus is running and accessible."

# Start MCP server in the background if not already running
echo "Checking if MCP server is running..."
if curl -s "http://localhost:8000/v1/models" >/dev/null; then
  echo "MCP server is already running"
else
  echo "Starting MCP server in the background..."
  uv run start_mcp_server.py --prometheus-url "http://localhost:9090" --debug &
  MCP_PID=$!

  # Wait for server to start
  echo "Waiting for MCP server to start..."
  sleep 5

  if ! curl -s "http://localhost:8000/v1/models" >/dev/null; then
    echo "Error: MCP server failed to start"
    exit 1
  fi

  echo "MCP server started with PID: $MCP_PID"
fi

# Run the memory test
echo ""
echo "========================================================"
echo "Running Prometheus Memory Test"
echo "========================================================"
echo "Note: Using quiet mode - AI recommendations are shown but detailed alert lists are hidden"
uv run test_prometheus.py --quiet

# Ask if user wants to simulate memory pressure
echo ""
echo "========================================================"
echo "Would you like to simulate memory pressure to trigger alerts? (y/n)"
read -p "> " simulate_pressure

if [[ "$simulate_pressure" == "y" || "$simulate_pressure" == "Y" ]]; then
  echo "Running memory pressure simulation..."

  # Ask for target percentage
  read -p "Enter target memory usage percentage (default: 85): " target_percent
  target_percent=${target_percent:-85}

  # Ask for duration
  read -p "Enter duration in seconds (default: 300): " duration
  duration=${duration:-300}

  # Run the simulation
  echo "Starting memory pressure simulation with target $target_percent% for $duration seconds..."
  uv run simulate_memory_pressure.py --target $target_percent --duration $duration

  # Wait a bit for Prometheus to detect the change
  echo "Waiting for Prometheus to process metrics..."
  sleep 15

  # Run the test again to see alerts
  echo "Running Prometheus test again to check for alerts..."
  echo "Note: Using quiet mode - AI recommendations are shown but detailed alert lists are hidden"
  uv run test_prometheus.py --quiet
fi

# Clean up
if [[ ! -z "$MCP_PID" ]]; then
  echo ""
  echo "========================================================"
  read -p "Stop the MCP server? (y/n): " stop_server
  if [[ "$stop_server" == "y" || "$stop_server" == "Y" ]]; then
    echo "Stopping MCP server (PID: $MCP_PID)..."
    kill $MCP_PID
  else
    echo "MCP server is still running with PID: $MCP_PID"
    echo "To stop it manually later, run: kill $MCP_PID"
  fi
fi

echo ""
echo "========================================================"
read -p "Stop Docker containers? (y/n): " stop_docker
if [[ "$stop_docker" == "y" || "$stop_docker" == "Y" ]]; then
  echo "Stopping Docker containers..."
  docker compose down
else
  echo "Docker containers are still running."
  echo "To stop them later, run: docker compose down"
fi

echo ""
echo "Prometheus memory test completed."
