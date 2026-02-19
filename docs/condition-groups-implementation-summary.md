# Condition Groups (AND/OR Logic) - Implementation Summary

## Overview

Successfully implemented condition groups feature that allows rules to have multiple groups of conditions with:

- **AND logic within each group**: All conditions in a group must pass
- **OR logic between groups**: Any group can pass for the rule to execute
- **Full backward compatibility**: Existing rules automatically migrate to single-group format

## Implementation Date

February 15, 2026

## Design Decision: No group_id in JSON

**Rationale**: The `group_id` is not included in the exported JSON for the following reasons:

1. **Rule Copying**: When copying a rule, group IDs would be regenerated anyway
2. **Cleaner JSON**: Removes unnecessary UUID clutter from exported rules
3. **Simpler Structure**: Groups are identified by their array position
4. **Generated IDs**: Backend generates simple indexed IDs ("group_1", "group_2") from array position for logging
5. **Internal UUIDs**: Frontend still uses UUIDs internally (`groupId`) for Vue reactivity keys, but these are never exported

This keeps the JSON export clean and focused on the actual rule logic rather than implementation details.

## Files Modified

### Backend

1. **`backend/app/features/meta_campaigns/service.py`**
    - Added `normalize_conditions_to_groups()` helper function (lines 411-434)
    - Replaced flat condition evaluation with grouped evaluation logic (lines 455-541)
    - Logs now capture group-level results with `condition_groups`, `any_group_passed`, and `passed_group_ids`

### Frontend - State Management

2. **`frontend/src/composables/useRuleForm.js`**
    - Updated initial state from `conditions: []` to `conditionGroups: [{groupId, conditions: []}]`
    - Added group management methods: `addConditionGroup()`, `removeConditionGroup()`, `addConditionToGroup()`, `removeConditionFromGroup()`
    - Updated `initializeFormFromRule()` to handle both old and new formats with automatic migration

3. **`frontend/src/composables/useRuleJsonConverter.js`**
    - Updated `ruleFormToJSON()` to export `condition_groups` instead of flat `conditions`
    - Updated `jsonToRuleForm()` to handle both formats:
        - New format: `condition_groups` array
        - Old format: `conditions` array (migrated to single group)

### Frontend - UI Components

4. **`frontend/src/components/meta-campaigns/rule-builder/ConditionGroup.vue`** _(NEW)_
    - Container for a single condition group
    - Displays group header with index and delete button
    - Shows AND connectors between conditions
    - Contains "Add Condition" button within the group

5. **`frontend/src/components/meta-campaigns/rule-builder/ConditionGroupDivider.vue`** _(NEW)_
    - Visual OR separator between groups
    - Blue bordered label with gradient lines

6. **`frontend/src/components/meta-campaigns/rule-builder/RuleConditions.vue`**
    - Completely refactored to use grouped structure
    - Now uses `ConditionGroup` and `ConditionGroupDivider` components
    - Added "Add Group" button
    - Prevents deleting the last group (minimum 1 required)

### Frontend - Logs Display

7. **`frontend/src/components/meta-campaigns/dialogs/LogDetailsDialog.vue`**
    - Updated to display grouped evaluation results
    - Shows overall result with passed group IDs
    - Displays each group with header showing pass/fail status
    - Shows OR dividers between groups and AND connectors within groups
    - Maintains backward compatibility for old log format

## Data Structure

### Old Format (Flat)

```json
{
    "conditions": {
        "rule_level": "ad_set",
        "conditions": [
            { "field": "cpp", "operator": "<", "value": 100 },
            { "field": "status", "operator": "=", "value": "ACTIVE" }
        ]
    }
}
```

### New Format (Grouped)

```json
{
    "conditions": {
        "rule_level": "ad_set",
        "condition_groups": [
            {
                "conditions": [
                    { "field": "cpp", "operator": "<", "value": 100 },
                    { "field": "status", "operator": "=", "value": "ACTIVE" }
                ]
            },
            {
                "conditions": [{ "field": "roas", "operator": ">", "value": 2 }]
            }
        ]
    }
}
```

**Note**: The `group_id` is NOT stored in JSON. It is generated dynamically by the backend (e.g., "group_1", "group_2") based on array index for logging purposes only.

**Logic**: `(cpp < 100 AND status = ACTIVE) OR (roas > 2)`

## Evaluation Logic

### Backend Processing

1. **Normalization**: `normalize_conditions_to_groups()` converts old format to new format automatically
2. **Group Evaluation**: Each group is evaluated independently with AND logic for conditions
3. **OR Logic**: If any group passes, the item meets conditions
4. **Performance**: Early break when first group passes (optimization)
5. **Logging**: Captures which groups passed and detailed condition results per group

### Log Structure

```python
{
  "condition_groups": [
    {
      "group_id": "group_1",
      "all_conditions_passed": True,
      "conditions_evaluated": [...]
    }
  ],
  "any_group_passed": True,
  "passed_group_ids": ["group_1"]
}
```

## Testing Checklist

### Backend

- [x] Old format rules still work (single group)
- [ ] New format with multiple groups evaluates correctly
- [ ] OR logic works (any group passing = rule passes)
- [ ] AND logic within groups works (all conditions must pass)
- [ ] Logs show correct group structure

### Frontend UI

- [ ] Can add/remove groups
- [ ] Can add/remove conditions within groups
- [ ] Visual AND/OR labels display correctly
- [ ] Can't delete last group (minimum 1)
- [ ] Groups are visually distinct

### JSON Import/Export

- [ ] Export creates grouped JSON
- [ ] Import recognizes old flat format
- [ ] Import recognizes new grouped format
- [ ] Old rules auto-migrate on first edit

### Logs Display

- [ ] Shows which groups passed/failed
- [ ] Shows overall result (any group passed)
- [ ] Displays AND connectors within groups
- [ ] Displays OR dividers between groups
- [ ] Backward compatible with old log format

## Migration Path

**No database migration required** - Both formats are supported in the `conditions` JSONB column.

Users can migrate rules by:

1. Opening existing rule (auto-migrates to single group on load)
2. Save rule (now uses new format)

OR keep old rules as-is - they continue working with backward compatibility layer.

## Example Use Case: Profitable Gate Scaling

The feature was specifically designed to support the "Profitable Gate Scaling" rule which requires:

```
Group 1 (Budget Increase):
  - Contribution Margin >= 0 AND
  - ROAS >= 2.5

OR

Group 2 (Alternative Conditions):
  - Spend >= Daily Budget * 1.5 AND
  - CPP < 60
```

This can now be configured with two groups, where group 1 has the first two conditions and group 2 has the second two conditions.

## Next Steps

1. Test the implementation in development environment
2. Create test rules with multiple groups
3. Execute rules and verify logs display correctly
4. Test backward compatibility with existing rules
5. Deploy to production after successful testing
