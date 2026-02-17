-- Migration: Add CASCADE DELETE for folder rules
-- Version: 4.0.1
-- Date: 2026-02-17

-- Drop existing foreign key constraint
ALTER TABLE campaign_rules
DROP CONSTRAINT IF EXISTS campaign_rules_folder_id_fkey;

-- Re-add with CASCADE DELETE
ALTER TABLE campaign_rules
ADD CONSTRAINT campaign_rules_folder_id_fkey
FOREIGN KEY (folder_id)
REFERENCES rule_folders(id)
ON DELETE CASCADE;
