#!/bin/bash
# Comprehensive Prometheus Testing Shell Script

# Default values
PROMETHEUS_URL=${1:-"https://prometheus.demo.do.prometheus.io"}
MCP_SERVER_URL=${2:-"http://localhost:8000"}

echo "======================================================"
echo "Prometheus MCP Testing Script"
echo "======================================================"
echo "Prometheus URL: $PROMETHEUS_URL"
echo "MCP Server URL: $MCP_SERVER_URL"
echo "======================================================" 

# Function to run a test with proper output formatting
run_test() {
    local test_name=$1
    local test_cmd=$2
    
    echo ""
    echo "------------------------------------------------------"
    echo "Running test: $test_name"
    echo "Command: $test_cmd"
    echo "------------------------------------------------------"
    eval $test_cmd
    
    local status=$?
    if [ $status -ne 0 ]; then
        echo "Test failed with status code: $status"
    else
        echo "Test completed successfully"
    fi
    echo "------------------------------------------------------"
    echo ""
}

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    echo "curl is not installed. Please install it to run this script."
    exit 1
fi

# Step 1: Test direct HTTP connection to Prometheus
echo "Step 1: Testing direct HTTP connection to Prometheus..."
run_test "Direct Prometheus HTTP query" "curl -s '$PROMETHEUS_URL/api/v1/query?query=up' | head -n 30"

# Step 2: Run the direct test script
echo "Step 2: Testing direct connection using our script..."
run_test "Direct test script" "python test_prometheus_direct.py $PROMETHEUS_URL"

# Step 3: Test if MCP server is running
echo "Step 3: Checking if MCP server is running..."
if curl -s "$MCP_SERVER_URL/v1/models" > /dev/null; then
    echo "MCP server is running at $MCP_SERVER_URL"
    run_test "MCP server models" "curl -s '$MCP_SERVER_URL/v1/models' | head -n 30"
else
    echo "MCP server is not running at $MCP_SERVER_URL"
    echo "Starting a new MCP server with the Prometheus URL..."
    
    # Export the environment variable
    export PROMETHEUS_URL="$PROMETHEUS_URL"
    echo "Set PROMETHEUS_URL environment variable to: $PROMETHEUS_URL"
    
    # Start the server in the background
    echo "Starting MCP server in the background..."
    python start_mcp_server.py --prometheus-url "$PROMETHEUS_URL" --debug &
    SERVER_PID=$!
    
    # Wait for the server to start
    echo "Waiting for the server to start..."
    sleep 5
    
    # Check if the server started successfully
    if curl -s "$MCP_SERVER_URL/v1/models" > /dev/null; then
        echo "MCP server started successfully with PID: $SERVER_PID"
        run_test "MCP server models" "curl -s '$MCP_SERVER_URL/v1/models' | head -n 30"
    else
        echo "Failed to start MCP server"
        if [ ! -z "$SERVER_PID" ]; then
            kill $SERVER_PID
        fi
        exit 1
    fi
fi

# Step 4: Test external Prometheus integration
echo "Step 4: Testing external Prometheus integration..."
run_test "External Prometheus integration" "python test_prometheus_external.py $PROMETHEUS_URL $MCP_SERVER_URL"

# Step 5: Test standard Prometheus test script
echo "Step 5: Testing with standard test script..."
run_test "Standard Prometheus test" "python test_prometheus.py --quiet"

echo "======================================================"
echo "All tests completed"
echo "======================================================"

# If we started the server, ask if the user wants to keep it running
if [ ! -z "$SERVER_PID" ]; then
    read -p "Keep the MCP server running? (y/n): " KEEP_RUNNING
    if [[ $KEEP_RUNNING != "y" && $KEEP_RUNNING != "Y" ]]; then
        echo "Stopping MCP server (PID: $SERVER_PID)..."
        kill $SERVER_PID
    else
        echo "MCP server is still running with PID: $SERVER_PID"
        echo "To stop it manually later, run: kill $SERVER_PID"
    fi
fi 