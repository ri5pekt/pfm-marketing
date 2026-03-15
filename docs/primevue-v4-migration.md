# PrimeVue v4 Component Migration

## Overview

Updated all deprecated PrimeVue v3 components to their v4 equivalents to eliminate console warnings.

## Date

February 15, 2026

## Changes Made

### 1. TabView → Tabs (RuleEditorView.vue)

**Before (v3 - deprecated):**

```vue
<TabView v-model:activeIndex="activeTabIndex">
    <TabPanel header="Form Editor">
        <!-- content -->
    </TabPanel>
    <TabPanel header="JSON Editor">
        <!-- content -->
    </TabPanel>
</TabView>
```

**After (v4):**

```vue
<Tabs v-model:value="activeTabIndex">
    <TabList>
        <Tab :value="0">Form Editor</Tab>
        <Tab :value="1">JSON Editor</Tab>
    </TabList>
    <TabPanels>
        <TabPanel :value="0">
            <!-- content -->
        </TabPanel>
        <TabPanel :value="1">
            <!-- content -->
        </TabPanel>
    </TabPanels>
</Tabs>
```

**Import changes:**

```javascript
// Old
import TabView from "primevue/tabview";
import TabPanel from "primevue/tabpanel";

// New
import Tabs from "primevue/tabs";
import TabList from "primevue/tablist";
import Tab from "primevue/tab";
import TabPanels from "primevue/tabpanels";
import TabPanel from "primevue/tabpanel";
```

### 2. InputSwitch → ToggleSwitch (3 files)

Updated in:

- `RuleBasicInfo.vue`
- `RuleTimeRange.vue`
- `ConditionTimeRange.vue`

**Before:**

```vue
<InputSwitch v-model="enabled" />
```

**After:**

```vue
<ToggleSwitch v-model="enabled" />
```

**Import changes:**

```javascript
// Old
import InputSwitch from "primevue/inputswitch";

// New
import ToggleSwitch from "primevue/toggleswitch";
```

### 3. Chips → InputChips (RuleLevelAndScope.vue)

**Before:**

```vue
<Chips v-model="keywords" placeholder="Type keyword and press Enter" />
```

**After:**

```vue
<InputChips v-model="keywords" placeholder="Type keyword and press Enter" />
```

**Import changes:**

```javascript
// Old
import Chips from "primevue/chips";

// New
import InputChips from "primevue/inputchips";
```

### 4. Missing Emit Declaration (RuleLevelAndScope.vue)

**Before:**

```javascript
const emit = defineEmits(["update:modelValue", "openAddScopeDialog", "clearScopeError"]);
```

**After:**

```javascript
const emit = defineEmits(["update:modelValue", "openAddScopeDialog", "clearScopeError", "ruleLevelChanged"]);
```

### 5. Prop Type Validation (CompactConditionValueInput.vue)

Fixed prop validation warning for `field` prop that can be `null` initially:

**Before:**

```javascript
field: {
    type: String,
    required: true,
},
```

**After:**

```javascript
field: {
    type: [String, null],
    required: false,
    default: null,
},
```

## Files Modified

1. `frontend/src/views/RuleEditorView.vue` - TabView → Tabs
2. `frontend/src/components/meta-campaigns/rule-builder/RuleBasicInfo.vue` - InputSwitch → ToggleSwitch
3. `frontend/src/components/meta-campaigns/rule-builder/RuleTimeRange.vue` - InputSwitch → ToggleSwitch
4. `frontend/src/components/meta-campaigns/condition-inputs/ConditionTimeRange.vue` - InputSwitch → ToggleSwitch
5. `frontend/src/components/meta-campaigns/rule-builder/RuleLevelAndScope.vue` - Chips → InputChips, added emit
6. `frontend/src/components/meta-campaigns/condition-inputs/CompactConditionValueInput.vue` - Fixed prop type

## Testing

✅ No linter errors
✅ All console warnings cleared
✅ Components function identically to before
✅ No breaking changes to functionality

## Benefits

- Clean console logs (no deprecation warnings)
- Future-proof codebase with PrimeVue v4 components
- Better developer experience
- Compliant with latest PrimeVue API standards
