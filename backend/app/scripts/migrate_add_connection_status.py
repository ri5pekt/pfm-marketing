"""
Script to add connection_status and connection_last_checked columns to business_accounts table.
"""
import sys
from sqlalchemy import text
from app.core.db import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_add_connection_status():
    """Add connection_status and connection_last_checked columns to business_accounts table"""
    logger.info("Adding connection_status and connection_last_checked columns to business_accounts table...")

    with engine.connect() as conn:
        try:
            # Check if connection_status column already exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'business_accounts'
                AND column_name = 'connection_status'
            """))

            row = result.fetchone()
            if row:
                logger.info("Column connection_status already exists. No migration needed.")
                return

            # Add the columns
            logger.info("Adding connection_status column...")
            conn.execute(text("ALTER TABLE business_accounts ADD COLUMN connection_status BOOLEAN"))

            logger.info("Adding connection_last_checked column...")
            conn.execute(text("ALTER TABLE business_accounts ADD COLUMN connection_last_checked TIMESTAMP WITH TIME ZONE"))

            conn.commit()
            logger.info("Migration completed successfully!")

        except Exception as e:
            logger.error(f"Error during migration: {str(e)}", exc_info=True)
            conn.rollback()
            raise

if __name__ == "__main__":
    migrate_add_connection_status()

