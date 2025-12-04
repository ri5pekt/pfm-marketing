# Production Deployment Guide

## Prerequisites

- Server with root SSH access: `31.220.56.146`
- Domain: `marketing.pfm-qa.com` (A record pointing to server IP)
- Docker and Docker Compose installed on server

## Initial Setup (One-time)

### 1. Connect to Server

```bash
ssh root@31.220.56.146
```

### 2. Run Setup Script

```bash
# Copy the setup script to server
scp deploy/production-setup.sh root@31.220.56.146:/tmp/

# On server, make executable and run
ssh root@31.220.56.146
chmod +x /tmp/production-setup.sh
/tmp/production-setup.sh
```

Or manually:

```bash
# Install dependencies
apt-get update
apt-get install -y git docker.io docker-compose-plugin nginx certbot python3-certbot-nginx

# Create project directory
mkdir -p /var/www/pfm-marketing
cd /var/www/pfm-marketing

# Clone repository
git clone https://github.com/ri5pekt/pfm-marketing.git .

# Create .env file
nano .env
# Add production environment variables (see below)

# Setup nginx
cp deploy/nginx.conf /etc/nginx/sites-available/marketing.pfm-qa.com
ln -s /etc/nginx/sites-available/marketing.pfm-qa.com /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# Get SSL certificate
certbot --nginx -d marketing.pfm-qa.com --non-interactive --agree-tos --email admin@pfm-qa.com

# Start services
docker compose build
docker compose up -d

# Create admin user
docker compose exec backend python -m app.scripts.create_user \
    --email admin@pfm-qa.com \
    --password "YOUR_SECURE_PASSWORD" \
    --admin
```

## Environment Variables (.env)

Create `/var/www/pfm-marketing/.env`:

```env
SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32
DATABASE_URL=postgresql+psycopg2://postgres:your-db-password@db:5432/pfm_marketing
REDIS_URL=redis://redis:6379/0
BACKEND_CORS_ORIGINS=["https://marketing.pfm-qa.com"]
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENVIRONMENT=production
```

## Updating the Application

### Option 1: Using Deploy Script

```bash
# Copy deploy script to server
scp deploy/deploy.sh root@31.220.56.146:/var/www/pfm-marketing/

# On server
ssh root@31.220.56.146
cd /var/www/pfm-marketing
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Manual Update

```bash
ssh root@31.220.56.146
cd /var/www/pfm-marketing
git pull origin main
docker compose build
docker compose down
docker compose up -d
```

## Nginx Configuration

The nginx configuration is in `deploy/nginx.conf`. It:
- Redirects HTTP to HTTPS
- Proxies frontend (port 5173) to `/`
- Proxies backend API (port 8000) to `/api`
- Includes security headers
- Uses Let's Encrypt SSL certificates

## SSL Certificate Renewal

Certbot automatically renews certificates. To test renewal:

```bash
certbot renew --dry-run
```

## Service Management

```bash
# Check service status
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Restart services
docker compose restart

# Stop services
docker compose down

# Start services
docker compose up -d
```

## Troubleshooting

### Check nginx status
```bash
systemctl status nginx
nginx -t
```

### Check Docker containers
```bash
docker compose ps
docker compose logs
```

### Check SSL certificate
```bash
certbot certificates
```

### Test domain
```bash
curl -I https://marketing.pfm-qa.com
```

## Security Notes

1. **Change default passwords** in `.env` file
2. **Use strong SECRET_KEY** (generate with `openssl rand -hex 32`)
3. **Keep Docker and system updated**: `apt-get update && apt-get upgrade`
4. **Monitor logs** regularly
5. **Backup database** regularly
6. **Use firewall** (ufw) to restrict access if needed

## Backup

```bash
# Backup database
docker compose exec db pg_dump -U postgres pfm_marketing > backup_$(date +%Y%m%d).sql

# Restore database
docker compose exec -T db psql -U postgres pfm_marketing < backup_YYYYMMDD.sql
```

