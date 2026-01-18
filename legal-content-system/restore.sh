#!/bin/bash
# Restore script for Legal Content System
# Restores database and uploaded files from backup

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
BACKUP_DIR="./backups"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Legal Content System Restore${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}Error: Backup directory not found!${NC}"
    exit 1
fi

# List available backups
echo -e "${YELLOW}Available database backups:${NC}"
DB_BACKUPS=($(ls -1t "$BACKUP_DIR"/db_backup_*.sql.gz 2>/dev/null || true))

if [ ${#DB_BACKUPS[@]} -eq 0 ]; then
    echo -e "${RED}No database backups found!${NC}"
    exit 1
fi

# Display backups with numbers
for i in "${!DB_BACKUPS[@]}"; do
    FILENAME=$(basename "${DB_BACKUPS[$i]}")
    SIZE=$(du -h "${DB_BACKUPS[$i]}" | cut -f1)
    echo -e "  [$((i+1))] $FILENAME ($SIZE)"
done

# Ask user to select backup
echo -e ""
read -p "Select backup to restore (1-${#DB_BACKUPS[@]}): " SELECTION

# Validate selection
if ! [[ "$SELECTION" =~ ^[0-9]+$ ]] || [ "$SELECTION" -lt 1 ] || [ "$SELECTION" -gt ${#DB_BACKUPS[@]} ]; then
    echo -e "${RED}Invalid selection!${NC}"
    exit 1
fi

SELECTED_BACKUP="${DB_BACKUPS[$((SELECTION-1))]}"
echo -e "${YELLOW}Selected: $(basename $SELECTED_BACKUP)${NC}"

# Confirm
read -p "Are you sure you want to restore? This will overwrite current data! (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}Restore cancelled.${NC}"
    exit 0
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${RED}Error: .env file not found!${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running!${NC}"
    exit 1
fi

# Extract timestamp from filename
TIMESTAMP=$(basename "$SELECTED_BACKUP" | sed 's/db_backup_\(.*\)\.sql\.gz/\1/')

# Restore database
echo -e "${YELLOW}Restoring database...${NC}"
gunzip -c "$SELECTED_BACKUP" | docker-compose exec -T postgres psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-legal_content_db}"
echo -e "${GREEN}✓ Database restored${NC}"

# Restore uploads if backup exists
UPLOADS_BACKUP="$BACKUP_DIR/uploads_backup_${TIMESTAMP}.tar.gz"
if [ -f "$UPLOADS_BACKUP" ]; then
    echo -e "${YELLOW}Restoring uploads directory...${NC}"
    cat "$UPLOADS_BACKUP" | docker-compose exec -T backend tar xzf - -C /
    echo -e "${GREEN}✓ Uploads restored${NC}"
else
    echo -e "${YELLOW}⚠ Uploads backup not found for this timestamp${NC}"
fi

# Restore storage if backup exists
STORAGE_BACKUP="$BACKUP_DIR/storage_backup_${TIMESTAMP}.tar.gz"
if [ -f "$STORAGE_BACKUP" ]; then
    echo -e "${YELLOW}Restoring storage directory...${NC}"
    cat "$STORAGE_BACKUP" | docker-compose exec -T backend tar xzf - -C /
    echo -e "${GREEN}✓ Storage restored${NC}"
else
    echo -e "${YELLOW}⚠ Storage backup not found for this timestamp${NC}"
fi

# Restart services
echo -e "${YELLOW}Restarting services...${NC}"
docker-compose restart backend

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Restore completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Done!${NC}"
