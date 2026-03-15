"""
Script to create rule_folders table and add folder_id column to campaign_rules.
"""
from sqlalchemy import text
from app.core.db import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_add_folders():
    """Create rule_folders table and add folder_id to campaign_rules"""

    with engine.connect() as conn:
        try:
            # --- rule_folders table ---
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'rule_folders'
            """))
            if result.fetchone():
                logger.info("Table rule_folders already exists, skipping creation.")
            else:
                logger.info("Creating rule_folders table...")
                conn.execute(text("""
                    CREATE TABLE rule_folders (
                        id SERIAL PRIMARY KEY,
                        ad_account_id INTEGER NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
                        name VARCHAR NOT NULL,
                        position INTEGER DEFAULT 0,
                        created_at TIMESTAMPTZ DEFAULT now(),
                        updated_at TIMESTAMPTZ
                    )
                """))
                conn.execute(text("CREATE INDEX ix_rule_folders_ad_account_id ON rule_folders(ad_account_id)"))
                logger.info("Table rule_folders created.")

            # --- folder_id column on campaign_rules ---
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'campaign_rules' AND column_name = 'folder_id'
            """))
            if result.fetchone():
                logger.info("Column folder_id already exists on campaign_rules, skipping.")
            else:
                logger.info("Adding folder_id column to campaign_rules...")
                conn.execute(text("""
                    ALTER TABLE campaign_rules
                    ADD COLUMN folder_id INTEGER REFERENCES rule_folders(id) ON DELETE SET NULL
                """))
                conn.execute(text("CREATE INDEX ix_campaign_rules_folder_id ON campaign_rules(folder_id)"))
                logger.info("Column folder_id added.")

            # --- position column on campaign_rules ---
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'campaign_rules' AND column_name = 'position'
            """))
            if result.fetchone():
                logger.info("Column position already exists on campaign_rules, skipping.")
            else:
                logger.info("Adding position column to campaign_rules...")
                conn.execute(text("ALTER TABLE campaign_rules ADD COLUMN position INTEGER DEFAULT 0"))
                logger.info("Column position added.")

            conn.commit()
            logger.info("Migration completed successfully!")

        except Exception as e:
            logger.error(f"Error during migration: {str(e)}", exc_info=True)
            conn.rollback()
            raise


if __name__ == "__main__":
    migrate_add_folders()
