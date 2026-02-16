# Campaign Name Scope Filters

## Overview

Campaign name scope filters allow you to narrow down which campaigns (and their child entities) should be evaluated by a rule. These filters operate at the **scope level** (before condition evaluation), making them highly performant.

## Available Filters

### 1. Campaign Name Contains (Positive Matching)

**Filter Type:** `campaign_name_contains`

**Purpose:** Include ONLY items from campaigns whose names contain any of the specified keywords.

**Use Cases:**
- Target specific campaign groups (e.g., "Prospecting", "Retargeting")
- Focus on seasonal campaigns (e.g., "Black Friday", "Summer Sale")
- Filter by campaign naming conventions (e.g., "TOF", "BOF", "Scaling")

**Example:**
```
Keywords: ["Prospecting", "TOF"]
Result: Only items from campaigns like "TOF - Prospecting - Q1" or "Prospecting Lookalike" will be evaluated
```

### 2. Campaign Name Doesn't Contain (Negative Matching)

**Filter Type:** `campaign_name_doesnt_contain`

**Purpose:** Exclude items from campaigns whose names contain any of the specified keywords.

**Use Cases:**
- Exclude specific campaign types (e.g., "Winback", "Test")
- Skip campaigns with certain tags (e.g., "Paused", "Archive")
- Filter out campaigns that shouldn't be automated (e.g., "Manual")

**Example:**
```
Keywords: ["Winback", "Test"]
Result: Items from campaigns like "Retargeting - Winback" or "Test Campaign 1" will be excluded
All other campaigns will be evaluated
```

## Combining Filters

You can use both filters together for precise targeting:

**Example: Target prospecting campaigns but exclude tests**
```
Campaign Name Contains: ["Prospecting"]
Campaign Name Doesn't Contain: ["Test", "Draft"]

Result: Only items from campaigns like "Prospecting - Lookalike Q1" will be evaluated
Campaigns like "Prospecting Test V2" or "Draft - Prospecting" will be excluded
```

## Performance Optimization

These filters are **pre-resolved** before the main data fetch, meaning:

1. **Fast Execution**: Campaign names are checked first
2. **Reduced API Calls**: Only relevant campaigns are fetched
3. **Lower Costs**: Fewer API calls = lower Facebook API usage

**Example Performance:**
- Without optimization: 15-20 API calls (fetch all ads → filter in memory)
- With campaign name filters: 2-3 API calls (filter campaigns → fetch only relevant ads)

## How It Works

### For Ad-Level and Ad Set-Level Rules:

1. Fetch all campaigns from the ad account
2. Apply positive filter (`campaign_name_contains`) if present
3. Apply negative filter (`campaign_name_doesnt_contain`) if present
4. Extract campaign IDs from matching campaigns
5. Fetch ONLY ads/ad sets from those campaigns (API-level filtering)
6. Continue with condition evaluation

### For Campaign-Level Rules:

1. Fetch all campaigns
2. Filter campaign names in memory (very fast)
3. Continue with condition evaluation

## UI Usage

1. **Add Scope Filter**: Click "Add Scope" in the Rule Builder
2. **Select Filter Type**: Choose "Campaign Name contains" or "Campaign Name doesn't contain"
3. **Enter Keywords**: Add one or more keywords (case-insensitive)
4. **Multiple Keywords**: Separate with commas or new lines

## Technical Notes

- **Case-Insensitive**: Matching is case-insensitive ("winback" matches "Winback" or "WINBACK")
- **Partial Match**: Keywords match anywhere in the campaign name
- **OR Logic for Contains**: If any keyword matches, the campaign is included
- **OR Logic for Doesn't Contain**: If any keyword matches, the campaign is excluded
- **Both Filters**: First apply positive (contains), then apply negative (doesn't contain)

## Example: Sunday's Stop Loss Rule

This rule uses negative matching to avoid reactivating Winback campaigns:

```
Rule: Late Attribution Reactivator
Level: Ad Set
Scope Filters:
  - Campaign Name doesn't contain: ["Winback"]
  - Adset Status: PAUSED

Conditions:
  - Cost Per Purchase (Last 7 Days) < $50

Actions:
  - Set Status to ACTIVE
```

**Result**: Only reactivates ad sets in non-Winback campaigns that meet the profitability threshold.
