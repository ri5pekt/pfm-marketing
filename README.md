# PFM Marketing

Marketing department tool for managing Meta campaigns with automated rules, scheduled checks, and logging.

## Version 3.0.0

### Major Features
- **Per-Condition Time Ranges**: Each condition can now specify its own time range for data fetching
- **CPP Winning Days**: New condition field that counts days where Cost Per Purchase was below a threshold
- **Amount of Active Ads**: New condition field to count active ads in campaigns/adsets
- **Enhanced Logging**: Detailed breakdowns for CPP Winning Days calculations in execution logs
- **Improved UI**: Refactored rule builder with better organization and user experience

### Technical Improvements
- Complete frontend refactoring: Split large components into smaller, maintainable modules
- Backend modularization: Separated concerns into focused modules (API client, condition evaluator, action executor, etc.)
- Better error handling and validation
- Enhanced special value support with multipliers

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.12)
- **Database**: PostgreSQL 16 with SQLAlchemy ORM
- **Cache/Queue**: Redis 7 with RQ (Redis Queue) and RQ-Scheduler
- **Authentication**: JWT with bcrypt password hashing

### Frontend
- **Framework**: Vue.js 3.4.0 (Composition API)
- **UI Library**: PrimeVue 4.4.1 (Aura theme)
- **Router**: Vue Router 4.2.5
- **Build Tool**: Vite 5.0.0

## Project Structure

```
pfm-marketing/
├── backend/
│   ├── app/
│   │   ├── auth/          # Authentication module
│   │   ├── core/          # Core configuration and utilities
│   │   ├── features/      # Feature modules
│   │   │   └── meta_campaigns/  # Meta campaigns automation
│   │   ├── jobs/          # Job models and queue utilities
│   │   └── main.py        # FastAPI app entry point
│   ├── worker.py          # RQ worker entry point
│   ├── scheduler.py       # Scheduler initialization
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/           # API client functions
│   │   ├── components/    # Reusable Vue components
│   │   ├── router/        # Vue Router configuration
│   │   ├── store/         # State management
│   │   ├── views/         # Page components
│   │   └── main.js        # Vue app entry point
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 20+ (for local frontend development)

### Setup

1. **Clone the repository** (if applicable)

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set `SECRET_KEY` to a random string.

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Create admin user**
   ```bash
   docker-compose exec backend python -m app.scripts.create_user --email admin@example.com --password yourpassword --admin
   ```

5. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Development

#### Backend Development
The backend code is mounted as a volume, so changes are reflected immediately with auto-reload.

#### Frontend Development
For local frontend development (outside Docker):
```bash
cd frontend
npm install
npm run dev
```

## Features

### Meta Campaigns Automation
- Create automated rules for Meta campaigns, adsets, and ads
- **Per-condition time ranges**: Each condition can use different time windows
- **CPP Winning Days**: Track performance consistency over time
- **Amount of Active Ads**: Monitor ad activation status
- Schedule rule checks using cron expressions
- View detailed execution logs with condition breakdowns
- Manual rule testing
- Full Meta API integration with rate limiting
- Support for all 12 standard automated rule types:
  - Auto Optimizer (#AO)
  - Late Attribution Reactivator (#AO)
  - Winners Booster 10% & 20% (#PGS)
  - Profitable Gate Scaling Increase/Decrease (#PGS)
  - Sunday Overspend Decrease (#PGS)
  - Stop-Loss Rule (#SLR)
  - Stop-Loss Reactivator (#SLR)
  - Stop-Loss Force Reactivator (#SLR)

### Authentication
- JWT-based authentication
- User roles (admin/user)
- Secure password hashing

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Meta Campaigns
- `GET /api/app/meta-campaigns/rules` - List all rules
- `POST /api/app/meta-campaigns/rules` - Create a rule
- `GET /api/app/meta-campaigns/rules/{id}` - Get a rule
- `PUT /api/app/meta-campaigns/rules/{id}` - Update a rule
- `DELETE /api/app/meta-campaigns/rules/{id}` - Delete a rule
- `GET /api/app/meta-campaigns/rules/{id}/logs` - Get rule logs
- `POST /api/app/meta-campaigns/rules/{id}/test` - Test a rule

## Docker Services

- **db**: PostgreSQL database
- **redis**: Redis cache and queue
- **backend**: FastAPI application
- **worker**: RQ worker for background jobs
- **scheduler**: RQ scheduler for scheduled tasks
- **frontend**: Vue.js development server

## Production Deployment

1. Update `.env` with production values
2. Set `ENVIRONMENT=production` in backend
3. Build frontend: `cd frontend && npm run build`
4. Use production Docker Compose configuration
5. Configure SSL/TLS certificates
6. Set up proper secrets management

## License

Proprietary - Internal use only

