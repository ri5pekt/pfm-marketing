"""
Script to delete all rule logs from the database.
"""
import sys
from sqlalchemy import text
from app.core.db import SessionLocal
from app.features.meta_campaigns.models import RuleLog
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delete_all_logs():
    """Delete all rule logs from the database"""
    db = SessionLocal()
    try:
        count = db.query(RuleLog).count()
        logger.info(f"Found {count} log entries to delete")

        if count > 0:
            db.query(RuleLog).delete()
            db.commit()
            logger.info(f"Successfully deleted {count} log entries")
        else:
            logger.info("No logs to delete")
    except Exception as e:
        logger.error(f"Error deleting logs: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    delete_all_logs()

