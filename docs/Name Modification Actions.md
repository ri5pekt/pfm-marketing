# Name Modification Actions

## Overview

Name modification actions allow you to dynamically append or remove text from campaign, adset, or ad names. This is useful for marking items that have been affected by automated rules.

## Available Actions

### 1. Append to Name

Adds text to the end of an item's name.

**Action Type:** `append_to_name`

**Parameters:**

- `text` (string, required): The text to append to the name

**Example JSON:**

```json
{
    "type": "append_to_name",
    "text": " | #SSL"
}
```

**Behavior:**

- Appends the specified text to the end of the current name
- **Smart duplicate detection**: Won't append if the text already exists in the name
- Example: `"My Campaign"` → `"My Campaign | #SSL"`

---

### 2. Remove from Name

Removes text from an item's name.

**Action Type:** `remove_from_name`

**Parameters:**

- `text` (string, required): The text to remove from the name

**Example JSON:**

```json
{
    "type": "remove_from_name",
    "text": " | #SSL"
}
```

**Behavior:**

- Removes all occurrences of the specified text from the name
- If text is not found, silently skips (no error)
- Example: `"My Campaign | #SSL"` → `"My Campaign"`

---

## Use Case: Sunday's Stop Loss Rules

These actions are designed for the Sunday's Stop Loss (SSL) automated rules pattern:

### Rule 1: Adset Deactivator (Pause + Mark)

**When:** Adsets underperform on Sunday
**Actions:**

1. Pause the adset (`set_status: PAUSED`)
2. Mark it with `append_to_name` adding `" | #SSL"`

```json
{
    "actions": [
        {
            "type": "set_status",
            "status": "PAUSED"
        },
        {
            "type": "append_to_name",
            "text": " | #SSL"
        }
    ]
}
```

### Rule 2: Adset Reactivator (Unpause)

**When:** Monday morning
**Conditions:** Adset is PAUSED AND name contains "#SSL"
**Actions:**

1. Reactivate the adset (`set_status: ACTIVE`)

```json
{
    "actions": [
        {
            "type": "set_status",
            "status": "ACTIVE"
        }
    ]
}
```

### Rule 3: Name Cleanup (Remove Marker)

**When:** Monday morning (30 minutes after reactivation)
**Conditions:** Adset is ACTIVE AND name contains "#SSL"
**Actions:**

1. Remove the marker with `remove_from_name`

```json
{
    "actions": [
        {
            "type": "remove_from_name",
            "text": " | #SSL"
        }
    ]
}
```

---

## Complete SSL Implementation

### Rule 1: SSL Adset Deactivator

- **Level:** Ad Set
- **Schedule:** `*/15 * * * 0` (Every 15 minutes on Sundays)
- **Timezone:** America/New_York (EST)
- **Conditions:**
    - Adset Spend (Today) > 0.9 × Daily Budget
    - AND ROAS (Today) < 1
    - AND Status = ACTIVE
    - AND Campaign Status = ACTIVE
    - AND Campaign Name doesn't contain "Winback"
- **Actions:**
    1. Set Status: PAUSED
    2. Append to Name: " | #SSL"

### Rule 2: SSL Adset Reactivator

- **Level:** Ad Set
- **Schedule:** `0 6 * * 1` (Monday at 6:00 AM EST)
- **Timezone:** America/New_York (EST)
- **Conditions:**
    - Status = PAUSED
    - AND Name Contains: #SSL
    - AND Daily Budget > 0
- **Actions:**
    1. Set Status: ACTIVE

### Rule 3: SSL Name Cleanup

- **Level:** Ad Set
- **Schedule:** `30 6 * * 1` (Monday at 6:30 AM EST)
- **Timezone:** America/New_York (EST)
- **Conditions:**
    - Status = ACTIVE
    - AND Name Contains: #SSL
    - AND Daily Budget > 0
- **Actions:**
    1. Remove from Name: " | #SSL"

---

## API Details

### Facebook Graph API Call

Both actions use the standard Facebook Graph API to update the `name` field:

```
POST https://graph.facebook.com/v21.0/{item_id}
Parameters: name=<new_name>, access_token=<token>
```

### Rate Limiting

- Uses `WRITE_DELAY` (0.7 seconds) between actions
- Tracked in API call counter
- Rate limit headers monitored

### Error Handling

- If the name update fails, the error is logged and returned in the action result
- Slack notifications include success/failure status
- Duplicate detection prevents multiple appends of the same text

---

## Slack Notifications

When name modification actions execute, Slack notifications show:

**Append/Remove Success:**

```
Name Updated: Original Name → New Name
```

**No Change (duplicate/not found):**

```
Name Append: Text already present in name
Name Remove: Text not found in name
```

---

## Tips

1. **Use descriptive markers**: Make tags easy to identify (e.g., `" | #SSL"`, `" [PAUSED]"`)
2. **Include separators**: Add spaces or pipes to keep names readable
3. **Test first**: Use the "Test Rule" button to verify name changes before scheduling
4. **Schedule cleanup**: Always have a rule to remove temporary markers
5. **Check logs**: Review execution logs to see before/after names
