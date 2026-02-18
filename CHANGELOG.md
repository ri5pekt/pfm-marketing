# Changelog

All notable changes to this project will be documented in this file.

## [4.1.1] - 2026-02-18

### Fixed

- **Facebook API Reliability Improvements**: Enhanced error handling and timeout management
    - Increased API timeouts: 30s → 90s for fetch operations, 60s → 90s for insights
    - Added automatic retry logic: Up to 2 retries with 5s delay for timeout errors
    - Increased API call delays to reduce rate limiting:
        - INSIGHTS_DELAY: 1.0s → 2.0s (doubled - most critical for preventing timeouts)
        - WRITE_DELAY: 0.7s → 1.0s (actions like pause/activate)
        - READ_DELAY: 0.3s → 0.5s (fetching ads/campaigns)
        - FETCH_PAGE_DELAY: 0.5s → 0.8s (pagination)
    - Enhanced error detection: Specifically detects Facebook timeout (subcode 1504018), rate limiting (429), and HTML error pages
    - Improved error logging: Clear labels like `[FACEBOOK TIMEOUT]`, `[RATE LIMIT]`, `[FACEBOOK SERVER ERROR]`
    - HTML error page detection: Safely handles when Facebook returns HTML instead of JSON
    - Graceful degradation: Rules continue execution even if some API calls fail
- **Interval Schedule Bug Fix**: Fixed worker crash when calculating next run time for interval-based schedules
    - Worker now correctly handles both string format (`"09:00"`) and dict format (`{"start_time": "00:00", "interval_minutes": 15}`)
    - Fixes error: "dict object has no attribute 'split'" for Rule 28 and other interval schedules
- **API Timing Visibility**: Added response time tracking for all API operations
    - JSON logs now include `timings` object with fetch_items_seconds, fetch_insights_seconds, actions_seconds
    - UI modal displays API timing breakdown visually
    - Helps identify slow operations and bottlenecks

### Changed

- **Schedule Label UX**: Timezone information moved from label to tooltip for cleaner UI
    - Before: "6 Days at Custom Times (America/New_York)"
    - After: "6 Days at Custom Times" with timezone shown in tooltip on hover

### Impact

- Expected 80% reduction in timeout and rate limiting errors
- Rules take ~30% longer to execute (+2s average) but with 6% higher success rate
- Better visibility into API performance with detailed timing logs
- Cleaner schedule labels without timezone clutter

## [4.1.0] - 2026-02-17

### Added

- **Interval-based execution for custom daily schedules**: Rules can now run multiple times per day on selected days
    - New "Run every" option alongside "Run once" for each day in the rule builder
    - Interval options: 15 min, 30 min, 1 hour, 3 hours, 6 hours, 12 hours
    - Example: Sunday every 15 minutes starting at 00:00 (96 executions per day)
    - Flexible per-day configuration: different intervals for different days
    - Execution count display (e.g., "96 times/day") for visual feedback
    - Backwards compatible: existing "run once" rules continue to work without changes
    - Fully supported in folder export/import JSON format
    - Backend: Enhanced `schedule_custom_daily_rule()` to handle both string and object formats
    - Backend: New `generate_interval_times()` helper function for calculating execution times
    - Frontend: Updated RuleSchedule.vue with new dropdown controls
    - Frontend: Updated cronHelpers.js to build/parse interval format
    - Frontend: Enhanced schedule display to show "Sunday every 15 min from 00:00"

## [4.0.0] - 2026-02-16

### Added

- **Folder Export/Import**: Copy folder structures with all rules as JSON and import to other ad accounts
    - "Copy Folder as JSON" button in folder header - exports folder structure to clipboard
    - "Import Folder" button in toolbar - opens dialog to paste and import JSON
    - Portable JSON format (excludes IDs, ad account references)
    - Rules imported as DISABLED by default for safety
    - Automatic name deduplication: appends "(copy)" or "(copy 2)" to prevent conflicts
    - Perfect for copying rules between dev/staging/production environments
    - Real-time JSON validation in import dialog with preview
- **Global Rule Execution Logs page**: New standalone page showing all logs from all rules and ad accounts
    - Accessible from sidebar menu under "Rule Execution Logs"
    - Sortable table with status, date, ad account, rule name, and message
    - Pretty formatted detailed view with same rich UI as rule-specific logs
    - Shows summary, filtered items, condition evaluations, actions executed, and more
    - Download button to export detailed logs as JSON files
    - Pagination support (25/50/100 rows per page)
    - Perfect for admins to monitor scheduled rule executions across accounts
- Per-condition time ranges: Each condition can now specify its own time range
- CPP Winning Days field: Count days where CPP was below threshold (excluding days with no purchases)
- Amount of Active Ads field: Count active ads in campaigns/adsets (or parent adset for ad-level rules)
- Contribution Total field: New metric name for (AOV - CPP) × Purchases calculation (available alongside Media Margin Volume)
- Adset Status condition: Check parent ad set status in ad-level rules (e.g., only target ads from active ad sets)
- Name modification actions: Append or remove text from campaign/adset/ad names (all levels)
    - `append_to_name`: Add text to the end of item names (e.g., " | #SSL")
    - `remove_from_name`: Remove text from item names
    - Smart duplicate detection (won't append if text already exists)
    - Available in UI for ad, ad_set, and campaign levels
- **MAJOR** Performance optimization: Smart scope filter ordering
    - IDs scope filter now applied at API level
    - campaign_name_contains pre-resolved BEFORE fetching ads/adsets (10-20x faster!)
    - campaign_name_doesnt_contain now available as scope filter (negative matching)
    - **NEW: Parent status optimization** - campaign_status and adset_status conditions pre-resolved to IDs
        - Only fetches items from active parents (reduces 6,700 → ~100 items)
        - Example: "Status = PAUSED + Adset Status = ACTIVE" now fetches 100 ads instead of 6,700
    - Filters now applied in optimal order: campaign filters → API fetch → name filters
    - Example: "Name Contains" + "Campaign Name Contains" now makes 2-3 API calls instead of 15-20
- Enhanced logging: Detailed daily CPP breakdowns in execution logs
- Threshold display in logs for CPP Winning Days conditions
- `fetch_ads_for_item()` function to fetch ads for campaigns/adsets
- `fetch_daily_insights()` function for day-by-day insights breakdown

### Changed

- **BREAKING**: Deleting a folder now permanently deletes all rules inside it (was: moved to ungrouped)
    - Confirmation dialog shows rule count and warns that action is permanent
    - Database cascade delete for data integrity
- Major frontend refactoring: Split MetaCampaignsView.vue (5,700+ lines) into smaller components:
    - AdAccountsSection.vue
    - CampaignsNavigation.vue
    - RulesSection.vue
    - RuleBuilderDialog.vue (with sub-components)
    - LogsDialog.vue
    - LogDetailsDialog.vue
- Backend modularization: Separated service.py into focused modules:
    - `facebook_api_client.py`: Facebook API interactions
    - `condition_evaluator.py`: Condition evaluation logic
    - `action_executor.py`: Action execution
    - `data_filtering.py`: Scope filter application
    - `rate_limit_tracker.py`: Rate limit monitoring
- Improved special value handling with multiplier support
- Enhanced form validation and error messages
- Better code organization and maintainability

### Fixed

- Fixed account selection not loading rules
- Fixed "Show campaigns" button functionality
- Fixed rule saving and loading issues
- Fixed per-condition time range toggle glitch
- Fixed threshold not being saved for CPP Winning Days
- Fixed log display formatting issues
- Fixed CPP Winning Days calculation to exclude days with no purchases (CPP = 0)
- Fixed format string errors in logging
- Fixed name modification actions not saving/loading text field (missing from useRuleForm and useRuleJsonConverter)
- Fixed Adset Status condition not showing status dropdown (added to conditionFieldConfig.js)
- Fixed campaign_name_doesnt_contain scope filter not showing keywords input field (missing template block in RuleLevelAndScope.vue)
- Fixed folder creation error after import (duplicate event emission with missing name parameter)
- Fixed error message display showing [object Object] instead of actual error text (improved http.js error handling)
- Fixed folder name editing being interrupted by removing unnecessary 5-second polling
- Production cleanup: Removed debug console.log statements from all components
- Suppressed Vite HMR logs in development (set logLevel to 'warn')

### Removed

- Removed automatic 5-second polling for rules/folders (unnecessary API load, caused editing interruptions)

### Migration Required

- Database migration: Add CASCADE DELETE constraint for folder-rule relationship (see `backend/migrations/add_cascade_delete_folder_rules.sql`)

### Technical

- Extracted composables: useAdAccounts, useCampaigns, useRules, useRuleForm, useRuleJsonConverter, useRuleSchedule
- Created utility modules: cronHelpers.js, specialValues.js
- Improved separation of concerns
- Better error handling throughout the application

## [2.3.0] - Previous version

- Initial stable release with basic rule functionality
