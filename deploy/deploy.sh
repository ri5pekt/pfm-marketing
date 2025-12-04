#!/bin/bash
# Production deployment script
# Run this on the server to update the application

set -e

PROJECT_DIR="/var/www/pfm-marketing"

echo "Deploying to production..."

cd $PROJECT_DIR

# Pull latest changes
git pull origin main

# Rebuild and restart containers
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Run database migrations if needed
# docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.migrate_schedule_cron_nullable || true

echo "Deployment complete!"
echo "Services restarted. Check status with: docker compose -f docker-compose.prod.yml ps"

