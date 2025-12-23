# Changelog

All notable changes to this project will be documented in this file.

## [3.0.0] - 2025-01-XX

### Added
- Per-condition time ranges: Each condition can now specify its own time range
- CPP Winning Days field: Count days where CPP was below threshold (excluding days with no purchases)
- Amount of Active Ads field: Count active ads in campaigns/adsets (or parent adset for ad-level rules)
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

### Technical
- Extracted composables: useAdAccounts, useCampaigns, useRules, useRuleForm, useRuleJsonConverter, useRuleSchedule
- Created utility modules: cronHelpers.js, specialValues.js
- Improved separation of concerns
- Better error handling throughout the application

## [2.3.0] - Previous version
- Initial stable release with basic rule functionality

