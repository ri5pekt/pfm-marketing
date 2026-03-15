# Rule Success Notification on Home Page

## Overview

Implemented success notifications that appear on the home page after successfully creating or updating a rule, instead of showing the notification in the rule editor before navigation.

## Date

February 15, 2026

## Problem

Previously, success notifications were shown in the rule editor just before navigating back to the home page. This meant users might miss the notification during the page transition.

## Solution

Pass success information via route query parameters and display the notification on the home page after navigation completes.

## Implementation

### 1. Rule Editor (`RuleEditorView.vue`)

**Before:**

```javascript
if (isEditMode.value) {
    await updateRule(ruleId.value, ruleData);
    toast.add({
        severity: "success",
        summary: "Success",
        detail: "Rule updated successfully",
        life: 3000,
    });
} else {
    await createRule(ruleData);
    toast.add({
        severity: "success",
        summary: "Success",
        detail: "Rule created successfully",
        life: 3000,
    });
}

goBack();
```

**After:**

```javascript
if (isEditMode.value) {
    await updateRule(ruleId.value, ruleData);
    // Navigate back with success message
    router.push({
        name: "meta-campaigns",
        query: { ruleUpdated: "true", ruleName: ruleForm.value.name },
    });
} else {
    await createRule(ruleData);
    // Navigate back with success message
    router.push({
        name: "meta-campaigns",
        query: { ruleCreated: "true", ruleName: ruleForm.value.name },
    });
}
```

### 2. Home Page (`MetaCampaignsView.vue`)

Added success notification check in `onMounted`:

```javascript
onMounted(async () => {
    // Check for success messages from rule creation/update
    if (route.query.ruleCreated === "true") {
        const ruleName = route.query.ruleName || "Rule";
        toast.add({
            severity: "success",
            summary: "Rule Created",
            detail: `${ruleName} was created successfully`,
            life: 4000,
        });
        // Clean up query params
        router.replace({ name: "meta-campaigns" });
    } else if (route.query.ruleUpdated === "true") {
        const ruleName = route.query.ruleName || "Rule";
        toast.add({
            severity: "success",
            summary: "Rule Updated",
            detail: `${ruleName} was updated successfully`,
            life: 4000,
        });
        // Clean up query params
        router.replace({ name: "meta-campaigns" });
    }

    // ... rest of initialization
});
```

Added required imports:

```javascript
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();
```

## Features

### Success Messages

**Create:**

- Summary: "Rule Created"
- Detail: "[Rule Name] was created successfully"

**Update:**

- Summary: "Rule Updated"
- Detail: "[Rule Name] was updated successfully"

### URL Cleanup

After showing the notification, the query parameters are automatically removed from the URL using `router.replace()`, keeping the URL clean.

**URL During Navigation:**

```
http://localhost:5173/meta-campaigns?ruleCreated=true&ruleName=My%20Rule
```

**URL After Cleanup:**

```
http://localhost:5173/meta-campaigns
```

### Error Handling

Errors still show toasts in the rule editor (not on home page), which is correct because:

- User stays on the editor to fix errors
- Context is preserved for debugging

## Benefits

✅ **Visible notifications** - Users see success message after page loads
✅ **Better UX** - No notification lost during page transition
✅ **Personalized message** - Includes the actual rule name
✅ **Clean URLs** - Query parameters automatically removed
✅ **Consistent pattern** - Same approach for both create and update
✅ **Proper error handling** - Errors stay in context

## Testing

- ✅ Create a new rule → See success toast on home page
- ✅ Update an existing rule → See success toast on home page
- ✅ URL query params are cleaned up after toast displays
- ✅ Error scenarios still show toast in editor
- ✅ No linter errors
