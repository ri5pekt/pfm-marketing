# Large Files Summary - Quick Reference

**Generated**: February 15, 2026  
**Purpose**: Quick overview of files that need refactoring attention

---

## Frontend Large Files

| Priority | File | Lines | Complexity | Refactoring Effort |
|----------|------|-------|------------|-------------------|
| 🔴 CRITICAL | `components/meta-campaigns/RulesSection.vue` | 981 | ⭐⭐⭐⭐⭐ | High (3-5 days) |
| 🔴 CRITICAL | `components/meta-campaigns/rule-builder/ConditionItem.vue` | 691 | ⭐⭐⭐⭐⭐ | High (3-4 days) |
| 🟡 HIGH | `components/meta-campaigns/dialogs/LogDetailsDialog.vue` | 572 | ⭐⭐⭐⭐ | Medium (2-3 days) |
| 🟡 HIGH | `views/RuleEditorView.vue` | 518 | ⭐⭐⭐⭐ | Medium (2-3 days) |
| 🟡 HIGH | `components/meta-campaigns/rule-builder/RuleLevelAndScope.vue` | 423 | ⭐⭐⭐ | Medium (2 days) |
| 🟢 MEDIUM | `utils/cronHelpers.js` | 403 | ⭐⭐⭐ | Low (1-2 days) |
| 🟢 MEDIUM | `composables/useRuleJsonConverter.js` | 396 | ⭐⭐⭐ | Low (1-2 days) |
| 🟢 MEDIUM | `components/meta-campaigns/rule-builder/RuleActions.vue` | 356 | ⭐⭐⭐ | Low (1-2 days) |
| 🟢 MEDIUM | `components/meta-campaigns/rule-builder/RuleSchedule.vue` | 320 | ⭐⭐⭐ | Low (1-2 days) |
| 🟢 MEDIUM | `views/MetaCampaignsView.vue` | 428 | ⭐⭐⭐ | Low (review needed) |
| ⚪ LOW | `composables/useAdAccounts.js` | 252 | ⭐⭐ | Very Low (1 day) |
| ⚪ LOW | `composables/useRuleForm.js` | 224 | ⭐⭐ | Very Low (optional) |

**Total Frontend Lines to Refactor**: ~5,544 lines across 12 files

---

## Backend Large Files

| Priority | File | Lines | Complexity | Refactoring Effort |
|----------|------|-------|------------|-------------------|
| 🔴 CRITICAL | `features/meta_campaigns/facebook_api_client.py` | 648 | ⭐⭐⭐⭐⭐ | High (3-4 days) |
| 🔴 CRITICAL | `features/meta_campaigns/service.py` | 636 | ⭐⭐⭐⭐⭐ | High (4-5 days) |
| 🟡 HIGH | `features/meta_campaigns/condition_evaluator.py` | 467 | ⭐⭐⭐⭐ | Medium (2-3 days) |
| 🟡 HIGH | `features/meta_campaigns/campaign_service.py` | 357 | ⭐⭐⭐ | Medium (2 days) |
| 🟢 MEDIUM | `features/meta_campaigns/scheduler_service.py` | 323 | ⭐⭐⭐ | Low (1-2 days) |
| 🟢 MEDIUM | `features/meta_campaigns/action_executor.py` | 262 | ⭐⭐⭐ | Low (1-2 days) |
| ⚪ LOW | `features/meta_campaigns/data_filtering.py` | 213 | ⭐⭐ | Very Low (optional) |
| ⚪ LOW | `features/meta_campaigns/routes.py` | 199 | ⭐⭐ | Very Low (optional) |
| ⚪ LOW | `features/meta_campaigns/rate_limit_tracker.py` | 194 | ⭐⭐ | Very Low (optional) |
| ⚪ LOW | `features/meta_campaigns/worker.py` | 188 | ⭐⭐ | Very Low (optional) |

**Total Backend Lines to Refactor**: ~3,487 lines across 10 files

---

## Refactoring Impact Analysis

### By Priority

| Priority | Files | Total Lines | Est. Time | Impact |
|----------|-------|-------------|-----------|--------|
| 🔴 CRITICAL | 4 files | 2,965 lines | 13-18 days | **Very High** - Core functionality |
| 🟡 HIGH | 4 files | 1,819 lines | 8-11 days | **High** - Complex components |
| 🟢 MEDIUM | 8 files | 2,759 lines | 8-14 days | **Medium** - Utilities & helpers |
| ⚪ LOW | 6 files | 1,488 lines | 3-6 days | **Low** - Optional improvements |

**Total Estimated Effort**: 32-49 days (6-10 weeks for 1 developer)

---

## Top 5 Refactoring Targets

### 1. 🥇 `RulesSection.vue` (981 lines)
- **Why**: Most complex component, multiple responsibilities
- **Impact**: Easier maintenance, better performance, reusable sub-components
- **Risk**: High (complex drag-and-drop logic)
- **Dependencies**: None
- **Recommendation**: Start here with careful testing

### 2. 🥈 `ConditionItem.vue` (691 lines)
- **Why**: Too many conditional branches, hard to extend
- **Impact**: Easier to add new field types, better testing
- **Risk**: Medium (complex logic but isolated)
- **Dependencies**: None
- **Recommendation**: Second priority, clear separation points

### 3. 🥉 `facebook_api_client.py` (648 lines)
- **Why**: Mixed concerns, hard to test and mock
- **Impact**: Better testability, easier API endpoint additions
- **Risk**: Medium (critical but well-defined)
- **Dependencies**: Used by service.py, campaign_service.py
- **Recommendation**: High impact, start with this on backend

### 4. 📊 `service.py` (636 lines)
- **Why**: God object with too many responsibilities
- **Impact**: Better separation of concerns, easier testing
- **Risk**: High (touches many parts of system)
- **Dependencies**: Routes, worker, scheduler
- **Recommendation**: Refactor after facebook_api_client.py

### 5. 📋 `LogDetailsDialog.vue` (572 lines)
- **Why**: Complex nested display logic
- **Impact**: Reusable log components, easier to extend
- **Risk**: Low (mostly display logic)
- **Dependencies**: None
- **Recommendation**: Good "quick win" for visible improvement

---

## Refactoring Patterns to Apply

### Frontend Patterns
1. **Component Composition** - Break large components into smaller, focused ones
2. **Composables Extraction** - Move logic out of components into reusable composables
3. **Utility Modules** - Split utility files by function domain
4. **Value Input Strategy** - Create specialized input components for different value types

### Backend Patterns
1. **Service Layer Pattern** - One service per domain concept (folders, rules, execution)
2. **Repository Pattern** - Separate data access from business logic
3. **Strategy Pattern** - For condition evaluation and action execution
4. **Facade Pattern** - Simplify complex API client interactions

---

## Common Anti-Patterns Found

### ❌ God Objects
- **Files**: `service.py`, `facebook_api_client.py`
- **Issue**: Too many responsibilities in one module
- **Fix**: Split by responsibility (SRP - Single Responsibility Principle)

### ❌ Long Methods
- **Files**: Most files over 300 lines
- **Issue**: Functions with 100+ lines, hard to understand
- **Fix**: Extract methods, apply Tell Don't Ask principle

### ❌ Conditional Complexity
- **Files**: `ConditionItem.vue`, `condition_evaluator.py`
- **Issue**: Deep nesting, many if/else branches
- **Fix**: Strategy pattern, lookup tables, polymorphism

### ❌ Mixed Concerns
- **Files**: `RulesSection.vue`, `RuleEditorView.vue`
- **Issue**: Display + logic + state management in one component
- **Fix**: Separate concerns - display, logic, state

---

## Dependencies & Order

### Backend Refactoring Order
```
1. facebook_api_client.py (no dependencies)
   ↓
2. condition_evaluator.py (uses facebook_api_client)
   ↓
3. action_executor.py (independent)
   ↓
4. service.py (uses all of above)
   ↓
5. campaign_service.py (uses facebook_api_client)
   ↓
6. scheduler_service.py (uses service.py)
```

### Frontend Refactoring Order
```
1. cronHelpers.js (utility, no dependencies)
   ↓
2. useRuleJsonConverter.js (uses cronHelpers)
   ↓
3. ConditionItem.vue (independent component)
   ↓
4. LogDetailsDialog.vue (independent component)
   ↓
5. RulesSection.vue (independent component)
   ↓
6. RuleLevelAndScope.vue, RuleActions.vue, RuleSchedule.vue (parallel)
   ↓
7. RuleEditorView.vue (uses all rule-builder components)
```

---

## Quick Wins (1-2 days each)

These provide immediate value with low risk:

1. ✅ **Split `cronHelpers.js`** - Pure functions, easy to test
2. ✅ **Extract `LogDetailsDialog.vue` components** - Display logic only, low risk
3. ✅ **Create `metric_calculator.py`** - Extract from `condition_evaluator.py`
4. ✅ **Split `facebook_api/helpers.py`** - Utility functions, no dependencies

---

## Postpone Until Later

These can wait until after critical refactoring:

- ⏸️ `data_filtering.py` (213 lines) - Reasonable size
- ⏸️ `routes.py` (199 lines) - Mostly route definitions
- ⏸️ `rate_limit_tracker.py` (194 lines) - Single concern
- ⏸️ `useRuleForm.js` (224 lines) - Acceptable size
- ⏸️ `useAdAccounts.js` (252 lines) - Acceptable size

---

## Success Criteria

### Per File
- ✅ No single file over 400 lines
- ✅ Each file has single, clear responsibility
- ✅ Functions under 50 lines (except specific cases)
- ✅ Test coverage > 80%

### Overall
- ✅ Reduced average file size by 50%
- ✅ Improved maintainability score
- ✅ No regression in functionality
- ✅ Faster CI/CD pipeline (better test isolation)

---

## Resources Needed

### Team
- 1 senior developer (lead refactoring, review)
- 1 mid-level developer (implementation, testing)
- QA resource (regression testing)

### Time
- **Minimum Viable**: 4 weeks (critical files only)
- **Recommended**: 8 weeks (critical + high priority)
- **Complete**: 12 weeks (all files)

### Tools
- Code coverage tools (pytest-cov, vitest coverage)
- Static analysis (ESLint, Pylint)
- Refactoring IDE support (IntelliJ, VS Code)

---

**Last Updated**: February 15, 2026  
**Status**: Planning Phase - Ready for Review
