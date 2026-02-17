# Interval Options Reference Guide

Quick reference for available execution intervals in custom daily schedules.

## Available Intervals

| Option | Minutes | Executions/Day | Executions/Week (1 day) | Executions/Week (7 days) |
|--------|---------|----------------|-------------------------|--------------------------|
| 15 minutes | 15 | 96 | 96 | 672 |
| 30 minutes | 30 | 48 | 48 | 336 |
| 1 hour | 60 | 24 | 24 | 168 |
| 3 hours | 180 | 8 | 8 | 56 |
| 6 hours | 360 | 4 | 4 | 28 |
| 12 hours | 720 | 2 | 2 | 14 |

## Execution Times by Interval

### 15 Minutes
```
00:00, 00:15, 00:30, 00:45
01:00, 01:15, 01:30, 01:45
... (continues every 15 minutes)
23:00, 23:15, 23:30, 23:45
```
**Total:** 96 times per day

### 30 Minutes
```
00:00, 00:30
01:00, 01:30
02:00, 02:30
... (continues every 30 minutes)
23:00, 23:30
```
**Total:** 48 times per day

### 1 Hour
```
00:00, 01:00, 02:00, 03:00, 04:00, 05:00
06:00, 07:00, 08:00, 09:00, 10:00, 11:00
12:00, 13:00, 14:00, 15:00, 16:00, 17:00
18:00, 19:00, 20:00, 21:00, 22:00, 23:00
```
**Total:** 24 times per day

### 3 Hours
```
00:00, 03:00, 06:00, 09:00
12:00, 15:00, 18:00, 21:00
```
**Total:** 8 times per day

### 6 Hours
```
00:00, 06:00, 12:00, 18:00
```
**Total:** 4 times per day

### 12 Hours
```
00:00, 12:00
```
**Total:** 2 times per day

## Business Hours Examples

### Example 1: Every 30 minutes during business hours (8 AM - 6 PM)
```json
{
  "start_time": "08:00",
  "end_time": "18:00",
  "interval_minutes": 30
}
```
**Execution times:**
```
08:00, 08:30, 09:00, 09:30, 10:00, 10:30, 11:00, 11:30
12:00, 12:30, 13:00, 13:30, 14:00, 14:30, 15:00, 15:30
16:00, 16:30, 17:00, 17:30, 18:00
```
**Total:** 21 times per day

### Example 2: Every hour during extended business hours (7 AM - 9 PM)
```json
{
  "start_time": "07:00",
  "end_time": "21:00",
  "interval_minutes": 60
}
```
**Execution times:**
```
07:00, 08:00, 09:00, 10:00, 11:00, 12:00, 13:00
14:00, 15:00, 16:00, 17:00, 18:00, 19:00, 20:00, 21:00
```
**Total:** 15 times per day

### Example 3: Every 15 minutes during peak hours (9 AM - 5 PM)
```json
{
  "start_time": "09:00",
  "end_time": "17:00",
  "interval_minutes": 15
}
```
**Total:** 33 times per day

## Common Use Cases

### 1. Sunday Stop Loss (Aggressive Monitoring)
**Goal:** Monitor underperforming ad sets closely on Sunday  
**Configuration:** Every 15 minutes, Sunday only  
**Executions:** 96 per week

```json
{
  "type": "custom_daily",
  "timezone": "America/New_York",
  "schedule": {
    "0": {
      "start_time": "00:00",
      "interval_minutes": 15
    }
  }
}
```

### 2. Late Attribution Reactivator (24/7)
**Goal:** Continuously check for conversion attribution  
**Configuration:** Every 15 minutes, all days  
**Executions:** 672 per week

```json
{
  "type": "custom_daily",
  "timezone": "UTC",
  "schedule": {
    "0": {"start_time": "00:00", "interval_minutes": 15},
    "1": {"start_time": "00:00", "interval_minutes": 15},
    "2": {"start_time": "00:00", "interval_minutes": 15},
    "3": {"start_time": "00:00", "interval_minutes": 15},
    "4": {"start_time": "00:00", "interval_minutes": 15},
    "5": {"start_time": "00:00", "interval_minutes": 15},
    "6": {"start_time": "00:00", "interval_minutes": 15}
  }
}
```

### 3. Profitable Gate Scaling (Daily Check)
**Goal:** Adjust budgets once per day  
**Configuration:** Once per day at midnight, except Sunday  
**Executions:** 6 per week

```json
{
  "type": "custom_daily",
  "timezone": "America/New_York",
  "schedule": {
    "1": "00:00",
    "2": "00:00",
    "3": "00:00",
    "4": "00:00",
    "5": "00:00",
    "6": "00:00"
  }
}
```

### 4. Business Hours Monitoring (Weekdays)
**Goal:** Monitor performance during business hours only  
**Configuration:** Every 30 minutes, 9 AM - 5 PM, weekdays  
**Executions:** 85 per week (17 per day × 5 days)

```json
{
  "type": "custom_daily",
  "timezone": "America/New_York",
  "schedule": {
    "1": {"start_time": "09:00", "end_time": "17:00", "interval_minutes": 30},
    "2": {"start_time": "09:00", "end_time": "17:00", "interval_minutes": 30},
    "3": {"start_time": "09:00", "end_time": "17:00", "interval_minutes": 30},
    "4": {"start_time": "09:00", "end_time": "17:00", "interval_minutes": 30},
    "5": {"start_time": "09:00", "end_time": "17:00", "interval_minutes": 30}
  }
}
```

### 5. Weekend Heavy, Weekday Light
**Goal:** More frequent checks on high-traffic weekends  
**Configuration:** 15 min on weekends, 3 hours on weekdays  
**Executions:** 248 per week (96+96+8+8+8+8+8+8)

```json
{
  "type": "custom_daily",
  "timezone": "America/New_York",
  "schedule": {
    "0": {"start_time": "00:00", "interval_minutes": 15},
    "1": {"start_time": "00:00", "interval_minutes": 180},
    "2": {"start_time": "00:00", "interval_minutes": 180},
    "3": {"start_time": "00:00", "interval_minutes": 180},
    "4": {"start_time": "00:00", "interval_minutes": 180},
    "5": {"start_time": "00:00", "interval_minutes": 180},
    "6": {"start_time": "00:00", "interval_minutes": 15}
  }
}
```

## Performance Considerations

### API Rate Limits
Meta API has rate limits. Consider:
- **15-minute intervals:** 96 API calls/day per rule
- **1-hour intervals:** 24 API calls/day per rule
- **Multiple rules:** Multiply by number of active rules

### Recommendations
1. **Start conservative:** Begin with 1-hour intervals and adjust based on needs
2. **Monitor usage:** Check Meta API usage in Facebook Business Manager
3. **Peak hours:** Use shorter intervals only when necessary
4. **Off-peak:** Use longer intervals overnight if not critical

### When to Use Each Interval

| Interval | Best For |
|----------|----------|
| **15 min** | Critical monitoring (Sunday Stop Loss, urgent budget protection) |
| **30 min** | Active monitoring during business hours |
| **1 hour** | Standard monitoring, balanced approach |
| **3 hours** | Periodic checks, stable campaigns |
| **6 hours** | Minimal monitoring, very stable campaigns |
| **12 hours** | Twice-daily checks, mostly automated campaigns |

## Calculation Formulas

### Executions Per Day
```
executions_per_day = floor((end_time_minutes - start_time_minutes) / interval_minutes) + 1
```

Where:
- `end_time_minutes` = (end_hour × 60) + end_minutes
- `start_time_minutes` = (start_hour × 60) + start_minutes

**Example:** 08:00 to 18:00 with 30-minute interval
```
start_time_minutes = (8 × 60) + 0 = 480
end_time_minutes = (18 × 60) + 0 = 1080
executions = floor((1080 - 480) / 30) + 1 = floor(600 / 30) + 1 = 20 + 1 = 21
```

### Executions Per Week
```
executions_per_week = sum of all enabled days' executions
```

**Example:** Sunday (96) + Monday (24) + Saturday (48)
```
executions_per_week = 96 + 24 + 48 = 168
```

## Timezone Impact

All execution times are calculated in the configured timezone.

**Example:** Rule set to "America/New_York" timezone
- Summer (EDT): UTC-4
- Winter (EST): UTC-5
- A rule at 09:00 EDT runs at 13:00 UTC
- Same rule at 09:00 EST runs at 14:00 UTC

**Important:** The rule always executes at 09:00 local time, regardless of UTC offset.

## Frontend Display Helpers

### Show Execution Count
```javascript
function getExecutionCount(intervalMinutes) {
  switch(intervalMinutes) {
    case 15: return 96;
    case 30: return 48;
    case 60: return 24;
    case 180: return 8;
    case 360: return 4;
    case 720: return 2;
    default: return Math.floor(1440 / intervalMinutes);
  }
}
```

### Format Interval Display
```javascript
function formatInterval(intervalMinutes) {
  if (intervalMinutes < 60) {
    return `${intervalMinutes} minutes`;
  }
  const hours = intervalMinutes / 60;
  return hours === 1 ? '1 hour' : `${hours} hours`;
}
```

### Calculate Time Range
```javascript
function calculateExecutionCount(startTime, endTime, intervalMinutes) {
  const start = timeToMinutes(startTime);
  const end = timeToMinutes(endTime);
  return Math.floor((end - start) / intervalMinutes) + 1;
}

function timeToMinutes(timeStr) {
  const [hours, minutes] = timeStr.split(':').map(Number);
  return hours * 60 + minutes;
}
```

## Quick Reference Card

Print-friendly summary:

```
┌─────────────────────────────────────────────────────┐
│     Interval Options - Quick Reference              │
├──────────────┬──────────┬────────────────────────────┤
│   Interval   │ Per Day  │  Weekly (1 day / 7 days)  │
├──────────────┼──────────┼────────────────────────────┤
│  15 minutes  │    96    │      96  /  672           │
│  30 minutes  │    48    │      48  /  336           │
│   1 hour     │    24    │      24  /  168           │
│   3 hours    │     8    │       8  /   56           │
│   6 hours    │     4    │       4  /   28           │
│  12 hours    │     2    │       2  /   14           │
└──────────────┴──────────┴────────────────────────────┘

Common Patterns:
• Sunday Stop Loss: 15 min, Sunday only = 96/week
• 24/7 Monitoring: 15 min, all days = 672/week
• Business Hours: 30 min, 8am-6pm = 21/day
• Daily Check: Once at midnight = 1/day
```

## Support

For questions or issues:
1. See full documentation: `docs/Custom Daily Schedule with Intervals.md`
2. Check implementation guide: `docs/IMPLEMENTATION_SUMMARY_Intervals.md`
3. Review test examples: `backend/tests/test_schedule_intervals.py`
