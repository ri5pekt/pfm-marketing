# Visual Refactoring Guide - Before & After

**Purpose**: Visual representation of how large files will be restructured

---

## 1. RulesSection.vue (981 lines → ~250 lines)

### ❌ BEFORE (Current Structure)
```
┌─────────────────────────────────────────────────────────────┐
│                    RulesSection.vue                         │
│                      (981 lines)                            │
├─────────────────────────────────────────────────────────────┤
│ • Header & toolbar (buttons)                                │
│ • Folders state management                                  │
│ • Rules state management                                    │
│ • Drag & drop logic (folders)                               │
│ • Drag & drop logic (rules)                                 │
│ • VueDraggable setup (unified list)                         │
│ • VueDraggable setup (ungrouped rules)                      │
│ • VueDraggable setup (folder rules)                         │
│ • Folder display template                                   │
│ • Folder actions (edit, delete, collapse)                   │
│ • Rule display template                                     │
│ • Rule actions (test, logs, edit, delete, toggle)           │
│ • Test rule logic                                           │
│ • Delete confirmation logic                                 │
│ • Logs dialog orchestration                                 │
│ • New folder dialog                                         │
│ • Edit folder dialog                                        │
│ • Reordering persistence logic                              │
│ • Schedule formatting                                       │
│ • API calls (folders CRUD)                                  │
│ • API calls (rules CRUD)                                    │
│ • Error handling                                            │
│ • Loading states                                            │
└─────────────────────────────────────────────────────────────┘
```

### ✅ AFTER (Refactored Structure)
```
┌───────────────────────────────────────────────────────────────────────────┐
│                         RulesSection.vue                                  │
│                          (~250 lines)                                     │
│  [Orchestrator - manages child components and high-level state]          │
└────────────┬──────────────────────────────────────────────────────────────┘
             │
             ├─► RulesToolbar.vue (~50 lines)
             │   └─ New Folder & Create Rule buttons
             │
             ├─► RulesFolderList.vue (~180 lines)
             │   ├─ VueDraggable for folders
             │   └─► RulesFolderItem.vue (~140 lines)
             │       ├─ Single folder display
             │       ├─ Folder drag handle
             │       ├─ Folder actions (edit, delete, collapse)
             │       └─► RuleListItem.vue (~90 lines)
             │           ├─ Single rule display
             │           ├─ Rule metadata
             │           └─ Rule action buttons
             │
             ├─► RulesUngroupedSection.vue (~110 lines)
             │   ├─ VueDraggable for ungrouped rules
             │   └─► RuleListItem.vue (shared)
             │
             ├─► NewFolderDialog.vue (~70 lines)
             ├─► EditFolderDialog.vue (~70 lines)
             └─► DeleteRuleConfirmDialog.vue (~50 lines)

┌───────────────────────────────────────────────────────────────────────────┐
│                          Composables                                      │
├───────────────────────────────────────────────────────────────────────────┤
│ • useFolderManagement.js (~110 lines) - Folder CRUD & reordering         │
│ • useRuleDragDrop.js (~90 lines) - Drag & drop state                     │
│ • useRuleActions.js (~70 lines) - Rule operations                        │
└───────────────────────────────────────────────────────────────────────────┘
```

**Benefits**:
- Single component → 10 focused components
- Reusable `RuleListItem` shared between folders and ungrouped
- Drag & drop logic isolated in composable
- Easier to test individual parts
- Better performance (smaller re-renders)

---

## 2. ConditionItem.vue (691 lines → ~180 lines)

### ❌ BEFORE (Current Structure)
```
┌─────────────────────────────────────────────────────────────┐
│                   ConditionItem.vue                         │
│                     (691 lines)                             │
├─────────────────────────────────────────────────────────────┤
│ • Field selector dropdown                                   │
│ • Field type detection (status, numeric, string, etc.)      │
│ • Operator selector (changes based on field)                │
│ • Operator options computation (10+ field types)            │
│ • Value input - status dropdown                             │
│ • Value input - numeric input                               │
│ • Value input - special value (with multiplier)             │
│ • Value input - text input                                  │
│ • Special value menu                                        │
│ • Special value parsing (__token__ * multiplier)            │
│ • Special value validation                                  │
│ • Lookahead period configuration                            │
│ • Field descriptions (tooltips)                             │
│ • Conditional rendering logic (huge template)               │
│ • Value updates and validation                              │
│ • Error handling                                            │
└─────────────────────────────────────────────────────────────┘
```

### ✅ AFTER (Refactored Structure)
```
┌───────────────────────────────────────────────────────────────────────────┐
│                         ConditionItem.vue                                 │
│                          (~180 lines)                                     │
│  [Orchestrator - coordinates field, operator, and value]                 │
└────────────┬──────────────────────────────────────────────────────────────┘
             │
             ├─► ConditionFieldSelector.vue (~60 lines)
             │   ├─ Field dropdown
             │   └─ Field descriptions/tooltips
             │
             ├─► ConditionOperatorSelector.vue (~60 lines)
             │   └─ Operator dropdown (dynamic options)
             │
             └─► ConditionValueInput.vue (~90 lines)
                 └─ Router component → delegates to:
                     │
                     ├─► StatusValueInput.vue (~50 lines)
                     │   └─ ACTIVE/PAUSED/... dropdown
                     │
                     ├─► NumericValueInput.vue (~70 lines)
                     │   └─ Number input with validation
                     │
                     ├─► SpecialValueInput.vue (~110 lines)
                     │   ├─ Special value dropdown
                     │   ├─ Token input (__daily_budget__)
                     │   └─ Multiplier input (× 1.5)
                     │
                     └─► TextValueInput.vue (~40 lines)
                         └─ Simple text input

┌───────────────────────────────────────────────────────────────────────────┐
│                          Composables                                      │
├───────────────────────────────────────────────────────────────────────────┤
│ • useConditionFieldTypes.js (~90 lines) - Field definitions              │
│ • useConditionOperators.js (~90 lines) - Operator logic                  │
│ • useConditionValueType.js (~70 lines) - Determine input component       │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                           Utils                                           │
├───────────────────────────────────────────────────────────────────────────┤
│ • conditionFieldConfig.js (~110 lines) - Field metadata & operator sets  │
└───────────────────────────────────────────────────────────────────────────┘
```

**Benefits**:
- Each input type isolated and testable
- Easy to add new field types (just add new value input component)
- Operator logic centralized in composable
- Template complexity reduced by 70%
- Clear separation: field → operator → value

---

## 3. facebook_api_client.py (648 lines → ~150 lines base)

### ❌ BEFORE (Current Structure)
```
┌─────────────────────────────────────────────────────────────┐
│              facebook_api_client.py                         │
│                    (648 lines)                              │
├─────────────────────────────────────────────────────────────┤
│ • Helper: _safe_float_any()                                 │
│ • Helper: _pick_canonical_purchase_action_value()           │
│ • fetch_facebook_data() - main data fetcher                 │
│   ├─ Determine endpoint (campaigns/adsets/ads)              │
│   ├─ Build field list                                       │
│   ├─ Apply scope filters                                    │
│   ├─ Build filtering param                                  │
│   ├─ Make API request                                       │
│   ├─ Handle pagination (while loop)                         │
│   ├─ Extract next page URL                                  │
│   ├─ Merge results                                          │
│   └─ Error handling                                         │
│ • fetch_insights() - fetch insights for date range          │
│   ├─ Build insights fields                                  │
│   ├─ Build time range string                                │
│   ├─ Make API request                                       │
│   ├─ Parse response                                         │
│   └─ Rate limit handling                                    │
│ • fetch_daily_insights() - daily breakdown                  │
│   ├─ Similar to fetch_insights                              │
│   └─ Daily iteration logic                                  │
│ • fetch_ads_for_item() - fetch ads for campaign/adset       │
│ • build_time_range_string() - time range formatting         │
│ • Pagination logic repeated in multiple functions           │
│ • Rate limiting delays (READ_DELAY, INSIGHTS_DELAY)         │
│ • Error handling duplicated                                 │
└─────────────────────────────────────────────────────────────┘
```

### ✅ AFTER (Refactored Structure)
```
┌───────────────────────────────────────────────────────────────────────────┐
│                    facebook_api/ (package)                                │
└────────────┬──────────────────────────────────────────────────────────────┘
             │
             ├─► __init__.py
             │   └─ Re-export main functions
             │
             ├─► base_client.py (~110 lines)
             │   ├─ FacebookAPIClient class
             │   ├─ Base URL & authentication
             │   ├─ request() - with rate limiting
             │   ├─ Error handling & retries
             │   └─ Response parsing
             │
             ├─► data_fetcher.py (~160 lines)
             │   ├─ fetch_facebook_data() - entry point
             │   ├─ fetch_campaigns()
             │   ├─ fetch_adsets()
             │   ├─ fetch_ads()
             │   ├─ build_fields_list()
             │   └─ build_filtering_param()
             │
             ├─► insights_fetcher.py (~160 lines)
             │   ├─ fetch_insights() - single date range
             │   ├─ fetch_daily_insights() - daily breakdown
             │   ├─ build_insights_fields()
             │   ├─ parse_insights_response()
             │   └─ aggregate_daily_insights()
             │
             ├─► pagination_handler.py (~90 lines)
             │   ├─ paginate_api_call() - generic paginator
             │   ├─ extract_next_page_url()
             │   ├─ has_more_pages()
             │   └─ merge_paginated_results()
             │
             ├─► helpers.py (~90 lines)
             │   ├─ _safe_float_any()
             │   ├─ _pick_canonical_purchase_action_value()
             │   ├─ build_time_range_string()
             │   ├─ ensure_act_prefix()
             │   └─ parse_action_value()
             │
             └─► constants.py (~50 lines)
                 ├─ API_VERSION = "v21.0"
                 ├─ BASE_URL
                 ├─ READ_DELAY, WRITE_DELAY, INSIGHTS_DELAY
                 ├─ DEFAULT_LIMITS
                 └─ FIELD_DEFINITIONS

Usage Example:
  from facebook_api import fetch_facebook_data, fetch_insights
  from facebook_api.base_client import FacebookAPIClient

  client = FacebookAPIClient(access_token)
  data = client.fetch_campaigns(account_id, limit=100)
```

**Benefits**:
- Single 648-line file → 6 focused modules (~660 lines total)
- Base client can be mocked for testing
- Pagination logic centralized (DRY principle)
- Easy to add new endpoints without touching existing code
- Rate limiting centralized in base client
- Constants clearly separated

---

## 4. service.py (636 lines → ~150 lines orchestrator)

### ❌ BEFORE (Current Structure)
```
┌─────────────────────────────────────────────────────────────┐
│                     service.py                              │
│                    (636 lines)                              │
├─────────────────────────────────────────────────────────────┤
│ • get_folders_by_ad_account()                               │
│ • create_folder()                                           │
│ • update_folder()                                           │
│ • delete_folder()                                           │
│ • reorder_folders()                                         │
│ • get_rules_by_ad_account()                                 │
│ • get_rule_by_id()                                          │
│ • create_rule()                                             │
│ • update_rule()                                             │
│ • delete_rule()                                             │
│ • reorder_rules()                                           │
│ • execute_rule() - main execution logic                     │
│   ├─ Fetch rule from DB                                     │
│   ├─ Parse conditions JSON                                  │
│   ├─ Fetch Facebook data                                    │
│   ├─ Apply scope filters                                    │
│   ├─ Fetch insights for each item                           │
│   ├─ Evaluate conditions                                    │
│   ├─ Execute actions on matched items                       │
│   ├─ Log execution results                                  │
│   └─ Error handling                                         │
│ • test_rule_execution() - dry run                           │
│ • get_rule_execution_logs()                                 │
│ • get_rule_execution_log_details()                          │
│ • format_log_details()                                      │
│ • Mixed DB access & business logic                          │
│ • Direct Facebook API calls                                 │
└─────────────────────────────────────────────────────────────┘
```

### ✅ AFTER (Refactored Structure)
```
┌───────────────────────────────────────────────────────────────────────────┐
│                    services/ (package)                                    │
└────────────┬──────────────────────────────────────────────────────────────┘
             │
             ├─► __init__.py
             │   └─ Re-export main service functions
             │
             ├─► folder_service.py (~130 lines)
             │   ├─ get_folders_by_ad_account()
             │   ├─ create_folder()
             │   ├─ update_folder()
             │   ├─ delete_folder()
             │   ├─ reorder_folders()
             │   └─ Folder CRUD only
             │
             ├─► rule_service.py (~160 lines)
             │   ├─ get_rules_by_ad_account()
             │   ├─ get_rule_by_id()
             │   ├─ create_rule()
             │   ├─ update_rule()
             │   ├─ delete_rule()
             │   ├─ reorder_rules()
             │   ├─ toggle_rule_enabled()
             │   └─ Rule CRUD only
             │
             ├─► rule_execution_service.py (~200 lines)
             │   ├─ execute_rule() - main entry point
             │   ├─ _fetch_rule_data()
             │   ├─ _apply_filters()
             │   ├─ _evaluate_items()
             │   ├─ _execute_actions_on_items()
             │   └─ Core execution logic
             │
             ├─► rule_testing_service.py (~110 lines)
             │   ├─ test_rule_execution() - dry run
             │   ├─ _simulate_rule_execution()
             │   ├─ _generate_test_report()
             │   └─ Testing/dry-run logic
             │
             └─► rule_logging_service.py (~90 lines)
                 ├─ log_rule_execution()
                 ├─ get_rule_execution_logs()
                 ├─ get_log_details()
                 ├─ format_log_entry()
                 └─ Logging operations

Usage Example:
  from services import folder_service, rule_service, rule_execution_service

  # Folder operations
  folders = folder_service.get_folders_by_ad_account(db, account_id)
  
  # Rule operations
  rule = rule_service.get_rule_by_id(db, rule_id)
  
  # Execute rule
  result = rule_execution_service.execute_rule(db, rule_id)
```

**Benefits**:
- Single 636-line file → 5 focused services (~690 lines total)
- Each service has single responsibility (SRP)
- Easier to test each service independently
- Reduced coupling between components
- Clear API boundaries
- Services can be independently mocked

---

## 5. cronHelpers.js (403 lines → ~130 lines base)

### ❌ BEFORE (Current Structure)
```
┌─────────────────────────────────────────────────────────────┐
│                  cronHelpers.js                             │
│                    (403 lines)                              │
├─────────────────────────────────────────────────────────────┤
│ • periodOptions array                                       │
│ • dayOfWeekOptions array                                    │
│ • weekDays array                                            │
│ • timezoneOptions array                                     │
│ • buildCronExpression() - build from form                   │
│   ├─ Handle "none" period                                   │
│   ├─ Handle "minute" period                                 │
│   ├─ Handle "hourly" period                                 │
│   ├─ Handle "daily" period                                  │
│   ├─ Handle "daily_custom" period (JSON)                    │
│   ├─ Handle "weekly" period                                 │
│   ├─ Handle "monthly" period                                │
│   └─ Build cron string                                      │
│ • parseCronExpression() - parse to form                     │
│   ├─ Detect if JSON (custom daily)                          │
│   ├─ Parse JSON custom schedule                             │
│   ├─ Parse standard cron                                    │
│   ├─ Detect period type                                     │
│   ├─ Extract frequency                                      │
│   ├─ Extract day of week                                    │
│   ├─ Extract day of month                                   │
│   └─ Extract time                                           │
│ • formatScheduleDisplay() - human readable                  │
│   ├─ Format "Every X minutes"                               │
│   ├─ Format "Every X hours"                                 │
│   ├─ Format "Daily at HH:MM"                                │
│   ├─ Format "Weekly on Monday at HH:MM"                     │
│   ├─ Format "Monthly on day X at HH:MM"                     │
│   └─ Format custom daily schedule                           │
│ • Validation logic mixed in                                 │
│ • Complex regex patterns                                    │
└─────────────────────────────────────────────────────────────┘
```

### ✅ AFTER (Refactored Structure)
```
┌───────────────────────────────────────────────────────────────────────────┐
│                    utils/cron/ (package)                                  │
└────────────┬──────────────────────────────────────────────────────────────┘
             │
             ├─► index.js
             │   └─ Re-export main functions
             │
             ├─► cronConstants.js (~50 lines)
             │   ├─ periodOptions
             │   ├─ dayOfWeekOptions
             │   ├─ weekDays
             │   ├─ timezoneOptions
             │   ├─ CRON_PATTERNS (regex)
             │   └─ DEFAULT_VALUES
             │
             ├─► cronBuilder.js (~160 lines)
             │   ├─ buildCronExpression() - main entry
             │   ├─ buildStandardCron()
             │   ├─ buildCustomDailyCron()
             │   ├─ buildMinuteCron()
             │   ├─ buildHourlyCron()
             │   ├─ buildDailyCron()
             │   ├─ buildWeeklyCron()
             │   └─ buildMonthlyCron()
             │
             ├─► cronParser.js (~160 lines)
             │   ├─ parseCronExpression() - main entry
             │   ├─ parseStandardCron()
             │   ├─ parseCustomDailyCron()
             │   ├─ detectPeriodType()
             │   ├─ extractFrequency()
             │   ├─ extractDayOfWeek()
             │   ├─ extractDayOfMonth()
             │   └─ extractTime()
             │
             ├─► cronFormatter.js (~90 lines)
             │   ├─ formatScheduleDisplay() - main entry
             │   ├─ formatMinuteSchedule()
             │   ├─ formatHourlySchedule()
             │   ├─ formatDailySchedule()
             │   ├─ formatWeeklySchedule()
             │   ├─ formatMonthlySchedule()
             │   └─ formatCustomDailySchedule()
             │
             └─► cronValidator.js (~70 lines)
                 ├─ validateCronExpression()
                 ├─ validateCustomSchedule()
                 ├─ validateTime()
                 ├─ validateFrequency()
                 └─ validateDayOfMonth()

Usage Example:
  import { buildCronExpression, parseCronExpression, formatScheduleDisplay } from '@/utils/cron';
  
  const cron = buildCronExpression(ruleForm);
  const parsed = parseCronExpression(cron);
  const display = formatScheduleDisplay(cron);
```

**Benefits**:
- Single 403-line file → 5 focused modules (~530 lines total)
- Clear separation: constants, build, parse, format, validate
- Each function isolated and testable
- Easy to add new period types
- Constants clearly separated
- Easier to maintain regex patterns

---

## Summary: Refactoring Impact

| File | Before | After (Main) | After (Total) | Components Created | Effort |
|------|--------|-------------|---------------|-------------------|---------|
| `RulesSection.vue` | 981 lines | 250 lines | ~900 lines | 10 components | High |
| `ConditionItem.vue` | 691 lines | 180 lines | ~680 lines | 11 components | High |
| `facebook_api_client.py` | 648 lines | 110 lines | ~660 lines | 6 modules | Medium |
| `service.py` | 636 lines | 0 lines | ~690 lines | 5 services | High |
| `cronHelpers.js` | 403 lines | 50 lines | ~530 lines | 5 modules | Low |
| **Total** | **3,359 lines** | **590 lines** | **~3,460 lines** | **37 files** | **4-6 weeks** |

### Key Insights

1. **Total line count increases slightly** (~3% more)
   - This is GOOD - we're adding structure, not removing code
   - More files = better organization
   - Slightly more imports/exports = clearer dependencies

2. **Main files reduce by 82%** (3,359 → 590 lines)
   - Dramatically easier to understand
   - Faster to navigate
   - Easier to find bugs

3. **37 new focused files created**
   - Each with single responsibility
   - Highly testable
   - Reusable components

4. **Better architecture patterns**
   - Component composition (frontend)
   - Service layer pattern (backend)
   - Facade pattern (API client)
   - Strategy pattern (condition evaluation)

---

## Refactoring Principles Applied

### 1. Single Responsibility Principle (SRP)
Each module/component has ONE reason to change.

**Example**: `folder_service.py` only changes if folder operations change, not if rule execution logic changes.

### 2. Don't Repeat Yourself (DRY)
Extract common logic into reusable functions/components.

**Example**: `RuleListItem.vue` used in both folders and ungrouped sections.

### 3. Composition Over Inheritance
Build complex components from simple, focused components.

**Example**: `ConditionItem` composed of `FieldSelector` + `OperatorSelector` + `ValueInput`.

### 4. Separation of Concerns
Separate data, logic, and presentation.

**Example**: Composables (logic) separated from components (presentation).

### 5. Open/Closed Principle
Open for extension, closed for modification.

**Example**: Adding new field type = create new `ValueInput` component, don't modify existing code.

---

**End of Visual Guide**

*Use this document alongside the detailed refactoring plan for implementation.*
