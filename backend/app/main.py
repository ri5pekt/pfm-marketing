# Patch for rq-scheduler compatibility with newer rq versions
import rq.utils
if not hasattr(rq.utils, 'ColorizingStreamHandler'):
    class ColorizingStreamHandler:
        pass
    rq.utils.ColorizingStreamHandler = ColorizingStreamHandler

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.db import engine, Base
from app.auth import routes as auth_routes
from app.features.meta_campaigns import routes as meta_campaigns_routes
from app.features.meta_campaigns import ad_account_routes
import os

# Create database tables (for development)
if os.getenv("ENVIRONMENT") != "production":
    Base.metadata.create_all(bind=engine)
    # Create default ad account if it doesn't exist
    try:
        from app.scripts.create_default_ad_account import create_default_ad_account
        create_default_ad_account()
    except Exception as e:
        print(f"Note: Could not create default ad account: {e}")

app = FastAPI(title="PFM Marketing API", version="2.0.0")

# CORS configuration
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

origins = []
if isinstance(settings.BACKEND_CORS_ORIGINS, str):
    # Try to parse as JSON first (for docker-compose environment variables)
    try:
        origins = json.loads(settings.BACKEND_CORS_ORIGINS)
        logger.info(f"CORS origins loaded from JSON: {origins}")
    except (json.JSONDecodeError, ValueError):
        # If not JSON, split by comma
        origins = [origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]
        logger.info(f"CORS origins loaded from comma-separated string: {origins}")
elif isinstance(settings.BACKEND_CORS_ORIGINS, list):
    origins = settings.BACKEND_CORS_ORIGINS
    logger.info(f"CORS origins loaded from list: {origins}")
else:
    origins = []
    logger.warning("No CORS origins configured, using defaults")

# Ensure localhost origins are always included in development
if os.getenv("ENVIRONMENT") != "production":
    default_origins = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"]
    for origin in default_origins:
        if origin not in origins:
            origins.append(origin)
    logger.info(f"Development mode: Added default origins. Final CORS origins: {origins}")

# Fallback: if no origins configured, allow all in development (not recommended for production)
if not origins and os.getenv("ENVIRONMENT") != "production":
    origins = ["*"]
    logger.warning("No CORS origins found, allowing all origins in development mode")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"CORS middleware configured with origins: {origins}")

# Include routers
app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
app.include_router(meta_campaigns_routes.router, prefix="/api/app", tags=["app"])
app.include_router(ad_account_routes.router, prefix="/api/app/meta-campaigns", tags=["app"])


@app.get("/api/health")
def health_check():
    return {"status": "ok"}

