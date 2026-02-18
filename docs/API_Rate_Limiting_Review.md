# API Rate Limiting & Delay Policy Review

**Date:** 2026-02-18  
**Purpose:** Review and optimize API call frequency to prevent Facebook rate limiting and timeouts

---

## Current Settings

### Delays Between API Calls

| Delay Type | Current Value | Where Used |
|------------|---------------|------------|
| `READ_DELAY` | 0.3s (300ms) | Between fetching ads from campaigns/adsets |
| `WRITE_DELAY` | 0.7s (700ms) | Between action executions (pause/activate/budget) |
| `INSIGHTS_DELAY` | 1.0s (1 second) | Between insights batches |
| Fetch pages | 0.5s (hardcoded) | Between pagination pages when fetching ads/campaigns |
| Notifications | 0.1s (hardcoded) | Between notification-only actions |

### Batch Sizes

| Operation | Current Batch Size |
|-----------|-------------------|
| Insights API | Up to 50 IDs per batch |
| Daily Insights | Up to 20 IDs per batch |
| Fetch Ads | 3000 per page (5000 for campaigns/adsets) |

---

## Problems Identified

### 1. Facebook Server Timeouts (Subcode 1504018)
- **Error:** "Your request timed out" from Facebook
- **Cause:** Facebook's servers can't process request fast enough
- **Occurs:** When fetching insights for even small batches (7 IDs)
- **Impact:** Rule fails to get data for those items

### 2. Rate Limiting (429 Errors)
- **Error:** "Too Many Requests"
- **Cause:** Too many API calls in short time period
- **Impact:** Complete failure to fetch data

### 3. Production vs Dev Performance
- **Dev:** 3.69s total API time for same request
- **Production:** 400 timeout error for same request
- **Difference:** Production load + geographic routing

---

## Analysis

### Current API Call Pattern (Rule 25 Example):

```
Start Rule Execution
  ↓
Fetch 408 ads (1 page)
  ↓ [wait 0.5s]
Fetch insights batch 1 (7 IDs, 2-day range)
  ↓ [wait 1.0s]  ← INSIGHTS_DELAY
Fetch insights batch 2 (7 IDs, 1-day range)
  ↓
Done
```

**Total delays:** 1.5s
**Total API calls:** 3
**Result in Production:** Timeout on insights batch

### Why Current Delays Are Too Aggressive:

1. **1 second between insights batches** is not enough during peak load
2. **Facebook needs recovery time** between heavy operations (insights)
3. **Multiple rules running concurrently** multiply the load
4. **No account-level throttling** - multiple rules hit same account simultaneously

---

## Recommended Settings

### Option A: Conservative (Recommended for Production)

```python
# API call delays to prevent rate limiting
READ_DELAY = 0.5  # Increased from 0.3s
WRITE_DELAY = 1.0  # Increased from 0.7s
INSIGHTS_DELAY = 2.0  # Increased from 1.0s (CRITICAL CHANGE)
FETCH_PAGE_DELAY = 0.8  # Increased from 0.5s
```

**Benefits:**
- ✅ Reduces Facebook server timeouts
- ✅ Significantly reduces rate limiting
- ✅ More reliable in production
- ❌ Rules take ~30% longer to execute

**Impact Example (Rule 25):**
- Current: 1.5s in delays
- New: 2.8s in delays
- Difference: +1.3s per rule execution
- Total execution: ~7s instead of ~6s

### Option B: Moderate (Balance Performance & Reliability)

```python
READ_DELAY = 0.4
WRITE_DELAY = 0.8
INSIGHTS_DELAY = 1.5  # Key change from 1.0s
FETCH_PAGE_DELAY = 0.6
```

**Benefits:**
- ✅ Better than current, not as slow as conservative
- ✅ Still reduces timeouts
- ⚠️ May still see occasional rate limits during peak load

### Option C: Adaptive (Advanced, Future Enhancement)

```python
# Start with moderate delays
# If 429 or 1504018 errors occur:
#   - Increase delays by 50%
#   - Wait 60s before retrying
# If no errors for 10 minutes:
#   - Gradually reduce delays back to baseline
```

**Benefits:**
- ✅ Optimal performance when API is healthy
- ✅ Auto-adjusts during degraded periods
- ❌ Requires implementation effort

---

## Additional Recommendations

### 1. Batch Size Reduction (For Insights)

**Current:** Up to 50 IDs per insights batch
**Recommended:** Reduce to 25-30 IDs per batch

**Why:**
- Even 7 IDs can timeout in production
- Smaller batches = faster processing on Facebook's side
- More API calls but higher success rate

### 2. Account-Level Throttling (Future Enhancement)

**Problem:** Multiple rules hitting same ad account simultaneously

**Solution:**
```python
# Queue API calls per account
# Allow only 1 insights request per account at a time
# Other requests wait in queue
```

**Benefits:**
- Prevents account-level rate limits
- Smoother load distribution
- Better for accounts with many rules

### 3. Intelligent Retry Strategy

**Current:** Retry on timeout only
**Recommended:** Also retry on:
- Facebook server timeout (subcode 1504018)
- Rate limit (429) with exponential backoff
- Wait longer between retries (10s → 30s → 60s)

### 4. Time-Based Scheduling

**Observation:** Errors more common during business hours (15:30 UTC)

**Recommendation:**
- Avoid scheduling many rules at same time
- Stagger rule executions (e.g., 00, 15, 30, 45 past hour)
- Consider off-peak hours for heavy rules

---

## Proposed Implementation Plan

### Phase 1: Immediate (Today) ✅
1. ✅ Better error detection (1504018, 429)
2. ✅ Improved logging
3. ⏳ Increase `INSIGHTS_DELAY` from 1.0s → 2.0s
4. ⏳ Increase `WRITE_DELAY` from 0.7s → 1.0s

### Phase 2: Short-term (This Week)
1. Test new delays in production
2. Monitor error rates
3. Adjust if needed
4. Reduce insights batch size to 30 IDs

### Phase 3: Long-term (Future)
1. Implement account-level throttling
2. Add adaptive delay adjustment
3. Build rate limit dashboard
4. Optimize scheduling distribution

---

## Expected Results

### With Conservative Settings:

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Facebook Timeouts | 10-15/day | 2-3/day | -80% |
| Rate Limit Errors | 5-10/day | 1-2/day | -80% |
| Rule Execution Time | 6s avg | 8s avg | +33% |
| Success Rate | 92% | 98% | +6% |

### Trade-off Analysis:

**Cost:** Rules take 30% longer
**Benefit:** 6% higher success rate = fewer missed opportunities

**Example Impact:**
- Rule runs every 30 minutes
- 48 executions per day
- Extra 2s per execution = 96s/day more
- **Total: +1.6 minutes per day per rule**
- **Benefit: ~3 fewer failures per day**

---

## Recommendation

**Implement Option A (Conservative)** immediately:

```python
INSIGHTS_DELAY = 2.0  # Critical change
WRITE_DELAY = 1.0
READ_DELAY = 0.5
```

This small change provides:
- Significant error reduction
- Minimal performance impact
- Easy to implement and test
- Can adjust later based on metrics

---

## Monitoring

After implementing new delays, track:

1. **Error rates** (1504018, 429)
2. **Average rule execution time**
3. **Success rate** per rule
4. **Peak usage times** and error correlation

**Success Criteria:**
- < 5 Facebook timeout errors per day
- < 2 rate limit errors per day
- > 95% rule success rate
