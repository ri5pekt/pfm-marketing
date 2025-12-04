# Quick Start Guide

## Initial Setup

1. **Copy environment file**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and set a secure SECRET_KEY**
   ```bash
   # Generate a random secret key (example)
   SECRET_KEY=your-super-secret-key-here-change-in-production
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Wait for services to be ready** (about 30 seconds)

5. **Create an admin user**
   ```bash
   docker-compose exec backend python -m app.scripts.create_user --email admin@example.com --password admin123 --admin
   ```

6. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Login

Use the credentials you created:
- Email: `admin@example.com`
- Password: `admin123` (or whatever you set)

## First Steps

1. **Login** to the application
2. **Navigate to Meta Campaigns** from the sidebar
3. **Create your first rule**:
   - Click "Create Rule"
   - Fill in the form:
     - Name: e.g., "Daily Campaign Check"
     - Schedule: e.g., `0 */6 * * *` (every 6 hours)
     - Meta Account ID: Your Meta account ID
     - Meta Access Token: Your Meta API access token
   - Click "Create"

## Cron Schedule Examples

- `0 */6 * * *` - Every 6 hours
- `0 9 * * *` - Daily at 9 AM
- `*/30 * * * *` - Every 30 minutes
- `0 0 * * 1` - Every Monday at midnight

## Troubleshooting

### Services won't start
- Check if ports 5433, 6379, 8000, 5173 are available
- Check Docker logs: `docker-compose logs`

### Database connection errors
- Wait a bit longer for PostgreSQL to initialize
- Check: `docker-compose logs db`

### Frontend can't connect to backend
- Verify `VITE_API_BASE_URL` in `.env` matches your setup
- Check backend is running: `docker-compose ps`

### Can't login
- Verify user was created: `docker-compose exec backend python -m app.scripts.create_user --email test@test.com --password test123`
- Check backend logs for errors

## Development

### Backend Development
- Code is hot-reloaded automatically
- Check logs: `docker-compose logs -f backend`

### Frontend Development
- For local development: `cd frontend && npm install && npm run dev`
- Or use Docker: `docker-compose logs -f frontend`

### Database Access
```bash
docker-compose exec db psql -U postgres -d pfm_marketing
```

### Redis Access
```bash
docker-compose exec redis redis-cli
```

## Next Steps

1. Implement Meta API integration in `backend/app/features/meta_campaigns/worker.py`
2. Add rule conditions and actions UI
3. Configure production environment variables
4. Set up SSL/TLS certificates
5. Configure backup strategy for database

