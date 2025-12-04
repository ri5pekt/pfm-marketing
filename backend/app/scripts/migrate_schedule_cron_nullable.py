"""
Script to migrate schedule_cron column to be nullable.
This allows rules to have no schedule (manual-only rules).
"""
import sys
from sqlalchemy import text
from app.core.db import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_schedule_cron():
    """Make schedule_cron column nullable"""
    logger.info("Migrating schedule_cron column to be nullable...")

    with engine.connect() as conn:
        try:
            # Check if column exists and is currently NOT NULL
            result = conn.execute(text("""
                SELECT column_name, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'campaign_rules'
                AND column_name = 'schedule_cron'
            """))

            row = result.fetchone()
            if not row:
                logger.warning("Column schedule_cron not found. Tables may need to be recreated.")
                return

            if row[1] == 'YES':
                logger.info("Column schedule_cron is already nullable. No migration needed.")
                return

            # Make the column nullable
            logger.info("Altering schedule_cron column to be nullable...")
            conn.execute(text("ALTER TABLE campaign_rules ALTER COLUMN schedule_cron DROP NOT NULL"))
            conn.commit()
            logger.info("Migration completed successfully!")

        except Exception as e:
            logger.error(f"Error during migration: {str(e)}", exc_info=True)
            conn.rollback()
            raise

if __name__ == "__main__":
    migrate_schedule_cron()

