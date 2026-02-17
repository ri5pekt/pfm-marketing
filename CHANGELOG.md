# Changelog

All notable changes to this project will be documented in this file.

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
- Fixed folder name editing being interrupted by polling refresh (skip folder reload when editing)
- Production cleanup: Removed debug console.log statements from all components
- Suppressed Vite HMR logs in development (set logLevel to 'warn')

### Technical
- Extracted composables: useAdAccounts, useCampaigns, useRules, useRuleForm, useRuleJsonConverter, useRuleSchedule
- Created utility modules: cronHelpers.js, specialValues.js
- Improved separation of concerns
- Better error handling throughout the application

## [2.3.0] - Previous version
- Initial stable release with basic rule functionality

