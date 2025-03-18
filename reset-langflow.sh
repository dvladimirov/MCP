#!/bin/bash
# Simple script to rebuild Langflow container with fresh configuration

# Color formatting
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping Langflow container...${NC}"
docker compose stop langflow

echo -e "${YELLOW}Rebuilding and starting Langflow container...${NC}"
docker compose up -d --build langflow

echo -e "${GREEN}Done! Langflow has been rebuilt with fresh configuration.${NC}"
echo -e "${YELLOW}Check logs for any issues:${NC}"
echo -e "  docker compose logs --tail=20 langflow" 