#!/bin/bash
# Production deployment setup script
# Run this on the server: ssh root@31.220.56.146

set -e

DOMAIN="marketing.pfm-qa.com"
PROJECT_DIR="/var/www/pfm-marketing"
REPO_URL="https://github.com/ri5pekt/pfm-marketing.git"

echo "Setting up production environment for $DOMAIN..."

# Update system
apt-get update
apt-get install -y git docker.io docker-compose-plugin nginx certbot python3-certbot-nginx

# Create project directory
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Clone repository if not exists
if [ ! -d ".git" ]; then
    git clone $REPO_URL .
else
    git pull origin main
fi

# Create .env file if not exists
if [ ! -f ".env" ]; then
    cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql+psycopg2://postgres:$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)@db:5432/pfm_marketing
REDIS_URL=redis://redis:6379/0
BACKEND_CORS_ORIGINS=["https://$DOMAIN"]
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENVIRONMENT=production
EOF
    echo ".env file created. Please review and update database password if needed."
fi

# Create nginx configuration
cat > /etc/nginx/sites-available/$DOMAIN << 'NGINX_EOF'
server {
    listen 80;
    server_name marketing.pfm-qa.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name marketing.pfm-qa.com;

    # SSL configuration (will be updated by certbot)
    ssl_certificate /etc/letsencrypt/live/marketing.pfm-qa.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/marketing.pfm-qa.com/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_buffering off;
    }

    # API Documentation
    location /docs {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX_EOF

# Enable site
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Start nginx
systemctl restart nginx

# Get SSL certificate
echo "Obtaining SSL certificate..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@pfm-qa.com --redirect

# Restart nginx with SSL
systemctl restart nginx

# Build and start Docker containers
cd $PROJECT_DIR
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Create admin user (if needed)
echo "Creating admin user..."
docker compose -f docker-compose.prod.yml exec -T backend python -m app.scripts.create_user \
    --email admin@pfm-qa.com \
    --password "CHANGE_THIS_PASSWORD" \
    --admin || echo "User may already exist"

echo "Setup complete!"
echo "Domain: https://$DOMAIN"
echo "Please update the admin password and review .env file"

