#!/bin/bash
# Backup script for Docker configuration files

# Color formatting
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create backup directory
BACKUP_DIR="docker-config-backup-$(date +%Y%m%d-%H%M%S)"
echo -e "${BLUE}Creating backup directory: ${BACKUP_DIR}${NC}"
mkdir -p "${BACKUP_DIR}"

# List of files to backup
FILES_TO_BACKUP=(
  "docker-compose.yml"
  "docker-compose.bridge.yml"
  "Dockerfile.prometheus"
  "Dockerfile.langflow"
  "Dockerfile.memory-stress"
  "reset-all.sh"
  "reset-prometheus.sh"
  "reset-langflow.sh"
  "prometheus/prometheus.yml"
  "prometheus/memory_alerts.yml"
)

# Copy each file to backup directory
for file in "${FILES_TO_BACKUP[@]}"; do
  if [ -f "$file" ]; then
    echo -e "${GREEN}Backing up: ${file}${NC}"
    # Create directory structure if needed
    dir=$(dirname "${BACKUP_DIR}/${file}")
    mkdir -p "$dir"
    # Copy the file
    cp "$file" "${BACKUP_DIR}/${file}"
  else
    echo -e "${RED}Warning: ${file} not found, skipping${NC}"
  fi
done

# Create archive
echo -e "${YELLOW}Creating archive...${NC}"
tar -czf "${BACKUP_DIR}.tar.gz" "${BACKUP_DIR}"

# Clean up
echo -e "${YELLOW}Cleaning up temporary directory...${NC}"
rm -rf "${BACKUP_DIR}"

echo -e "${GREEN}Backup completed: ${BACKUP_DIR}.tar.gz${NC}"
echo -e "${BLUE}To restore:${NC}"
echo -e "  tar -xzf ${BACKUP_DIR}.tar.gz"
echo -e "  cp -r ${BACKUP_DIR}/* ." 