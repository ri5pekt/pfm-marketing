"""
Script to rename business_accounts to ad_accounts while preserving all data.
This migration:
1. Renames the business_accounts table to ad_accounts
2. Renames business_account_id to ad_account_id in campaign_rules
3. Updates foreign key constraints
4. Preserves all existing data and rules

IMPORTANT: Backup your database before running this migration!
"""
import sys
from sqlalchemy import text
from app.core.db import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_rename_business_to_ad_account():
    """Rename business_accounts to ad_accounts"""
    logger.info("Starting migration: business_accounts → ad_accounts")

    with engine.connect() as conn:
        try:
            # Check if column already renamed (this is the real indicator)
            column_result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'campaign_rules'
                AND column_name = 'ad_account_id'
            """))

            if column_result.fetchone():
                logger.info("Column ad_account_id already exists. Migration may have already been run.")
                return

            # Check if business_account_id still exists (needs migration)
            old_column_result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'campaign_rules'
                AND column_name = 'business_account_id'
            """))

            if not old_column_result.fetchone():
                logger.warning("Column business_account_id does not exist. Migration may have already been run or table structure is unexpected.")
                return

            # Check which table exists
            table_result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name IN ('business_accounts', 'ad_accounts')
            """))

            tables = [row[0] for row in table_result.fetchall()]
            has_business_accounts = 'business_accounts' in tables
            has_ad_accounts = 'ad_accounts' in tables

            if has_ad_accounts and not has_business_accounts:
                logger.info("Table already renamed to ad_accounts. Only need to rename column.")
                skip_table_rename = True
            elif has_business_accounts and not has_ad_accounts:
                skip_table_rename = False
            elif has_business_accounts and has_ad_accounts:
                logger.warning("Both business_accounts and ad_accounts tables exist. This is unexpected. Proceeding with column rename only.")
                skip_table_rename = True
            else:
                logger.error("Neither business_accounts nor ad_accounts table found. Cannot proceed.")
                return

            # Step 1: Rename the foreign key column in campaign_rules
            logger.info("Step 1: Renaming business_account_id to ad_account_id in campaign_rules...")
            conn.execute(text("""
                ALTER TABLE campaign_rules
                RENAME COLUMN business_account_id TO ad_account_id
            """))

            # Step 2: Drop the old foreign key constraint (get constraint name first)
            logger.info("Step 2: Finding and dropping old foreign key constraint...")
            constraint_result = conn.execute(text("""
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_name = 'campaign_rules'
                AND constraint_type = 'FOREIGN KEY'
                AND constraint_name LIKE '%business_account%'
            """))

            constraint_row = constraint_result.fetchone()
            if constraint_row:
                constraint_name = constraint_row[0]
                logger.info(f"Dropping constraint: {constraint_name}")
                conn.execute(text(f"""
                    ALTER TABLE campaign_rules
                    DROP CONSTRAINT IF EXISTS {constraint_name}
                """))

            # Step 3: Rename the business_accounts table to ad_accounts (if needed)
            if not skip_table_rename:
                logger.info("Step 3: Renaming business_accounts table to ad_accounts...")
                conn.execute(text("""
                    ALTER TABLE business_accounts
                    RENAME TO ad_accounts
                """))
            else:
                logger.info("Step 3: Table already renamed, skipping...")

            # Step 4: Recreate the foreign key constraint with new name
            logger.info("Step 4: Creating new foreign key constraint...")
            conn.execute(text("""
                ALTER TABLE campaign_rules
                ADD CONSTRAINT campaign_rules_ad_account_id_fkey
                FOREIGN KEY (ad_account_id)
                REFERENCES ad_accounts(id)
            """))

            # Step 5: Rename the index if it exists
            logger.info("Step 5: Renaming index...")
            index_result = conn.execute(text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'campaign_rules'
                AND indexname LIKE '%business_account%'
            """))

            index_row = index_result.fetchone()
            if index_row:
                old_index_name = index_row[0]
                new_index_name = old_index_name.replace('business_account', 'ad_account')
                logger.info(f"Renaming index: {old_index_name} → {new_index_name}")
                conn.execute(text(f"""
                    ALTER INDEX IF EXISTS {old_index_name}
                    RENAME TO {new_index_name}
                """))

            conn.commit()
            logger.info("✅ Migration completed successfully! All data preserved.")
            logger.info("Next steps:")
            logger.info("1. Update backend code (models, services, routes)")
            logger.info("2. Update frontend code (API calls, UI labels)")
            logger.info("3. Restart backend service")

        except Exception as e:
            logger.error(f"❌ Error during migration: {str(e)}", exc_info=True)
            conn.rollback()
            raise

if __name__ == "__main__":
    migrate_rename_business_to_ad_account()

