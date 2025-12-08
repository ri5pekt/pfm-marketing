"""
Script to add slack_webhook_url column to business_accounts table.
"""
import sys
from sqlalchemy import text
from app.core.db import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_add_slack_webhook():
    """Add slack_webhook_url column to business_accounts table"""
    logger.info("Adding slack_webhook_url column to business_accounts table...")

    with engine.connect() as conn:
        try:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'business_accounts'
                AND column_name = 'slack_webhook_url'
            """))

            row = result.fetchone()
            if row:
                logger.info("Column slack_webhook_url already exists. No migration needed.")
                return

            # Add the column
            logger.info("Adding slack_webhook_url column...")
            conn.execute(text("ALTER TABLE business_accounts ADD COLUMN slack_webhook_url VARCHAR"))
            conn.commit()
            logger.info("Migration completed successfully!")

        except Exception as e:
            logger.error(f"Error during migration: {str(e)}", exc_info=True)
            conn.rollback()
            raise

if __name__ == "__main__":
    migrate_add_slack_webhook()

