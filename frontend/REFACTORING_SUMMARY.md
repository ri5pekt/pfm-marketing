# MetaCampaignsView Refactoring Summary

## Current Issues
- **5,726 lines** in a single Vue component
- Multiple concerns mixed together:
  - Ad Account management
  - Campaign/Ad Set/Ad navigation
  - Rules management
  - Complex rule builder with conditions, actions, scheduling
  - Logs viewing
  - Multiple dialogs

## Proposed Solution

### Phase 1: Extract Utilities (Independent, no dependencies)
1. ✅ `utils/cronHelpers.js` - Cron expression building/parsing
2. ✅ `utils/specialValues.js` - Special value definitions and helpers
3. ✅ `utils/formValidation.js` - Form validation logic

### Phase 2: Extract Composables (State management)
1. `composables/useAdAccounts.js` - Ad account state and operations
2. `composables/useCampaigns.js` - Campaigns navigation state
3. `composables/useRules.js` - Rules state and operations

### Phase 3: Extract Dialog Components
1. `components/meta-campaigns/dialogs/AdAccountDialog.vue`
2. `components/meta-campaigns/dialogs/RuleBuilderDialog.vue` (largest, ~2000+ lines)
3. `components/meta-campaigns/dialogs/LogsDialog.vue`
4. `components/meta-campaigns/dialogs/LogDetailsDialog.vue`

### Phase 4: Extract Section Components
1. `components/meta-campaigns/AdAccountsSection.vue`
2. `components/meta-campaigns/CampaignsNavigation.vue`
3. `components/meta-campaigns/RulesSection.vue`

### Phase 5: Refactor Main View
- `views/MetaCampaignsView.vue` becomes orchestrator (~200-300 lines)

## Benefits
- **Maintainability**: Each component has a single responsibility
- **Reusability**: Components can be reused elsewhere
- **Testability**: Smaller units are easier to test
- **Performance**: Better code splitting and lazy loading
- **Developer Experience**: Easier to navigate and understand

## Estimated File Sizes After Refactoring
- MetaCampaignsView.vue: ~200-300 lines
- RuleBuilderDialog.vue: ~2000-2500 lines (still large, but isolated)
- Other components: 200-500 lines each
- Composables: 100-300 lines each
- Utilities: 50-200 lines each

