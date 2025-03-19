#!/bin/bash
# Startup script for MCP-Grafana Bridge
# This script will automatically create a Grafana API key if one is not provided

# Install required packages
echo "Installing required packages..."
apt-get update
apt-get install -y curl
pip install flask requests jinja2

# MCP-Grafana Bridge startup script
echo "Starting MCP-Grafana Bridge..."

# Check if GRAFANA_API_KEY is provided
if [ -z "$GRAFANA_API_KEY" ]; then
    echo "No Grafana API key provided. Will attempt to create one automatically."
    
    # Define Grafana settings from environment variables or use defaults
    GRAFANA_URL=${GRAFANA_URL:-http://grafana:3000}
    GRAFANA_USERNAME=${GRAFANA_USERNAME:-admin}
    GRAFANA_PASSWORD=${GRAFANA_PASSWORD:-admin}
    SA_NAME="mcp-service-account"
    
    # Wait for Grafana to be available before attempting to create API key
    echo "Waiting for Grafana to be available at $GRAFANA_URL..."
    MAX_ATTEMPTS=30
    ATTEMPT=0
    
    until $(curl --output /dev/null --silent --fail --max-time 5 $GRAFANA_URL/api/health); do
        ATTEMPT=$((ATTEMPT+1))
        if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
            echo "Grafana not available after $MAX_ATTEMPTS attempts. Proceeding with default authentication."
            break
        fi
        echo "Grafana not yet available, retrying in 2 seconds... (Attempt $ATTEMPT/$MAX_ATTEMPTS)"
        sleep 2
    done
    
    # If Grafana is available, create a service account and token
    if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
        echo "Grafana is available. Creating Grafana service account and token..."
        
        # Try to find existing service account first
        echo "Checking for existing service account..."
        SA_LIST=$(curl -s -X GET -H "Content-Type: application/json" \
            -u "$GRAFANA_USERNAME:$GRAFANA_PASSWORD" \
            "$GRAFANA_URL/api/serviceaccounts/search?query=$SA_NAME")
        
        SA_ID=$(echo $SA_LIST | grep -o '"id":[0-9]\+' | head -1 | cut -d':' -f2)
        
        # If service account doesn't exist, create it
        if [ -z "$SA_ID" ]; then
            echo "Creating new service account..."
            SA_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" \
                -d "{\"name\":\"$SA_NAME\", \"role\": \"Admin\"}" \
                -u "$GRAFANA_USERNAME:$GRAFANA_PASSWORD" \
                "$GRAFANA_URL/api/serviceaccounts")
            
            SA_ID=$(echo $SA_RESPONSE | grep -o '"id":[0-9]\+' | head -1 | cut -d':' -f2)
            
            if [ -z "$SA_ID" ]; then
                echo "Failed to create service account. Error response:"
                echo "$SA_RESPONSE"
                echo "Falling back to basic auth."
            else
                echo "Service account created with ID: $SA_ID"
            fi
        else
            echo "Found existing service account with ID: $SA_ID"
        fi
        
        # If we have a service account ID, create a token
        if [ ! -z "$SA_ID" ]; then
            echo "Creating token for service account..."
            TOKEN_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" \
                -d '{"name":"mcp-token", "secondsToLive": 86400}' \
                -u "$GRAFANA_USERNAME:$GRAFANA_PASSWORD" \
                "$GRAFANA_URL/api/serviceaccounts/$SA_ID/tokens")
            
            GRAFANA_API_KEY=$(echo $TOKEN_RESPONSE | grep -o '"key":"[^"]\+' | head -1 | cut -d':' -f2 | tr -d '"')
            
            if [ ! -z "$GRAFANA_API_KEY" ]; then
                echo "Successfully created API token"
                export GRAFANA_API_KEY
            else
                echo "Failed to create API token. Response: $TOKEN_RESPONSE"
                echo "Falling back to basic auth."
            fi
        fi
    fi
else
    echo "Using provided Grafana API key"
fi

# Start the MCP-Grafana Bridge
if [ ! -z "$GRAFANA_API_KEY" ]; then
    echo "Using API key for Grafana authentication"
else
    echo "Using basic auth for Grafana authentication"
fi

echo "Starting MCP-Grafana Bridge..."
python mcp_grafana_bridge.py 