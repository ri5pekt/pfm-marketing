# Quick Start - Production Deployment

## Step 1: Connect to Server

```bash
ssh root@31.220.56.146
```

## Step 2: Run Initial Setup

Copy and paste this entire block into your SSH session:

```bash
# Install dependencies
apt-get update
apt-get install -y git docker.io docker-compose-plugin nginx certbot python3-certbot-nginx

# Create project directory
mkdir -p /var/www/pfm-marketing
cd /var/www/pfm-marketing

# Clone repository
git clone https://github.com/ri5pekt/pfm-marketing.git .

# Create .env file with secure values
cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)
DATABASE_URL=postgresql+psycopg2://postgres:\${DB_PASSWORD}@db:5432/pfm_marketing
REDIS_URL=redis://redis:6379/0
BACKEND_CORS_ORIGINS=["https://marketing.pfm-qa.com"]
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENVIRONMENT=production
EOF

# Setup nginx
cp deploy/nginx.conf /etc/nginx/sites-available/marketing.pfm-qa.com
ln -sf /etc/nginx/sites-available/marketing.pfm-qa.com /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# Get SSL certificate
certbot --nginx -d marketing.pfm-qa.com --non-interactive --agree-tos --email admin@pfm-qa.com --redirect

# Build and start services
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Wait for services
sleep 15

# Create admin user (change password!)
docker compose -f docker-compose.prod.yml exec -T backend python -m app.scripts.create_user \
    --email admin@pfm-qa.com \
    --password "CHANGE_THIS_PASSWORD" \
    --admin

echo "Setup complete! Visit https://marketing.pfm-qa.com"
echo "IMPORTANT: Change the admin password!"
```

## Step 3: Verify Deployment

1. Visit: https://marketing.pfm-qa.com
2. Login with: `admin@pfm-qa.com` / `CHANGE_THIS_PASSWORD`
3. **Change the password immediately!**

## Future Updates

To update the application:

```bash
ssh root@31.220.56.146
cd /var/www/pfm-marketing
git pull origin main
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

Or use the quick deploy script from your local machine:

```bash
bash deploy/quick-deploy.sh
```

## Troubleshooting

```bash
# Check service status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Check nginx
systemctl status nginx
nginx -t

# Test domain
curl -I https://marketing.pfm-qa.com
```

