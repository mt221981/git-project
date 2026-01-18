#!/bin/bash
# Deployment script for Legal Content System
# Usage: ./deploy.sh [environment]
# Environments: dev, staging, production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default environment
ENVIRONMENT=${1:-production}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Legal Content System Deployment${NC}"
echo -e "${GREEN}Environment: ${ENVIRONMENT}${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please copy .env.production.example to .env and configure it.${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running!${NC}"
    echo -e "${YELLOW}Please start Docker and try again.${NC}"
    exit 1
fi

# Function to run database migrations
run_migrations() {
    echo -e "${YELLOW}Running database migrations...${NC}"
    docker-compose exec backend alembic upgrade head
    echo -e "${GREEN}✓ Migrations completed${NC}"
}

# Function to create initial superuser
create_superuser() {
    echo -e "${YELLOW}Creating superuser (if needed)...${NC}"
    docker-compose exec backend python -m app.scripts.create_superuser
    echo -e "${GREEN}✓ Superuser setup completed${NC}"
}

# Function to health check
health_check() {
    echo -e "${YELLOW}Performing health check...${NC}"

    # Check backend
    for i in {1..30}; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Backend is healthy${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}✗ Backend health check failed${NC}"
            exit 1
        fi
        sleep 2
    done

    # Check frontend
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is healthy${NC}"
    else
        echo -e "${RED}✗ Frontend health check failed${NC}"
        exit 1
    fi
}

# Main deployment flow
case "$ENVIRONMENT" in
    dev)
        echo -e "${YELLOW}Starting development environment...${NC}"
        docker-compose up -d postgres backend frontend
        ;;

    staging)
        echo -e "${YELLOW}Starting staging environment...${NC}"
        docker-compose up -d
        ;;

    production)
        echo -e "${YELLOW}Deploying to production...${NC}"

        # Pull latest images
        echo -e "${YELLOW}Pulling latest images...${NC}"
        docker-compose pull

        # Build services
        echo -e "${YELLOW}Building services...${NC}"
        docker-compose build --no-cache

        # Stop old containers
        echo -e "${YELLOW}Stopping old containers...${NC}"
        docker-compose down

        # Start services with nginx
        echo -e "${YELLOW}Starting services...${NC}"
        docker-compose --profile production up -d

        # Wait for services to be ready
        sleep 10

        # Run migrations
        run_migrations

        # Create superuser if needed
        # create_superuser

        # Health check
        health_check

        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}Deployment completed successfully!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo -e "${YELLOW}Services:${NC}"
        echo -e "  Backend API: http://localhost:8000"
        echo -e "  Frontend: http://localhost:3000"
        echo -e "  Nginx Proxy: http://localhost:80"
        echo -e ""
        echo -e "${YELLOW}Useful commands:${NC}"
        echo -e "  View logs: docker-compose logs -f [service]"
        echo -e "  Stop services: docker-compose down"
        echo -e "  Restart service: docker-compose restart [service]"
        ;;

    *)
        echo -e "${RED}Error: Unknown environment '${ENVIRONMENT}'${NC}"
        echo -e "${YELLOW}Usage: $0 [dev|staging|production]${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}Done!${NC}"
