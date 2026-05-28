# Deployment Guide — All Servers

## Server Reference

| | Old VPS — Particle ⚠️ | New VPS — Particle | New VPS — Blurr |
|---|---|---|---|
| **Client** | Particle For Man | Particle For Man | Blurr Beauty LTD |
| **IP** | `31.220.56.146` | `72.62.148.226` | `2.25.142.93` |
| **Domain** | `marketing.pfm-qa.com` | `pfm-marketing.cloud` | `blurr-marketing.cloud` |
| **SSH** | `ssh root@31.220.56.146` | `ssh root@72.62.148.226` | `ssh root@2.25.142.93` |
| **Status** | Legacy — do not touch | Active | To be deployed |

> ⚠️ **The old Particle VPS (`31.220.56.146`) remains fully operational. Do not modify it.**

---

## Quick Access

```bash
# Particle (new VPS)
ssh root@72.62.148.226

# Blurr Beauty
ssh root@2.25.142.93
```

---

## Nginx / Domain Notes

| Server | Nginx config file | CORS origin |
|---|---|---|
| Particle | `/etc/nginx/sites-available/pfm-marketing.cloud` | `https://pfm-marketing.cloud` |
| Blurr | `/etc/nginx/sites-available/blurr-marketing.cloud` | `https://blurr-marketing.cloud` |

---

## Phase 1 — Server Access & SSH Key Setup

On your local machine, copy your SSH key to the new server (run once):

```bash
ssh-copy-id root@72.62.148.226
# Enter root password when prompted
```

Then verify key-based access works:

```bash
ssh root@72.62.148.226
```

---

## Phase 2 — Server Check & System Prep

```bash
ssh root@72.62.148.226

# Check OS and resources
uname -a
lsb_release -a
nproc
free -h
df -h /

# Update system
apt-get update && apt-get upgrade -y
```

---

## Phase 3 — Install Docker & Docker Compose

```bash
# Install Docker
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify
docker --version
docker compose version

# Enable Docker on boot
systemctl enable docker
systemctl start docker
```

---

## Phase 4 — Install Nginx & Certbot

```bash
apt-get install -y nginx certbot python3-certbot-nginx

systemctl enable nginx
systemctl start nginx
```

---

## Phase 5 — Create Project Directory & Clone Repo

```bash
mkdir -p /var/www/pfm-marketing
cd /var/www/pfm-marketing

git clone https://github.com/ri5pekt/pfm-marketing.git .

# Verify version
cat frontend/src/config/version.js
```

---

## Phase 6 — Create Environment File

```bash
cd /var/www/pfm-marketing
nano .env
```

Paste the following (replace placeholder values):

**Particle server:**
```env
SECRET_KEY=<generate: openssl rand -hex 32>
DB_PASSWORD=<your-secure-db-password>
DATABASE_URL=postgresql+psycopg2://postgres:<your-secure-db-password>@db:5432/pfm_marketing
REDIS_URL=redis://redis:6379/0
BACKEND_CORS_ORIGINS=["https://pfm-marketing.cloud"]
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENVIRONMENT=production
```

**Blurr server:**
```env
SECRET_KEY=<generate: openssl rand -hex 32>
DB_PASSWORD=<your-secure-db-password>
DATABASE_URL=postgresql+psycopg2://postgres:<your-secure-db-password>@db:5432/pfm_marketing
REDIS_URL=redis://redis:6379/0
BACKEND_CORS_ORIGINS=["https://blurr-marketing.cloud"]
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENVIRONMENT=production
```

Generate a secret key:

```bash
openssl rand -hex 32
```

---

## Phase 7 — Configure Nginx

Replace `YOUR_DOMAIN` below with the actual domain for the server you are deploying:
- Particle: `pfm-marketing.cloud`
- Blurr: `blurr-marketing.cloud`

```bash
# Particle:
nano /etc/nginx/sites-available/pfm-marketing.cloud

# Blurr:
nano /etc/nginx/sites-available/blurr-marketing.cloud
```

Paste (substituting your domain):

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN www.YOUR_DOMAIN;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

Enable the site:

```bash
# Particle:
ln -s /etc/nginx/sites-available/pfm-marketing.cloud /etc/nginx/sites-enabled/

# Blurr:
ln -s /etc/nginx/sites-available/blurr-marketing.cloud /etc/nginx/sites-enabled/

rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
```

---

## Phase 8 — DNS Setup

Before getting SSL, point the domain DNS to the correct server IP:

**Particle (`pfm-marketing.cloud`):**

| Type | Name | Value |
|---|---|---|
| A | `@` | `72.62.148.226` |
| A | `www` | `72.62.148.226` |

**Blurr (`blurr-marketing.cloud`):**

| Type | Name | Value |
|---|---|---|
| A | `@` | `2.25.142.93` |
| A | `www` | `2.25.142.93` |

Verify DNS has propagated:

```bash
# Particle
nslookup pfm-marketing.cloud
# Should return 72.62.148.226

# Blurr
nslookup blurr-marketing.cloud
# Should return 2.25.142.93
```

---

## Phase 9 — SSL Certificate

**Particle:**
```bash
certbot --nginx -d pfm-marketing.cloud -d www.pfm-marketing.cloud \
  --non-interactive --agree-tos --email admin@pfm-marketing.cloud
```

**Blurr:**
```bash
certbot --nginx -d blurr-marketing.cloud -d www.blurr-marketing.cloud \
  --non-interactive --agree-tos --email admin@blurr-marketing.cloud
```

Test auto-renewal:

```bash
certbot renew --dry-run
```

---

## Phase 10 — Build & Start Docker Services

```bash
cd /var/www/pfm-marketing

# Build images
docker compose -f docker-compose.prod.yml build

# Start all services
docker compose -f docker-compose.prod.yml up -d

# Check all containers are healthy
docker compose -f docker-compose.prod.yml ps
```

---

## Phase 11 — Create Admin User

**Particle:**
```bash
cd /var/www/pfm-marketing

docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.create_user \
    --email admin@pfm-marketing.cloud \
    --password "YOUR_SECURE_PASSWORD" \
    --admin
```

**Blurr:**
```bash
cd /var/www/pfm-marketing

docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.create_user \
    --email admin@blurr-marketing.cloud \
    --password "YOUR_SECURE_PASSWORD" \
    --admin
```

---

## Phase 12 — Verify Deployment

```bash
# Check all containers running
docker compose -f docker-compose.prod.yml ps

# Check backend health
curl -I http://127.0.0.1:8001/api/health

# Check frontend
curl -I http://127.0.0.1:5173

# Check via domain (use relevant domain)
curl -I https://pfm-marketing.cloud    # Particle
curl -I https://blurr-marketing.cloud  # Blurr
```

---

## Data Migration (After New Server is Verified)

Once the new server is confirmed working with fresh data, migrate the database from the old server:

```bash
# On OLD server — export database
ssh root@31.220.56.146
cd /var/www/pfm-marketing
docker compose -f docker-compose.prod.yml exec db \
    pg_dump -U postgres pfm_marketing > /tmp/pfm_backup_$(date +%Y%m%d).sql

# Copy backup to new server
scp root@31.220.56.146:/tmp/pfm_backup_*.sql root@72.62.148.226:/tmp/

# On NEW server — stop services, restore, restart
ssh root@72.62.148.226
cd /var/www/pfm-marketing
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d db redis
sleep 10
docker compose -f docker-compose.prod.yml exec -T db \
    psql -U postgres pfm_marketing < /tmp/pfm_backup_*.sql
docker compose -f docker-compose.prod.yml up -d
```

---

## Updating the Application

**Particle:**
```bash
ssh root@72.62.148.226
cd /var/www/pfm-marketing
git pull origin main
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

**Blurr:**
```bash
ssh root@2.25.142.93
cd /var/www/pfm-marketing
git pull origin main
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

---

## Service Management

```bash
# Status
docker compose -f docker-compose.prod.yml ps

# Logs
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend

# Restart
docker compose -f docker-compose.prod.yml restart

# Stop
docker compose -f docker-compose.prod.yml down
```

---

## Deployment Status

### Particle — `pfm-marketing.cloud` (`72.62.148.226`)

- [x] Phase 1 — SSH key copied
- [x] Phase 2 — Server checked, system updated
- [x] Phase 3 — Docker installed
- [x] Phase 4 — Nginx & Certbot installed
- [x] Phase 5 — Repo cloned
- [x] Phase 6 — `.env` file created
- [x] Phase 7 — Nginx config created
- [x] Phase 8 — DNS A records pointed to `72.62.148.226`
- [x] Phase 9 — SSL certificate issued
- [x] Phase 10 — Docker services running
- [x] Phase 11 — Admin user created
- [x] Phase 12 — Deployment verified

---

### Blurr Beauty — `blurr-marketing.cloud` (`2.25.142.93`)

- [ ] Phase 1 — SSH key copied to `2.25.142.93`
- [ ] Phase 2 — Server checked, system updated
- [ ] Phase 3 — Docker installed
- [ ] Phase 4 — Nginx & Certbot installed
- [ ] Phase 5 — Repo cloned
- [ ] Phase 6 — `.env` file created (CORS: `https://blurr-marketing.cloud`)
- [ ] Phase 7 — Nginx config created for `blurr-marketing.cloud`
- [ ] Phase 8 — DNS A records pointed to `2.25.142.93`
- [ ] Phase 9 — SSL certificate issued
- [ ] Phase 10 — Docker services running
- [ ] Phase 11 — Admin user created
- [ ] Phase 12 — Deployment verified
