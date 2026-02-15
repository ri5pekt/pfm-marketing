# Complete Refactoring Guide

## Current Status

**MetaCampaignsView.vue is still 5,726 lines because:**
- ✅ New component files have been created
- ❌ Original file hasn't been replaced yet
- ❌ RuleBuilderDialog (~2000 lines) still needs extraction
- ❌ All old code is still in the original file

## What's Been Created

### ✅ Completed Extractions:
1. **Utilities** (~500 lines)
   - `utils/cronHelpers.js`
   - `utils/specialValues.js`

2. **Composables** (~650 lines)
   - `composables/useAdAccounts.js`
   - `composables/useCampaigns.js`
   - `composables/useRules.js`

3. **Section Components** (~530 lines)
   - `components/meta-campaigns/AdAccountsSection.vue`
   - `components/meta-campaigns/CampaignsNavigation.vue`
   - `components/meta-campaigns/RulesSection.vue`

4. **Dialog Components** (~700 lines)
   - `components/meta-campaigns/dialogs/AdAccountDialog.vue`
   - `components/meta-campaigns/dialogs/LogsDialog.vue`
   - `components/meta-campaigns/dialogs/LogDetailsDialog.vue`

**Total Extracted: ~2,380 lines**

## What Remains

### ❌ RuleBuilderDialog (~2000 lines)
This is the largest and most complex component. It contains:
- Complex rule builder form (6 sections)
- Conditions builder with special values
- Actions builder
- Scope filters
- Scheduling configuration (cron)
- JSON editor with syntax highlighting
- Form validation logic
- All related state and functions

**Location in original file:** Lines 452-1334 (template) + ~1500 lines of script logic

### ❌ Original File Replacement
The original `MetaCampaignsView.vue` needs to be replaced with a simplified orchestrator that:
- Uses all the extracted components
- Manages top-level state coordination
- Handles account selection
- Should be ~200-300 lines

## Next Steps to Complete

1. **Extract RuleBuilderDialog** - Create `components/meta-campaigns/dialogs/RuleBuilderDialog.vue`
   - Move template (lines 452-1334)
   - Move all rule form state and functions
   - Import utilities (cronHelpers, specialValues)
   - Handle form validation
   - Handle JSON editor

2. **Replace Original File** - Update `MetaCampaignsView.vue`:
   - Remove all old code
   - Import and use all extracted components
   - Keep only orchestration logic
   - Should reduce to ~200-300 lines

3. **Test and Fix** - Verify everything works

## Estimated Final Result

- **MetaCampaignsView.vue**: ~200-300 lines (from 5,726)
- **RuleBuilderDialog.vue**: ~2,000-2,500 lines (isolated)
- **All other components**: Already extracted

**Total reduction: 95% reduction in main file size**

## Files to Reference

- See `MetaCampaignsView_REFACTORED.vue` for the structure of the new main view
- All extracted components are ready to use
- RuleBuilderDialog extraction is the final step

