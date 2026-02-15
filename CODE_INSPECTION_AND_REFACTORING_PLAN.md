# Code Inspection & Refactoring Plan

**Date**: February 15, 2026  
**Project**: PFM Marketing - Meta Campaigns Automation Platform  
**Status**: Planning Phase - No Changes Made Yet

---

## Executive Summary

This document provides a comprehensive analysis of large files in the codebase and proposes specific refactoring strategies. The codebase is a full-stack application (Vue.js + FastAPI) with some prior refactoring work already completed on the frontend.

### Key Findings
- **15 frontend files** over 200 lines (largest: 981 lines)
- **10 backend files** over 200 lines (largest: 648 lines)
- Prior refactoring documentation exists but is incomplete
- Several files have clear separation points for extraction

---

## 1. Frontend - Large Files Analysis

### 🔴 CRITICAL PRIORITY (800+ lines)

#### 1.1 `frontend/src/components/meta-campaigns/RulesSection.vue` (981 lines)
**Current State**: Monolithic component handling rules display, folders, drag-and-drop, and multiple dialogs.

**Issues**:
- Mixed concerns: display logic, drag-and-drop, folder management, dialog orchestration
- Complex nested template structure with multiple VueDraggable instances
- Extensive state management for folders, rules, and UI interactions
- Multiple dialog components embedded

**Refactoring Strategy**:
```
RulesSection.vue (current: 981 lines → target: 200-250 lines)
│
├── components/
│   ├── RulesToolbar.vue (40-60 lines)
│   │   └── Header with "New Folder" and "Create Rule" buttons
│   │
│   ├── RulesFolderList.vue (150-200 lines)
│   │   ├── Handles VueDraggable for folders
│   │   ├── Emits folder operations (reorder, delete, edit)
│   │   └── Uses RulesFolderItem component
│   │
│   ├── RulesFolderItem.vue (120-150 lines)
│   │   ├── Individual folder with drag handle
│   │   ├── Nested rules list with VueDraggable
│   │   └── Folder-level actions (edit, delete, collapse)
│   │
│   ├── RulesUngroupedSection.vue (100-120 lines)
│   │   ├── Ungrouped rules container
│   │   ├── VueDraggable for ungrouped rules
│   │   └── Uses RuleListItem component
│   │
│   ├── RuleListItem.vue (80-100 lines)
│   │   ├── Single rule display
│   │   ├── Rule metadata (status, schedule)
│   │   └── Action buttons (test, logs, edit, delete)
│   │
│   └── dialogs/
│       ├── NewFolderDialog.vue (60-80 lines)
│       ├── EditFolderDialog.vue (60-80 lines)
│       └── DeleteRuleConfirmDialog.vue (40-60 lines)
│
└── composables/
    ├── useFolderManagement.js (100-120 lines)
    │   └── Folder CRUD, reordering logic
    │
    ├── useRuleDragDrop.js (80-100 lines)
    │   └── Drag-and-drop state and handlers
    │
    └── useRuleActions.js (60-80 lines)
        └── Rule operations (test, delete, toggle)
```

**Benefits**:
- Each component has single responsibility
- Easier testing of individual drag-and-drop logic
- Reusable RuleListItem for folders and ungrouped
- Better performance (smaller component re-renders)

---

#### 1.2 `frontend/src/components/meta-campaigns/rule-builder/ConditionItem.vue` (691 lines)
**Current State**: Massive component for a single condition with complex field type handling.

**Issues**:
- Single component handles 10+ different field types (status, spend, cpp, purchase_count, etc.)
- Complex conditional rendering for different operators
- Special value handling (multipliers, tokens) deeply nested
- Operator options computed differently per field type
- 400+ lines of template alone

**Refactoring Strategy**:
```
ConditionItem.vue (current: 691 lines → target: 150-200 lines)
│
├── components/
│   ├── ConditionFieldSelector.vue (50-70 lines)
│   │   └── Field selection dropdown with descriptions
│   │
│   ├── ConditionOperatorSelector.vue (50-70 lines)
│   │   └── Operator dropdown (dynamic based on field type)
│   │
│   ├── ConditionValueInput.vue (80-100 lines)
│   │   ├── Router component for value input types
│   │   └── Delegates to specific value input components
│   │
│   └── value-inputs/
│       ├── StatusValueInput.vue (40-60 lines)
│       │   └── Status dropdown (ACTIVE, PAUSED, etc.)
│       │
│       ├── NumericValueInput.vue (60-80 lines)
│       │   └── Number input with validation
│       │
│       ├── SpecialValueInput.vue (100-120 lines)
│       │   ├── Special value dropdown
│       │   ├── Base token input (__daily_budget__)
│       │   └── Multiplier input (× 1.5)
│       │
│       └── TextValueInput.vue (40-50 lines)
│           └── Simple text input
│
├── composables/
│   ├── useConditionFieldTypes.js (80-100 lines)
│   │   ├── Field definitions (label, type, description)
│   │   └── Available fields by rule level
│   │
│   ├── useConditionOperators.js (80-100 lines)
│   │   ├── Operator definitions per field type
│   │   └── Operator compatibility logic
│   │
│   └── useConditionValueType.js (60-80 lines)
│       └── Determine value input component for field+operator
│
└── utils/
    └── conditionFieldConfig.js (100-120 lines)
        ├── Field metadata (numeric, status, special value eligible)
        └── Operator sets (comparison, equality, range)
```

**Benefits**:
- Each value input type isolated and testable
- Easier to add new field types
- Reduced cognitive load per component
- Cleaner template structure

---

### 🟡 HIGH PRIORITY (500-800 lines)

#### 1.3 `frontend/src/components/meta-campaigns/dialogs/LogDetailsDialog.vue` (572 lines)
**Current State**: Dialog showing detailed rule execution logs with condition breakdown.

**Refactoring Strategy**:
```
LogDetailsDialog.vue (current: 572 lines → target: 120-150 lines)
│
├── components/
│   ├── LogSummaryHeader.vue (60-80 lines)
│   │   ├── Rule name, execution time, status badge
│   │   └── Overall success/failure summary
│   │
│   ├── LogConditionsList.vue (100-120 lines)
│   │   ├── List of conditions with pass/fail status
│   │   └── Uses LogConditionItem component
│   │
│   ├── LogConditionItem.vue (80-100 lines)
│   │   ├── Single condition display
│   │   ├── Expected vs actual values
│   │   └── Pass/fail badge with explanation
│   │
│   ├── LogActionsList.vue (80-100 lines)
│   │   ├── Actions executed during rule run
│   │   └── Uses LogActionItem component
│   │
│   ├── LogActionItem.vue (60-80 lines)
│   │   ├── Single action result
│   │   ├── Success/failure status
│   │   └── Error messages if any
│   │
│   └── LogAffectedItemsList.vue (80-100 lines)
│       ├── Items affected by rule execution
│       └── Item names, IDs, status changes
│
└── composables/
    └── useLogDetailsFormatting.js (60-80 lines)
        ├── Format condition values
        ├── Format timestamps
        └── Format action results
```

**Benefits**:
- Reusable condition/action display components
- Easier to extend with new log detail types
- Better performance with virtual scrolling potential

---

#### 1.4 `frontend/src/views/RuleEditorView.vue` (518 lines)
**Current State**: Full-page rule editor with multiple sections.

**Refactoring Strategy**:
```
RuleEditorView.vue (current: 518 lines → target: 150-200 lines)
│
├── components/
│   ├── RuleEditorForm.vue (80-100 lines)
│   │   └── Main form orchestrator
│   │
│   ├── RuleLevelAndScope.vue (already exists - 423 lines, needs refactoring)
│   │   └── See section 1.5 below
│   │
│   ├── RuleConditions.vue (already split into multiple components)
│   ├── RuleActions.vue (already exists - 356 lines, needs refactoring)
│   ├── RuleSchedule.vue (already exists - 320 lines, needs refactoring)
│   │
│   └── RuleEditorToolbar.vue (60-80 lines)
│       ├── Save, Cancel, Delete buttons
│       └── JSON editor toggle
│
└── composables/
    ├── useRuleForm.js (already exists - 224 lines)
    ├── useRuleValidation.js (80-100 lines)
    │   └── Form validation logic
    └── useRuleJsonConverter.js (already exists - 396 lines, needs review)
```

**Benefits**:
- Clear separation between view and form logic
- Easier navigation and maintenance

---

#### 1.5 `frontend/src/components/meta-campaigns/rule-builder/RuleLevelAndScope.vue` (423 lines)
**Current State**: Rule level selection and scope filters (campaign IDs, name contains, etc.).

**Refactoring Strategy**:
```
RuleLevelAndScope.vue (current: 423 lines → target: 120-150 lines)
│
├── components/
│   ├── RuleLevelSelector.vue (60-80 lines)
│   │   ├── Campaign / Ad Set / Ad radio buttons
│   │   └── Description of what each level means
│   │
│   ├── ScopeFiltersList.vue (100-120 lines)
│   │   ├── List of scope filters
│   │   └── Add/remove filter buttons
│   │
│   └── ScopeFilterItem.vue (120-150 lines)
│       ├── Single scope filter (type + value)
│       ├── Filter type selector (name_contains, ids, campaign_ids)
│       └── Value input (chips, textarea, or text input)
│
└── composables/
    └── useScopeFilters.js (80-100 lines)
        ├── Add/remove filter logic
        ├── Filter validation
        └── Available filter types per rule level
```

---

### 🟢 MEDIUM PRIORITY (300-500 lines)

#### 1.6 `frontend/src/utils/cronHelpers.js` (403 lines)
**Current State**: Utility functions for cron expression building and parsing.

**Refactoring Strategy**:
```
utils/cron/
├── cronBuilder.js (150-180 lines)
│   ├── buildCronExpression()
│   ├── buildStandardCron()
│   └── buildCustomDailyCron()
│
├── cronParser.js (150-180 lines)
│   ├── parseCronExpression()
│   ├── parseStandardCron()
│   └── parseCustomDailyCron()
│
├── cronFormatter.js (80-100 lines)
│   ├── formatScheduleDisplay()
│   └── formatTimeDisplay()
│
├── cronValidation.js (60-80 lines)
│   ├── validateCronExpression()
│   └── validateCustomSchedule()
│
└── cronConstants.js (40-60 lines)
    ├── periodOptions
    ├── dayOfWeekOptions
    ├── timezoneOptions
    └── cronRegex patterns
```

**Benefits**:
- Clear separation: build vs parse vs format vs validate
- Easier unit testing
- More maintainable

---

#### 1.7 `frontend/src/composables/useRuleJsonConverter.js` (396 lines)
**Current State**: Converts between rule form and JSON representation.

**Refactoring Strategy**:
```
composables/ruleJson/
├── useRuleJsonConverter.js (80-100 lines)
│   └── Main orchestrator composable
│
├── ruleJsonBuilder.js (120-150 lines)
│   ├── ruleFormToJSON()
│   ├── buildScopeObject()
│   ├── buildConditionsJSON()
│   └── buildActionsJSON()
│
├── ruleJsonParser.js (120-150 lines)
│   ├── jsonToRuleForm()
│   ├── parseScopeFilters()
│   ├── parseConditions()
│   └── parseActions()
│
└── ruleJsonValidator.js (60-80 lines)
    └── validateRuleJSON()
```

---

#### 1.8 `frontend/src/components/meta-campaigns/rule-builder/RuleActions.vue` (356 lines)
**Refactoring Strategy**: Split into action type components similar to ConditionItem approach.

---

#### 1.9 `frontend/src/components/meta-campaigns/rule-builder/RuleSchedule.vue` (320 lines)
**Refactoring Strategy**: Extract schedule type components (daily, weekly, monthly, custom daily).

---

#### 1.10 `frontend/src/views/MetaCampaignsView.vue` (428 lines)
**Current State**: According to refactoring docs, this was 5,726 lines but has been reduced.

**Status Check Needed**: Verify current state and if more refactoring is needed.

---

## 2. Backend - Large Files Analysis

### 🔴 CRITICAL PRIORITY (600+ lines)

#### 2.1 `backend/app/features/meta_campaigns/facebook_api_client.py` (648 lines)
**Current State**: Monolithic API client with multiple Facebook API operations.

**Issues**:
- Mixed concerns: data fetching, insights, pagination, rate limiting
- Multiple endpoint types (campaigns, adsets, ads, insights)
- Complex pagination logic repeated across functions
- Helper functions mixed with API functions

**Refactoring Strategy**:
```
meta_campaigns/facebook_api/
├── __init__.py
│
├── base_client.py (100-120 lines)
│   ├── FacebookAPIClient class
│   ├── Base URL, authentication
│   ├── Request wrapper with rate limiting
│   └── Error handling
│
├── data_fetcher.py (150-180 lines)
│   ├── fetch_facebook_data() - main entry point
│   ├── fetch_campaigns()
│   ├── fetch_adsets()
│   └── fetch_ads()
│
├── insights_fetcher.py (150-180 lines)
│   ├── fetch_insights() - single date range
│   ├── fetch_daily_insights() - daily breakdown
│   ├── build_insights_fields()
│   └── parse_insights_response()
│
├── pagination_handler.py (80-100 lines)
│   ├── paginate_api_call()
│   ├── extract_next_page_url()
│   └── merge_paginated_results()
│
├── helpers.py (80-100 lines)
│   ├── _safe_float_any()
│   ├── _pick_canonical_purchase_action_value()
│   ├── build_time_range_string()
│   └── ensure_act_prefix()
│
└── constants.py (40-60 lines)
    ├── READ_DELAY, WRITE_DELAY, INSIGHTS_DELAY
    ├── API_VERSION
    └── Field definitions
```

**Benefits**:
- Each module has single responsibility
- Easier to mock for testing
- Easier to add new endpoints
- Rate limiting centralized

---

#### 2.2 `backend/app/features/meta_campaigns/service.py` (636 lines)
**Current State**: God object handling folders, rules, execution, and orchestration.

**Issues**:
- Multiple responsibilities: folder CRUD, rule CRUD, rule execution, logging
- Mix of database operations and business logic
- Difficult to test individual functions
- Long functions with complex logic

**Refactoring Strategy**:
```
meta_campaigns/services/
├── __init__.py
│
├── folder_service.py (120-150 lines)
│   ├── get_folders_by_ad_account()
│   ├── create_folder()
│   ├── update_folder()
│   ├── delete_folder()
│   ├── reorder_folders()
│   └── Folder CRUD operations only
│
├── rule_service.py (150-180 lines)
│   ├── get_rules_by_ad_account()
│   ├── get_rule_by_id()
│   ├── create_rule()
│   ├── update_rule()
│   ├── delete_rule()
│   ├── reorder_rules()
│   └── Rule CRUD operations only
│
├── rule_execution_service.py (180-220 lines)
│   ├── execute_rule() - main entry point
│   ├── fetch_rule_data()
│   ├── apply_filters()
│   ├── evaluate_items()
│   └── execute_actions_on_items()
│
├── rule_testing_service.py (100-120 lines)
│   ├── test_rule_execution()
│   ├── dry_run_rule()
│   └── simulate_actions()
│
└── rule_logging_service.py (80-100 lines)
    ├── log_rule_execution()
    ├── get_rule_logs()
    ├── get_log_details()
    └── format_log_entry()
```

**Benefits**:
- Clear separation of concerns
- Easier to test each service independently
- Reduced coupling between components
- Better code organization

---

### 🟡 HIGH PRIORITY (400-600 lines)

#### 2.3 `backend/app/features/meta_campaigns/condition_evaluator.py` (467 lines)
**Current State**: Large module with metric calculation and condition evaluation.

**Refactoring Strategy**:
```
meta_campaigns/evaluation/
├── __init__.py
│
├── metric_calculator.py (200-250 lines)
│   ├── calculate_metric_from_insights()
│   ├── calculate_cpp()
│   ├── calculate_purchase_count()
│   ├── calculate_purchase_value()
│   ├── calculate_ctr()
│   ├── calculate_conversion_rate()
│   └── Metric calculation functions
│
├── condition_evaluator.py (150-180 lines)
│   ├── evaluate_condition()
│   ├── evaluate_all_conditions()
│   ├── check_numeric_condition()
│   ├── check_string_condition()
│   └── Condition evaluation logic
│
└── metric_helpers.py (80-100 lines)
    ├── _safe_float_any()
    ├── _pick_canonical_purchase_action_value()
    ├── extract_action_value()
    └── parse_special_value()
```

---

#### 2.4 `backend/app/features/meta_campaigns/campaign_service.py` (357 lines)
**Current State**: Campaign data fetching and processing with rate limiting.

**Refactoring Strategy**:
```
meta_campaigns/campaign/
├── campaign_service.py (150-180 lines)
│   ├── fetch_campaigns_with_insights()
│   ├── fetch_campaign_hierarchy()
│   └── High-level campaign operations
│
├── campaign_enricher.py (100-120 lines)
│   ├── enrich_campaign_with_insights()
│   ├── add_performance_metrics()
│   └── format_campaign_response()
│
└── campaign_cache.py (80-100 lines)
    ├── Cache campaign data
    └── Invalidate cache logic
```

---

### 🟢 MEDIUM PRIORITY (300-400 lines)

#### 2.5 `backend/app/features/meta_campaigns/scheduler_service.py` (323 lines)
**Refactoring**: Extract cron parsing, timezone handling, and job scheduling into separate modules.

#### 2.6 `backend/app/features/meta_campaigns/action_executor.py` (262 lines)
**Refactoring**: Split by action type (budget updates, status changes, notifications).

---

## 3. Refactoring Priorities & Order

### Phase 1: Backend Foundation (Week 1-2)
**Goal**: Stabilize backend services for easier testing

1. ✅ Split `facebook_api_client.py` into modular API client
2. ✅ Refactor `service.py` into separate services
3. ✅ Split `condition_evaluator.py` into evaluation modules

**Why First**: Backend is more stable, easier to test, and frontend depends on it.

---

### Phase 2: Frontend Core Components (Week 3-4)
**Goal**: Reduce largest frontend components

4. ✅ Refactor `RulesSection.vue` (981 lines)
5. ✅ Refactor `ConditionItem.vue` (691 lines)
6. ✅ Refactor `LogDetailsDialog.vue` (572 lines)

**Why Next**: These are the most complex components causing maintenance issues.

---

### Phase 3: Frontend Utilities (Week 5)
**Goal**: Clean up utility functions

7. ✅ Split `cronHelpers.js` into cron modules
8. ✅ Split `useRuleJsonConverter.js` into converter modules

---

### Phase 4: Polish & Remaining Components (Week 6)
**Goal**: Complete remaining refactoring

9. ✅ Finish `RuleEditorView.vue` and child components
10. ✅ Refactor remaining backend services

---

## 4. Testing Strategy

### During Refactoring
- ✅ Create unit tests for each new module before refactoring
- ✅ Keep old code alongside new code during transition
- ✅ Use feature flags to switch between old/new implementations
- ✅ Test each phase before moving to next

### Regression Testing
- ✅ Test all rule execution scenarios
- ✅ Test all CRUD operations (folders, rules, ad accounts)
- ✅ Test drag-and-drop functionality
- ✅ Test JSON import/export
- ✅ Test schedule configurations

---

## 5. Risks & Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation**: 
- Incremental refactoring with parallel implementations
- Comprehensive testing before removing old code
- Feature flags for gradual rollout

### Risk 2: Time Investment
**Mitigation**: 
- Phased approach allows stopping at any phase
- Each phase delivers immediate value
- Prioritize most problematic files first

### Risk 3: Code Churn During Refactoring
**Mitigation**: 
- Communicate refactoring plan to team
- Create refactoring branches separate from features
- Document new structure clearly

---

## 6. Success Metrics

### Quantitative
- ✅ No files over 400 lines (target: max 350 lines)
- ✅ Reduce average file size by 50%
- ✅ Increase code coverage to 80%+
- ✅ Reduce component re-render times by 30%

### Qualitative
- ✅ Easier onboarding for new developers
- ✅ Faster bug fixes (easier to locate issues)
- ✅ More confident deployments
- ✅ Improved maintainability scores

---

## 7. Next Steps

### Immediate Actions (Before Starting Refactoring)
1. **Review this plan** with the team
2. **Create refactoring branch** (`refactor/large-files`)
3. **Set up test coverage** baseline
4. **Document current behavior** (integration tests)
5. **Create refactoring checklist** for each phase

### When Ready to Start
1. Begin with **Phase 1: Backend Foundation**
2. Start with `facebook_api_client.py` (clearest separation)
3. Create new modules alongside old code
4. Write tests for new modules
5. Gradually migrate old code to new modules
6. Remove old code once verified

---

## 8. Open Questions

1. **Are there existing tests** for the large files to ensure no regression?
2. **What is the deployment frequency** (affects refactoring strategy)?
3. **Are there active feature branches** that would conflict?
4. **What's the team's appetite** for breaking changes (if any)?
5. **Any performance issues** with current large files?

---

## 9. Additional Notes

### Existing Refactoring Work
- Frontend has **partial refactoring** already done (see `REFACTORING_*.md` files)
- Some components already extracted (`RulesSection.vue`, `LogDetailsDialog.vue`)
- Composables pattern already in use (`useAdAccounts.js`, `useRules.js`)
- Good foundation to build upon

### Architecture Strengths
- ✅ Good separation: frontend, backend, worker, scheduler
- ✅ Modular feature structure (`features/meta_campaigns/`)
- ✅ Composables pattern for reusable logic
- ✅ Clear API boundaries (FastAPI routes)

### Architecture Opportunities
- 🔄 Further service layer decomposition
- 🔄 Component size reduction
- 🔄 Utility module organization
- 🔄 Test coverage improvement

---

**End of Document**

*This plan is a living document. Update as refactoring progresses.*
