# MetaCampaignsView Refactoring Plan

## Current State
- **File**: `frontend/src/views/MetaCampaignsView.vue`
- **Size**: 5,726 lines
- **Issues**: Monolithic component handling multiple concerns

## Target Structure

```
frontend/src/
├── views/
│   └── MetaCampaignsView.vue (main orchestrator, ~200-300 lines)
├── components/
│   └── meta-campaigns/
│       ├── AdAccountsSection.vue
│       ├── CampaignsNavigation.vue
│       ├── RulesSection.vue
│       └── dialogs/
│           ├── AdAccountDialog.vue
│           ├── RuleBuilderDialog.vue
│           ├── LogsDialog.vue
│           └── LogDetailsDialog.vue
├── composables/
│   ├── useAdAccounts.js
│   ├── useCampaigns.js
│   └── useRules.js
└── utils/
    ├── cronHelpers.js
    ├── formValidation.js
    └── specialValues.js
```

## Component Responsibilities

### 1. MetaCampaignsView.vue (Main View)
- Orchestrates all sections
- Manages top-level state coordination
- Handles account selection

### 2. AdAccountsSection.vue
- Displays ad accounts table
- Handles account selection
- Account CRUD operations

### 3. CampaignsNavigation.vue
- Campaigns/Ad Sets/Ads navigation
- Hierarchical view switching
- Search and filtering

### 4. RulesSection.vue
- Rules table display
- Rule actions (test, edit, delete, view logs)

### 5. AdAccountDialog.vue
- Create/edit ad account form
- Connection testing

### 6. RuleBuilderDialog.vue
- Complex rule builder form
- Conditions, actions, scope filters
- Scheduling configuration
- JSON editor

### 7. LogsDialog.vue
- Rule execution logs table
- Log filtering and pagination

### 8. LogDetailsDialog.vue
- Detailed log view
- Condition evaluations
- Action results

## Composables

### useAdAccounts.js
- Ad account state management
- CRUD operations
- Connection testing

### useCampaigns.js
- Campaigns/Ad Sets/Ads state
- Loading and navigation logic

### useRules.js
- Rules state management
- Rule operations (CRUD, test, logs)

## Utilities

### cronHelpers.js
- Cron expression building/parsing
- Schedule formatting
- Timezone handling

### formValidation.js
- Rule form validation
- Schedule validation

### specialValues.js
- Special value definitions
- Special value helpers

## Refactoring Steps

1. ✅ Create directory structure
2. Extract utility functions
3. Extract composables
4. Extract dialog components
5. Extract section components
6. Update main view
7. Test and verify

