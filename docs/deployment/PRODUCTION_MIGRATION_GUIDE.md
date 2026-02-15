# Production Migration Guide: BusinessAccount → AdAccount

This guide explains how to safely migrate from "BusinessAccount" to "AdAccount" naming in production while preserving all existing rules and data.

## Overview

This migration renames:
- Database table: `business_accounts` → `ad_accounts`
- Database column: `campaign_rules.business_account_id` → `campaign_rules.ad_account_id`
- All code references and UI labels

**All existing rules and data will be preserved.**

## Pre-Migration Checklist

- [ ] **Backup your database** - This is critical!
- [ ] Test the migration on a staging environment first
- [ ] Schedule a maintenance window (estimated 5-10 minutes)
- [ ] Notify users about the brief downtime
- [ ] Have rollback plan ready (database backup)

## Step-by-Step Migration Process

### Step 1: Backup Database

```bash
# On production server
pg_dump -h localhost -U postgres -d pfm_marketing > backup_before_migration_$(date +%Y%m%d_%H%M%S).sql
```

### Step 2: Stop Services

```bash
# Stop backend, worker, and scheduler to prevent any writes during migration
docker-compose stop backend worker scheduler
# OR if using systemd
systemctl stop pfm-backend pfm-worker pfm-scheduler
```

### Step 3: Run Database Migration

```bash
# SSH into production server
ssh user@your-production-server

# Navigate to project directory
cd /var/www/pfm-marketing

# Run the migration script
docker-compose exec backend python -m app.scripts.migrate_rename_business_to_ad_account

# OR if running directly
cd backend
python -m app.scripts.migrate_rename_business_to_ad_account
```

**Expected Output:**
```
INFO:__main__:Starting migration: business_accounts → ad_accounts
INFO:__main__:Step 1: Renaming business_account_id to ad_account_id in campaign_rules...
INFO:__main__:Step 2: Finding and dropping old foreign key constraint...
INFO:__main__:Step 3: Renaming business_accounts table to ad_accounts...
INFO:__main__:Step 4: Creating new foreign key constraint...
INFO:__main__:Step 5: Renaming index...
INFO:__main__:✅ Migration completed successfully! All data preserved.
```

### Step 4: Deploy Code Changes

```bash
# Pull latest code (which includes all the renamed files)
git pull origin main

# OR if deploying manually, ensure all files are updated:
# - backend/app/features/meta_campaigns/models.py
# - backend/app/features/meta_campaigns/ad_account_*.py (new files)
# - backend/app/main.py
# - frontend/src/api/adAccountsApi.js (new file)
# - frontend/src/views/MetaCampaignsView.vue
```

### Step 5: Restart Services

```bash
# Restart all services
docker-compose restart backend worker scheduler

# OR if using systemd
systemctl restart pfm-backend pfm-worker pfm-scheduler
```

### Step 6: Verify Migration

1. **Check Database:**
   ```sql
   -- Verify table renamed
   SELECT table_name FROM information_schema.tables WHERE table_name = 'ad_accounts';

   -- Verify column renamed
   SELECT column_name FROM information_schema.columns
   WHERE table_name = 'campaign_rules' AND column_name = 'ad_account_id';

   -- Verify data preserved
   SELECT COUNT(*) FROM ad_accounts;
   SELECT COUNT(*) FROM campaign_rules;
   ```

2. **Check Backend:**
   ```bash
   # Check backend logs
   docker-compose logs backend | grep -i "ad account\|error"

   # Test API endpoint
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        http://your-domain/api/app/meta-campaigns/ad-accounts
   ```

3. **Check Frontend:**
   - Log in to the application
   - Verify "Ad Accounts" section appears (not "Business Accounts")
   - Verify all existing accounts are visible
   - Verify all existing rules are visible and functional
   - Test creating/editing an ad account
   - Test creating/editing a rule

## Rollback Plan

If something goes wrong, you can rollback:

### Option 1: Restore Database Backup

```bash
# Stop services
docker-compose stop backend worker scheduler

# Restore database
psql -h localhost -U postgres -d pfm_marketing < backup_before_migration_YYYYMMDD_HHMMSS.sql

# Revert code to previous version
git checkout <previous-commit-hash>

# Restart services
docker-compose restart backend worker scheduler
```

### Option 2: Reverse Migration Script

If you need to reverse the migration, you can create a reverse script that:
1. Renames `ad_accounts` → `business_accounts`
2. Renames `ad_account_id` → `business_account_id`
3. Updates foreign key constraints

## Post-Migration Tasks

- [ ] Verify all rules are working correctly
- [ ] Test rule execution (manual test)
- [ ] Check scheduled rules are still running
- [ ] Monitor logs for any errors
- [ ] Update any external documentation
- [ ] Notify team about the naming change

## Troubleshooting

### Issue: Migration fails with "table does not exist"
**Solution:** The migration may have already been run. Check if `ad_accounts` table exists.

### Issue: Foreign key constraint error
**Solution:** Ensure all services are stopped before running migration. Check for any active connections.

### Issue: Frontend shows errors after migration
**Solution:**
1. Clear browser cache
2. Verify frontend code is updated
3. Check browser console for API errors
4. Verify API endpoints changed from `/business-accounts` to `/ad-accounts`

### Issue: Rules not showing up
**Solution:**
1. Check database: `SELECT * FROM campaign_rules WHERE ad_account_id IS NOT NULL;`
2. Verify foreign key relationship: `SELECT * FROM ad_accounts;`
3. Check backend logs for errors

## API Endpoint Changes

**Old endpoints (will 404 after migration):**
- `GET /api/app/meta-campaigns/business-accounts`
- `POST /api/app/meta-campaigns/business-accounts`
- etc.

**New endpoints:**
- `GET /api/app/meta-campaigns/ad-accounts`
- `POST /api/app/meta-campaigns/ad-accounts`
- etc.

**Query parameter changes:**
- Old: `?business_account_id=1`
- New: `?ad_account_id=1`

## Support

If you encounter issues during migration:
1. Check the migration script logs
2. Review database state
3. Check application logs
4. Restore from backup if needed

## Summary

This migration is **safe** and **reversible**. All data is preserved, and the changes are primarily cosmetic (naming). The functionality remains exactly the same - we're just using more accurate terminology.

**Estimated Downtime:** 5-10 minutes
**Risk Level:** Low (with proper backup)
**Data Loss:** None (all data preserved)

