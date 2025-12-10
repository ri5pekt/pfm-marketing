"""
Script to clean up the old business_accounts table after migration.
This should only be run after confirming that:
1. The migration to ad_accounts is complete
2. All data has been verified
3. The application is working correctly

IMPORTANT: This will DROP the business_accounts table. Make sure you have a backup!
"""
import sys
from sqlalchemy import text
from app.core.db import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_old_business_accounts():
    """Drop the old business_accounts table if ad_accounts exists and has data"""
    logger.info("Checking if cleanup is needed...")

    with engine.connect() as conn:
        try:
            # Check if ad_accounts table exists
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name = 'ad_accounts'
            """))

            if not result.fetchone():
                logger.error("ad_accounts table does not exist. Cannot proceed with cleanup.")
                return

            # Check if business_accounts table exists
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name = 'business_accounts'
            """))

            if not result.fetchone():
                logger.info("business_accounts table does not exist. Nothing to clean up.")
                return

            # Verify ad_accounts has data
            result = conn.execute(text("SELECT COUNT(*) FROM ad_accounts"))
            ad_accounts_count = result.fetchone()[0]

            if ad_accounts_count == 0:
                logger.warning("ad_accounts table is empty. Not safe to drop business_accounts.")
                return

            logger.info(f"Found {ad_accounts_count} records in ad_accounts table.")
            logger.info("Dropping old business_accounts table...")

            conn.execute(text("DROP TABLE IF EXISTS business_accounts CASCADE"))
            conn.commit()

            logger.info("✅ Cleanup completed successfully! Old business_accounts table removed.")

        except Exception as e:
            logger.error(f"❌ Error during cleanup: {str(e)}", exc_info=True)
            conn.rollback()
            raise

if __name__ == "__main__":
    cleanup_old_business_accounts()

