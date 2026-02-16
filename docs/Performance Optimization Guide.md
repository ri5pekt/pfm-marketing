# Performance Optimization Guide

## Rule Execution Performance

Understanding how scope filters affect rule execution performance can help you create faster, more efficient rules.

---

## Scope Filter Performance

### ⚡ **Fast Filters** (Applied at API Level)

These filters are sent to Facebook's API, so only matching items are fetched:

#### 1. **IDs**
- **Performance**: ⭐⭐⭐⭐⭐ Fastest
- **API Calls**: 1 call (fetches only specified items)
- **Use When**: Targeting specific ads, ad sets, or campaigns by ID
- **Example**: Rule targets 2 specific ad sets → 1 API call

```json
{
  "ids": ["123456789", "987654321"]
}
```

#### 2. **Campaign IDs**
- **Performance**: ⚡⚡⚡⚡⚡ Very Fast
- **API Calls**: 1-2 calls depending on result size
- **Use When**: Targeting ads/ad sets within specific campaigns
- **Example**: Rule targets all ads in 5 campaigns → 1-2 API calls

```json
{
  "campaign_ids": ["111222333", "444555666"]
}
```

---

### 🐌 **Slow Filters** (Applied After Fetching)

These filters require fetching ALL items, then filtering in memory:

#### 3. **Name Contains**
- **Performance**: 🐌🐌🐌 Slow (requires fetching all items)
- **API Calls**: 10-20+ calls for large accounts (fetches everything, then filters)
- **Use When**: You don't know item IDs and need to search by name pattern
- **Example**: Rule targets ads with "#AO" in name → 15 API calls to fetch all 30,000 ads

```json
{
  "name_contains": ["#AO-FC", "#PGS-FC"]
}
```

**Why It's Slow:**
- Facebook API doesn't support name filtering
- System must fetch ALL ads/ad sets/campaigns (could be 30,000+ items)
- Then filters by name in memory

**Optimization Tip:** If you know the IDs, use the IDs filter instead!

#### 4. **Campaign Name Contains**
- **Performance**: 🐌🐌 Moderate (fetches all campaigns, then all items)
- **API Calls**: 5-15+ calls depending on account size
- **Use When**: Targeting items in campaigns matching a name pattern

---

## Performance Comparison

| Scope Filter | API Calls (Small Account) | API Calls (Large Account) | Speed |
|-------------|--------------------------|---------------------------|-------|
| **IDs** | 1 | 1 | ⚡⚡⚡⚡⚡ |
| **Campaign IDs** | 1-2 | 1-3 | ⚡⚡⚡⚡⚡ |
| **Campaign Name Contains** | 3-5 | 10-15 | 🐌🐌 |
| **Name Contains** | 5-10 | 15-25 | 🐌🐌🐌 |

---

## Optimization Strategies

### ✅ **Best Practices**

1. **Use IDs When Possible**
   - Fastest option
   - Directly fetches only what you need
   - Ideal for targeting specific items

2. **Use Campaign IDs for Bulk Operations**
   - Fast for targeting all items in specific campaigns
   - Better than name-based filtering

3. **Combine Filters Wisely**
   - ✅ **Good**: Campaign IDs + Status conditions
   - ✅ **Good**: IDs + Time-based metrics
   - ❌ **Slow**: Name Contains alone on large accounts

4. **Status Filters Are Free**
   - Status conditions (ACTIVE, PAUSED) are evaluated in the rule conditions
   - If you have a status condition in your rule, it's applied at the API level
   - No performance impact

### 🎯 **Real-World Examples**

#### Example 1: Sunday Stop Loss (Good Performance)
```json
{
  "rule_level": "ad_set",
  "campaign_ids": ["111222333", "444555666"],
  "conditions": {
    "status": "ACTIVE",
    "spend_today": "> daily_budget × 0.9"
  }
}
```
- **API Calls**: 2-3 (fetches only ad sets in specified campaigns)
- **Performance**: ⚡⚡⚡⚡⚡ Fast

#### Example 2: Auto Optimizer with Name Filter (Slower)
```json
{
  "rule_level": "ad",
  "name_contains": ["#AO-FC"],
  "conditions": {
    "cpp_last_7_days": "> 115",
    "roas_last_7_days": "< 1"
  }
}
```
- **API Calls**: 15-20 (must fetch all 30,000 ads to find ones with "#AO-FC")
- **Performance**: 🐌🐌🐌 Slow

---

## Monitoring Performance

### Log Indicators

Check your rule execution logs for performance metrics:

```json
{
  "api_calls": {
    "total": 16,
    "fetch_items": 15,
    "fetch_insights": 1,
    "actions": 0
  },
  "items_checked": 2,
  "items_meeting_conditions": 2
}
```

**Red Flag**: If `fetch_items` is high (>10) but `items_checked` is low (<10), you may be fetching too much data.

**Solution**: Consider using IDs or Campaign IDs filters instead of Name Contains.

---

## When to Accept Slower Performance

Some rules legitimately need name-based filtering:

1. **Dynamic targeting**: Need to automatically target new ads matching a pattern
2. **Pattern-based rules**: "#AO", "#PGS" naming conventions
3. **Don't know IDs**: Initial setup before collecting item IDs

In these cases, the slower performance is necessary for the flexibility.

---

## Future Optimizations

Potential improvements being considered:

1. **Caching**: Cache frequently-accessed item lists
2. **Incremental Fetching**: Only fetch items changed since last run
3. **Name-based API Filters**: Request Facebook to add name filtering support

---

## Summary

- ✅ **Use IDs or Campaign IDs for best performance**
- 🐌 **Name Contains is slower but sometimes necessary**
- 📊 **Monitor your rule execution logs**
- 🎯 **Optimize based on your account size**

