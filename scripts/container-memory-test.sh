#!/bin/bash
# Container Memory Stress Test Control Script

echo "========================================================"
echo "Container Memory Stress Test Controller"
echo "========================================================"

ACTION=${1:-"start"}

# Check if docker and docker compose are installed

# Function to check if containers are running
check_containers() {
  if ! docker ps | grep -q prometheus; then
    echo "Prometheus container is not running."
    return 1
  fi

  if ! docker ps | grep -q cadvisor; then
    echo "cAdvisor container is not running."
    return 1
  fi

  if ! docker ps | grep -q node-exporter; then
    echo "Node Exporter container is not running."
    return 1
  fi

  return 0
}

# Function to build and start the memory stress container
start_memory_stress() {
  echo "Building and starting memory stress container..."

  # Check if memory-stress container already exists and remove it if it does
  if docker ps -a | grep -q memory-stress; then
    echo "Removing existing memory-stress container..."
    docker rm -f memory-stress
  fi

  # Build and start the memory-stress container
  docker compose up -d --build memory-stress

  echo "Memory stress container started."
  echo "View Prometheus alerts at: http://localhost:9090/alerts"
  echo "View container metrics at: http://localhost:9090/graph?g0.expr=(container_memory_usage_bytes%7Bcontainer_name%3D%22memory-stress%22%7D%20%2F%20container_spec_memory_limit_bytes%7Bcontainer_name%3D%22memory-stress%22%7D)*100&g0.tab=0"
  echo "View memory stress container logs with: docker logs -f memory-stress"
}

# Function to stop the memory stress container
stop_memory_stress() {
  echo "Stopping memory stress container..."

  if docker ps | grep -q memory-stress; then
    docker compose stop memory-stress
    docker compose rm -f memory-stress
    echo "Memory stress container stopped and removed."
  else
    echo "Memory stress container is not running."
  fi
}

# Function to show system status
show_status() {
  echo "========================================================"
  echo "System Status"
  echo "========================================================"

  # Check container status
  echo "Container Status:"
  docker ps | grep -E 'prometheus|cadvisor|node-exporter|memory-stress' || echo "No monitoring containers found"

  # Check if Prometheus is accessible
  echo -n "Prometheus API: "
  if curl -s "http://localhost:9090/api/v1/query?query=up" >/dev/null; then
    echo "Accessible"
  else
    echo "Not accessible"
  fi

  # Check alerts
  echo -n "Current alerts: "
  alerts=$(curl -s "http://localhost:9090/api/v1/alerts" | grep -o '"name":"[^"]*"' | sed 's/"name":"//g' | sed 's/"//g')

  if [ -n "$alerts" ]; then
    echo "Found"
    echo "$alerts"
  else
    echo "None"
  fi

  echo "========================================================"
}

# Main execution
case $ACTION in
"start")
  if check_containers; then
    start_memory_stress
  else
    echo "Starting all monitoring containers..."
    docker compose up -d prometheus cadvisor node-exporter
    sleep 5
    start_memory_stress
  fi
  show_status
  ;;

"stop")
  stop_memory_stress
  show_status
  ;;

"restart")
  stop_memory_stress
  sleep 2
  start_memory_stress
  show_status
  ;;

"status")
  show_status
  ;;

*)
  echo "Usage: $0 [start|stop|restart|status]"
  echo "  start   - Start memory stress testing"
  echo "  stop    - Stop memory stress testing"
  echo "  restart - Restart memory stress testing"
  echo "  status  - Show system status"
  ;;
esac
