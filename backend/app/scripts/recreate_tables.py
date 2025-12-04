"""
Script to recreate database tables with updated schema.
WARNING: This will drop all existing tables and data!
"""
import sys
from sqlalchemy import text
from app.core.db import engine, Base
from app.auth.models import User
from app.features.meta_campaigns.models import BusinessAccount, CampaignRule, RuleLog
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_tables():
    """Drop all tables and recreate them"""
    logger.info("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)

    logger.info("Creating all tables...")
    Base.metadata.create_all(bind=engine)

    logger.info("Tables recreated successfully!")

if __name__ == "__main__":
    recreate_tables()

