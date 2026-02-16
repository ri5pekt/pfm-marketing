# Performance Optimization: Parent Status Filters (Phase 2)

## Overview

This optimization pre-resolves parent status conditions (`campaign_status` and `adset_status`) to IDs **before** fetching items from Facebook API, dramatically reducing the amount of data fetched.

## How It Works

### Without Optimization:
```
1. Fetch ALL 6,707 paused ads with #AO
2. Check parent campaign status for each ad (in memory)
3. Check parent adset status for each ad (in memory)
4. Result: 6 relevant ads (0.09% efficiency)
```

### With Phase 2 Optimization:
```
1. Pre-fetch campaigns with status = ACTIVE → Get 91 campaign IDs
2. Pre-fetch adsets with status = ACTIVE (from those 91 campaigns) → Get ~500 adset IDs
3. Fetch ads where:
   - status = PAUSED (Phase 1)
   - campaign_id IN [91 campaigns]
   - adset_id IN [500 adsets]
4. Result: Fetch ~100 ads (not 6,707!)
5. Filter to 6 relevant ads (6% efficiency - 67x better!)
```

## Performance Impact

### Late Attribution Reactivator Example:

**Before Phase 2:**
- Items fetched: 6,707 ads
- API calls: 5
- Items evaluated: 6
- Efficiency: 0.09%

**After Phase 2:**
- Items fetched: ~100 ads (estimated)
- API calls: 6-7 (2 extra pre-fetch, but much smaller payload)
- Items evaluated: 6
- Efficiency: 6% (67x improvement!)

## When Optimization Applies

The optimization automatically activates when:

1. **Ad-level rules** with `adset_status = ACTIVE` condition
2. **Ad or AdSet-level rules** with `campaign_status = ACTIVE` condition
3. Operator is `=` (equality check)

## Technical Implementation

### Step 0.6a: Campaign Status Pre-Resolution

Location: `service.py` lines ~445-500

```python
# Extract campaign_status condition
if campaign_status = ACTIVE:
    # Fetch campaigns with effective_status = ACTIVE
    # Get campaign IDs
    # Add to scope_filters["campaign_ids"]
    # Will be applied at API level in Step 1
```

### Step 0.6b: Adset Status Pre-Resolution

Location: `service.py` lines ~500-555

```python
# Extract adset_status condition (ad-level rules only)
if adset_status = ACTIVE:
    # Fetch adsets with effective_status = ACTIVE
    # Optionally filter by campaign_ids from Step 0.6a
    # Get adset IDs
    # Add to scope_filters["adset_ids"]
    # Will be applied at API level in Step 1
```

### API-Level Filtering

Location: `facebook_api_client.py` lines ~186-212

```python
# Add adset_ids filter to API request
if adset_ids in scope_filters:
    filtering.append({
        "field": "adset.id",
        "operator": "IN",
        "value": adset_ids
    })
```

## Execution Order

The optimizations run in sequence:

1. **Step 0.5:** Campaign name filters → campaign_ids
2. **Step 0.6a:** Campaign status condition → campaign_ids (merge with Step 0.5)
3. **Step 0.6b:** Adset status condition → adset_ids (filtered by Step 0.6a campaign_ids)
4. **Step 1:** Fetch items with all filters applied at API level

## Logging

Look for these log messages to verify optimization is working:

```
[TIMING] Step 0.6a - Pre-resolving campaign_status=ACTIVE to campaign_ids for API optimization
[TIMING] Step 0.6a completed in 0.45 seconds - Found 91 campaigns with status=ACTIVE
[OPTIMIZATION] campaign_status condition resolved to campaign_ids - will fetch only from 91 campaigns

[TIMING] Step 0.6b - Pre-resolving adset_status=ACTIVE for API optimization
[TIMING] Step 0.6b completed in 0.62 seconds - Found 487 adsets with status=ACTIVE
[OPTIMIZATION] adset_status condition resolved to adset_ids - will fetch only from 487 adsets

[FETCH] Added campaign_ids filter to API request: 91 campaign(s)
[FETCH] Added adset_ids filter to API request: 487 adset(s)
```

## Combining with Other Optimizations

Phase 2 works seamlessly with existing optimizations:

**Example: Full optimization stack**
```
Rule: Late Attribution Reactivator
Scope: Name contains "#AO"
Conditions:
  - Status = PAUSED
  - Campaign Status = ACTIVE
  - Adset Status = ACTIVE
  - Conversions > 0
  - Spend < $10

Optimization Chain:
1. Phase 1: Filter by status=PAUSED → reduces 15,000 to 6,707
2. Step 0.6a: Filter by campaign_status=ACTIVE → reduces to 91 campaigns
3. Step 0.6b: Filter by adset_status=ACTIVE → reduces to 487 adsets
4. Name filter: "#AO" applied to final ~100 ads
Result: Fetch ~100 ads instead of 15,000 (150x improvement!)
```

## Edge Cases

1. **No matching parents:** If no campaigns/adsets match status filter, rule execution skips immediately
2. **Multiple condition groups:** Optimization still applies (uses first group's status conditions)
3. **Negative operators (!=):** Optimization doesn't apply (falls back to post-fetch filtering)

## Trade-offs

**Pros:**
- ✅ Dramatic reduction in data fetched (67-150x)
- ✅ Faster execution time
- ✅ Lower API bandwidth usage
- ✅ Works automatically for all applicable rules

**Cons:**
- ⚠️ 2-3 additional API calls for pre-fetching parents
- ⚠️ Slightly more complex execution flow

**Net Result:** Almost always a significant performance improvement!

## Monitoring

To verify optimization effectiveness, compare logs:

**Before Phase 2:**
```
data_fetch.total_items: 6707
items_checked: 6
```

**After Phase 2:**
```
data_fetch.total_items: 100
items_checked: 6
```

Look for dramatic reduction in `total_items` while `items_checked` stays similar.
