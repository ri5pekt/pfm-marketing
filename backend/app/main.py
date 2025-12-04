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
from app.features.meta_campaigns import business_account_routes
import os

# Create database tables (for development)
if os.getenv("ENVIRONMENT") != "production":
    Base.metadata.create_all(bind=engine)
    # Create default business account if it doesn't exist
    try:
        from app.scripts.create_default_business_account import create_default_business_account
        create_default_business_account()
    except Exception as e:
        print(f"Note: Could not create default business account: {e}")

app = FastAPI(title="PFM Marketing API", version="1.0.0")

# CORS configuration
if isinstance(settings.BACKEND_CORS_ORIGINS, str):
    origins = [origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",")]
else:
    origins = settings.BACKEND_CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
app.include_router(meta_campaigns_routes.router, prefix="/api/app", tags=["app"])
app.include_router(business_account_routes.router, prefix="/api/app/meta-campaigns", tags=["app"])


@app.get("/api/health")
def health_check():
    return {"status": "ok"}

