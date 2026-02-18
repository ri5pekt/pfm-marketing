# API Timing in JSON Logs

**Date:** 2026-02-18  
**Feature:** Response times now included in downloadable JSON logs

---

## What Changed

The JSON log file that you download from the UI now includes detailed timing information for all API operations.

---

## New JSON Structure

The `api_calls` section in the JSON log now includes a `timings` object:

```json
{
  "timestamp": "2026-02-18T08:14:42.311620",
  "rule_level": "ad",
  "api_calls": {
    "total": 2,
    "fetch_items": 1,
    "fetch_insights": 1,
    "actions": 0,
    "timings": {
      "fetch_items_seconds": 3.45,
      "fetch_insights_seconds": 8.72,
      "actions_seconds": 0,
      "total_api_time_seconds": 12.17,
      "total_execution_seconds": 15.83
    }
  }
}
```

---

## Timing Fields Explained

### `fetch_items_seconds`
- Time spent fetching ads/campaigns/adsets from Facebook API
- Includes pagination (all pages)
- Example: `3.45` = 3.45 seconds

### `fetch_insights_seconds`
- Time spent fetching insights (metrics like spend, ROAS, CPP)
- Includes all batches and time ranges
- Example: `8.72` = 8.72 seconds

### `actions_seconds`
- Time spent executing actions (pause, budget changes, etc.)
- Only includes time if actions were executed
- Example: `0` = no actions executed, or actions completed instantly

### `total_api_time_seconds`
- Sum of all API operation times
- Formula: `fetch_items + fetch_insights + actions`
- Example: `12.17` = total time spent on API calls

### `total_execution_seconds`
- Total time for entire rule execution
- Includes API calls + data processing + condition evaluation
- Example: `15.83` = total time from start to finish

---

## How to Use This Data

### 1. **Identify Slow Operations**
```json
{
  "fetch_items_seconds": 1.2,    // ✅ Fast
  "fetch_insights_seconds": 45.8  // ⚠️ Slow - may timeout
}
```

### 2. **Compare API vs Processing Time**
```json
{
  "total_api_time_seconds": 12.17,      // Time waiting on Facebook
  "total_execution_seconds": 15.83      // Total time
}
```
**Processing time:** `15.83 - 12.17 = 3.66` seconds

### 3. **Monitor After Changes**
- Check timing before and after optimization
- Identify if retry logic kicked in (longer times)
- Compare production vs dev timings

---

## Example Scenarios

### Fast Execution
```json
{
  "api_calls": {
    "total": 2,
    "timings": {
      "fetch_items_seconds": 1.2,
      "fetch_insights_seconds": 3.5,
      "actions_seconds": 0,
      "total_api_time_seconds": 4.7,
      "total_execution_seconds": 6.3
    }
  }
}
```
✅ All operations completed quickly

### Slow Insights API
```json
{
  "api_calls": {
    "total": 2,
    "timings": {
      "fetch_items_seconds": 2.1,
      "fetch_insights_seconds": 85.3,    // ⚠️ Close to 90s timeout
      "actions_seconds": 0,
      "total_api_time_seconds": 87.4,
      "total_execution_seconds": 89.2
    }
  }
}
```
⚠️ Insights took 85 seconds - close to timeout threshold

### With Retry (Estimated)
```json
{
  "api_calls": {
    "total": 2,
    "timings": {
      "fetch_items_seconds": 2.3,
      "fetch_insights_seconds": 145.8,   // Likely had 1 retry (90s + 5s wait + 50s)
      "actions_seconds": 0,
      "total_api_time_seconds": 148.1,
      "total_execution_seconds": 151.4
    }
  }
}
```
ℹ️ Long time suggests retry occurred (check Docker logs for confirmation)

### With Actions
```json
{
  "api_calls": {
    "total": 5,
    "timings": {
      "fetch_items_seconds": 1.8,
      "fetch_insights_seconds": 4.2,
      "actions_seconds": 2.1,            // Time to pause 3 ads
      "total_api_time_seconds": 8.1,
      "total_execution_seconds": 10.5
    }
  }
}
```
✅ Includes action execution time

---

## Benefits

1. **Quick Diagnosis** - See at a glance which operation is slow
2. **No Docker Access Needed** - All timing in the downloadable JSON
3. **Historical Tracking** - Compare timing across multiple test runs
4. **Production Monitoring** - Track timing trends over time

---

## Where to Find

1. **UI Test Run** - Download JSON log after testing a rule
2. **Rule Logs Page** - View/download historical logs
3. **All logs now include timing** - Both manual tests and scheduled executions

---

## Summary

Every JSON log now shows:
- ⏱️ How long each API operation took
- 📊 Total API time vs total execution time
- 🔍 Easy identification of slow operations
- 📈 Trackable over time for performance monitoring
