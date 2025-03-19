#!/bin/bash
# This script creates a Grafana API key for use with the MCP-Grafana Bridge
# Uses the new service account token API

# Default values
GRAFANA_URL=${GRAFANA_URL:-http://localhost:3000}
GRAFANA_USER=${GRAFANA_USER:-admin}
GRAFANA_PASSWORD=${GRAFANA_PASSWORD:-admin}
SERVICE_ACCOUNT_NAME="mcp-grafana-bridge"
TOKEN_NAME="mcp-grafana-bridge-token"

echo "Creating Grafana Service Account and Token..."
echo "Grafana URL: $GRAFANA_URL"
echo "Service Account Name: $SERVICE_ACCOUNT_NAME"
echo "Token Name: $TOKEN_NAME"
echo "---------------------------------"

# Step 1: Create a Service Account
echo "Creating service account..."
SA_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" \
  -d "{\"name\":\"$SERVICE_ACCOUNT_NAME\", \"role\":\"Admin\", \"isDisabled\":false}" \
  -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
  "$GRAFANA_URL/api/serviceaccounts")

# Extract service account ID
SA_ID=$(echo $SA_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$SA_ID" ]; then
  echo "Failed to create service account. Error response:"
  echo $SA_RESPONSE
  exit 1
fi

echo "Service account created with ID: $SA_ID"

# Step 2: Create a Token for the Service Account
echo "Creating token for service account..."
TOKEN_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" \
  -d "{\"name\":\"$TOKEN_NAME\", \"role\":\"Admin\"}" \
  -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
  "$GRAFANA_URL/api/serviceaccounts/$SA_ID/tokens")

# Extract token
API_KEY=$(echo $TOKEN_RESPONSE | grep -o '"key":"[^"]*"' | cut -d'"' -f4)

if [ -z "$API_KEY" ]; then
  echo "Failed to create token. Error response:"
  echo $TOKEN_RESPONSE
  exit 1
fi

echo "API token created successfully!"
echo "---------------------------------"
echo "To use this token with MCP-Grafana Bridge, you can:"
echo ""
echo "1. Export it as an environment variable:"
echo "   export GRAFANA_API_KEY=$API_KEY"
echo ""
echo "2. Add it to a .env file:"
echo "   echo \"GRAFANA_API_KEY=$API_KEY\" >> .env"
echo ""
echo "3. Pass it directly when starting docker-compose:"
echo "   GRAFANA_API_KEY=$API_KEY docker-compose up -d"
echo "---------------------------------"
echo "GRAFANA_API_KEY=$API_KEY" 