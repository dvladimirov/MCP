#!/bin/bash
# Script to kill all running Kubernetes simulator processes
# This script finds and terminates all K8s data generators and simulators

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Kubernetes Process Cleanup Utility ===${NC}"

# Find all running instances of the K8s data generators and simulators
DUMMY_DATA_PIDS=$(pgrep -f "python3.*k8s_dummy_data_generator.py")
POD_SIMULATOR_PIDS=$(pgrep -f "python3.*k8s_pod_simulator.py")
ALL_PIDS="$DUMMY_DATA_PIDS $POD_SIMULATOR_PIDS"

# Check if any processes were found
if [ -z "$ALL_PIDS" ]; then
  echo -e "${GREEN}No running Kubernetes generators or simulators found.${NC}"
  exit 0
fi

# Count total processes
DUMMY_DATA_COUNT=$(echo "$DUMMY_DATA_PIDS" | grep -v '^$' | wc -l)
POD_SIMULATOR_COUNT=$(echo "$POD_SIMULATOR_PIDS" | grep -v '^$' | wc -l)
TOTAL_COUNT=$((DUMMY_DATA_COUNT + POD_SIMULATOR_COUNT))

# Show a summary
echo -e "${YELLOW}Found $TOTAL_COUNT Kubernetes processes:${NC}"
[ $DUMMY_DATA_COUNT -gt 0 ] && echo -e " - ${YELLOW}$DUMMY_DATA_COUNT${NC} dummy data generator(s)"
[ $POD_SIMULATOR_COUNT -gt 0 ] && echo -e " - ${YELLOW}$POD_SIMULATOR_COUNT${NC} pod simulator(s)"

# Display the processes
if [ $DUMMY_DATA_COUNT -gt 0 ]; then
  echo -e "\n${BLUE}Dummy Data Generator processes:${NC}"
  ps -p $DUMMY_DATA_PIDS -o pid,cmd | grep -v PID
fi

if [ $POD_SIMULATOR_COUNT -gt 0 ]; then
  echo -e "\n${BLUE}Pod Simulator processes:${NC}"
  ps -p $POD_SIMULATOR_PIDS -o pid,cmd | grep -v PID
fi

# Confirm killing
echo -e "\n${YELLOW}Do you want to terminate all these processes? (y/n)${NC}"
read -p "> " confirm

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo -e "${YELLOW}Operation canceled.${NC}"
  exit 0
fi

# Kill all processes
echo -e "${BLUE}Terminating processes...${NC}"

# First try a graceful termination with SIGTERM
for PID in $ALL_PIDS; do
  if ps -p $PID > /dev/null; then
    echo -e "Terminating process ${YELLOW}$PID${NC}"
    kill $PID
  fi
done

# Wait a bit for processes to terminate
sleep 2

# Check if any processes are still running
REMAINING_PIDS=$(pgrep -f "python3.*(k8s_dummy_data_generator|k8s_pod_simulator).py")

if [ -n "$REMAINING_PIDS" ]; then
  echo -e "${YELLOW}Some processes didn't terminate gracefully, forcing termination...${NC}"
  
  # Force kill with SIGKILL
  for PID in $REMAINING_PIDS; do
    if ps -p $PID > /dev/null; then
      echo -e "Force terminating process ${YELLOW}$PID${NC}"
      kill -9 $PID
    fi
  done
fi

# Final verification
REMAINING=$(pgrep -f "python3.*(k8s_dummy_data_generator|k8s_pod_simulator).py")

if [ -z "$REMAINING" ]; then
  echo -e "\n${GREEN}All Kubernetes simulator processes have been terminated.${NC}"
else
  echo -e "\n${RED}Warning: Some processes could not be terminated.${NC}"
  echo -e "Remaining processes:"
  ps -p $REMAINING -o pid,cmd
  exit 1
fi

exit 0 