# Parent Status Conditions

## Overview

Parent status conditions allow you to check the status of parent objects when evaluating child entities. This is useful for rules that should only apply to items with specific parent states.

## Available Parent Status Conditions

### 1. Campaign Status (for Ad-Level and Ad Set-Level Rules)

**Condition Field:** `campaign_status`

**Purpose:** Check the status of the parent campaign when evaluating ads or ad sets.

**Use Cases:**
- Only target ads/ad sets in ACTIVE campaigns
- Exclude items from PAUSED or DELETED campaigns
- Combine with other conditions for complex rules

**Example - Ad Set Rule:**
```
Conditions:
  - Campaign Status = ACTIVE
  - Daily Budget < 100

Actions:
  - Increase Daily Budget by 20%
```

**Result:** Only increases budget for ad sets in ACTIVE campaigns.

### 2. Adset Status (for Ad-Level Rules)

**Condition Field:** `adset_status`

**Purpose:** Check the status of the parent ad set when evaluating ads.

**Use Cases:**
- Only target ads in ACTIVE ad sets
- Pause ads that belong to PAUSED ad sets
- Ensure ads match parent ad set status

**Example - Ad Rule:**
```
Conditions:
  - Adset Status = ACTIVE
  - Ad Status = ACTIVE
  - CPA (Last 7 Days) > 50

Actions:
  - Set Status to PAUSED
  - Send Notification
```

**Result:** Only pauses ads that are currently active and belong to active ad sets, with high CPA.

## How It Works

### Pre-Fetch Mechanism

To avoid excessive API calls, parent statuses are **pre-fetched** before condition evaluation:

1. **Detect Condition**: System scans rule conditions for `campaign_status` or `adset_status` fields
2. **Collect IDs**: Extracts unique parent IDs from filtered items
3. **Batch Fetch**: Fetches parent statuses in batches (up to 50 per API call)
4. **Cache**: Stores statuses in memory for fast lookup
5. **Evaluate**: Uses cached statuses during condition evaluation

### Performance

- **Efficient**: Only fetches statuses when needed
- **Batched**: Minimizes API calls with batch requests
- **Cached**: No repeated API calls for same parent objects

**Example:**
- Rule evaluates 100 ads from 5 ad sets
- Without optimization: 100+ API calls
- With pre-fetch: 1-2 API calls to fetch 5 ad set statuses

## Available Status Values

All status conditions support these Facebook status values:

- `ACTIVE`: Object is currently active and serving
- `PAUSED`: Object is paused
- `DELETED`: Object is deleted (soft delete)
- `ARCHIVED`: Object is archived (campaigns only)

## Operators

Parent status conditions support these operators:

- `=` (equals): Exact match
- `!=` (not equals): Exclude specific status

**Examples:**
```
Campaign Status = ACTIVE     → Only items from active campaigns
Campaign Status != PAUSED    → Exclude items from paused campaigns
Adset Status = ACTIVE        → Only ads from active ad sets
```

## Combining Multiple Status Conditions

You can combine multiple status conditions in the same rule:

**Example - Triple Status Check:**
```
Rule: High Performing Ad Reactivator
Level: Ad

Conditions (Group 1):
  - Campaign Status = ACTIVE
  - Adset Status = ACTIVE
  - Ad Status = PAUSED
  - CPA (Last 7 Days) < 30

Actions:
  - Set Status to ACTIVE
```

**Result:** Reactivates paused ads that belong to active ad sets in active campaigns, with good CPA.

## Error Handling

### Graceful Degradation

If parent status cannot be fetched (API error, network issue, etc.):

- **Condition Fails**: The status condition evaluates to `false`
- **Rule Continues**: Other conditions are still evaluated
- **Log Warning**: Error is logged for debugging
- **No Action**: Items fail the condition check and are excluded

### Missing Parent IDs

If an item doesn't have a parent ID field:

- **Ad with no `adset_id`**: `adset_status` condition fails
- **Ad/AdSet with no `campaign_id`**: `campaign_status` condition fails

## Best Practices

### 1. Use Scope Filters First

If you always want to target items from specific campaigns, use **Campaign Name** scope filters instead of conditions:

```
✅ BETTER (Scope Filter):
Scope: Campaign Name contains ["Prospecting"]
Conditions: CPA > 50

❌ LESS EFFICIENT (Condition):
Conditions:
  - Campaign Name contains "Prospecting"
  - CPA > 50
```

**Why?** Scope filters are applied before data fetch, reducing API calls.

### 2. Combine with Item Status

For ad-level rules, check both the ad status and parent statuses:

```
✅ COMPREHENSIVE:
Conditions:
  - Adset Status = ACTIVE
  - Ad Status = PAUSED
  - CPA < 30

Result: Only reactivates paused ads in active ad sets
```

### 3. Use Status Conditions for Safety

Add parent status checks to prevent unwanted actions:

```
✅ SAFE RULE:
Conditions:
  - Campaign Status = ACTIVE  ← Safety check
  - Spend > 1000

Actions:
  - Send Notification

Result: Only alerts for high spend in active campaigns
```

## Technical Details

### API Fields Fetched

For efficiency, only minimal fields are fetched:

- **Campaigns**: `id`, `status`, `effective_status`
- **Ad Sets**: `id`, `status`, `effective_status`

### Status Priority

If both `status` and `effective_status` are available, the system uses:
1. `status` (actual status set by user)
2. Falls back to `effective_status` if `status` is null

### Caching Scope

Status caches are:
- **Per Rule Execution**: Fresh fetch for each rule run
- **Not Persisted**: Cleared after rule completes
- **In-Memory Only**: Not stored in database

## Example: Complete Rule with Parent Status

**Use Case:** Pause underperforming ads, but only in active campaigns and active ad sets

```
Rule Name: Ad Performance Gate
Rule Level: Ad

Scope Filters:
  - Campaign Name contains: ["Scaling"]

Conditions (Group 1):
  - Campaign Status = ACTIVE
  - Adset Status = ACTIVE
  - Ad Status = ACTIVE
  - CPA (Last 7 Days) > 50
  - Spend (Last 7 Days) > 100

Actions:
  - Set Status to PAUSED
  - Append to Name: " | Paused - High CPA"
  - Send Notification to Slack

Result:
- Targets only ads in "Scaling" campaigns
- Checks parent campaign is active
- Checks parent ad set is active
- Checks ad itself is active
- Verifies CPA is too high with significant spend
- Pauses the ad, marks it, and sends alert
```

This multi-level status checking ensures rules only affect items in the correct state hierarchy.
