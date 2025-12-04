#!/bin/bash
# Quick deployment script - run from your local machine
# This script will SSH to the server and deploy

SERVER="root@31.220.56.146"
PROJECT_DIR="/var/www/pfm-marketing"

echo "Deploying to production server..."

# Copy deployment script to server
scp deploy/deploy.sh $SERVER:/tmp/deploy.sh

# Run deployment on server
ssh $SERVER "chmod +x /tmp/deploy.sh && cd $PROJECT_DIR && /tmp/deploy.sh"

echo "Deployment initiated. Check https://marketing.pfm-qa.com"

