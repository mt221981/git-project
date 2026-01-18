#!/bin/bash
# Backup script for Legal Content System
# Creates backups of database and uploaded files

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_BACKUP_FILE="db_backup_${TIMESTAMP}.sql"
UPLOADS_BACKUP_FILE="uploads_backup_${TIMESTAMP}.tar.gz"
STORAGE_BACKUP_FILE="storage_backup_${TIMESTAMP}.tar.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Legal Content System Backup${NC}"
echo -e "${GREEN}Timestamp: ${TIMESTAMP}${NC}"
echo -e "${GREEN}========================================${NC}"

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

# Backup database
echo -e "${YELLOW}Backing up database...${NC}"
docker-compose exec -T postgres pg_dump -U "${POSTGRES_USER:-postgres}" "${POSTGRES_DB:-legal_content_db}" > "$BACKUP_DIR/$DB_BACKUP_FILE"

# Compress database backup
gzip "$BACKUP_DIR/$DB_BACKUP_FILE"
DB_BACKUP_FILE="${DB_BACKUP_FILE}.gz"

echo -e "${GREEN}✓ Database backed up: $DB_BACKUP_FILE${NC}"

# Backup uploads directory
echo -e "${YELLOW}Backing up uploads directory...${NC}"
if docker-compose exec -T backend test -d /app/uploads; then
    docker-compose exec -T backend tar czf - /app/uploads > "$BACKUP_DIR/$UPLOADS_BACKUP_FILE"
    echo -e "${GREEN}✓ Uploads backed up: $UPLOADS_BACKUP_FILE${NC}"
else
    echo -e "${YELLOW}⚠ Uploads directory not found, skipping${NC}"
fi

# Backup storage directory
echo -e "${YELLOW}Backing up storage directory...${NC}"
if docker-compose exec -T backend test -d /app/storage; then
    docker-compose exec -T backend tar czf - /app/storage > "$BACKUP_DIR/$STORAGE_BACKUP_FILE"
    echo -e "${GREEN}✓ Storage backed up: $STORAGE_BACKUP_FILE${NC}"
else
    echo -e "${YELLOW}⚠ Storage directory not found, skipping${NC}"
fi

# Calculate sizes
DB_SIZE=$(du -h "$BACKUP_DIR/$DB_BACKUP_FILE" | cut -f1)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Backup completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Database backup: $DB_SIZE"
echo -e "Total backup size: $TOTAL_SIZE"
echo -e "Location: $BACKUP_DIR"
echo -e ""
echo -e "${YELLOW}Files created:${NC}"
echo -e "  - $DB_BACKUP_FILE"
if [ -f "$BACKUP_DIR/$UPLOADS_BACKUP_FILE" ]; then
    echo -e "  - $UPLOADS_BACKUP_FILE"
fi
if [ -f "$BACKUP_DIR/$STORAGE_BACKUP_FILE" ]; then
    echo -e "  - $STORAGE_BACKUP_FILE"
fi

# Cleanup old backups (keep last 7 days)
echo -e ""
echo -e "${YELLOW}Cleaning up old backups (keeping last 7 days)...${NC}"
find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete
echo -e "${GREEN}✓ Cleanup completed${NC}"

echo -e "${GREEN}Done!${NC}"
