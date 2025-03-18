#!/bin/bash
# Simple script to rebuild Prometheus container and reset its data volume

# Color formatting
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping Prometheus container...${NC}"
docker compose stop prometheus

echo -e "${YELLOW}Removing Prometheus data volume...${NC}"
docker volume rm prometheus_data 2>/dev/null || true

echo -e "${YELLOW}Rebuilding and starting Prometheus container...${NC}"
docker compose up -d --build prometheus

echo -e "${GREEN}Done! Prometheus has been rebuilt with fresh configuration.${NC}"
echo -e "${YELLOW}Check logs for any issues:${NC}"
echo -e "  docker compose logs --tail=20 prometheus" 