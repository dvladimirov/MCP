#!/bin/bash
# Reset script for all containerized services

# Color formatting
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}     MCP Services Reset Script          ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Stop all services
echo -e "\n${YELLOW}Stopping all services...${NC}"
docker compose down

# Remove volumes if specified
if [[ "$1" == "--clean" ]]; then
    echo -e "\n${YELLOW}Removing volumes...${NC}"
    docker volume rm prometheus_data grafana-data 2>/dev/null || true
fi

# Rebuild images
echo -e "\n${YELLOW}Rebuilding custom images...${NC}"
docker compose build prometheus langflow

# Start all services
echo -e "\n${YELLOW}Starting all services...${NC}"
docker compose up -d

echo -e "\n${GREEN}Done! All services have been rebuilt with fresh configuration.${NC}"
echo -e "${YELLOW}Check logs for any issues:${NC}"
echo -e "  docker compose logs --follow"
echo -e "  or check a specific service:"
echo -e "  docker compose logs --tail=20 prometheus"
echo -e "  docker compose logs --tail=20 langflow"

echo -e "\n${BLUE}=========================================${NC}"
echo -e "${GREEN}Available services:${NC}"
echo -e "- Prometheus: http://localhost:9090"
echo -e "- Grafana: http://localhost:3000 (admin/admin)"
echo -e "- Langflow: http://localhost:7860"
echo -e "${BLUE}=========================================${NC}" 