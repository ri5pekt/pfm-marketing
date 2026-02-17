# Custom Daily Schedule with Intervals

## Overview

The custom daily schedule now supports two execution modes:
1. **Run Once** - Execute at a specific time (original behavior)
2. **Run Every** - Execute multiple times at regular intervals

This allows you to create rules like "Run every 15 minutes on Sunday starting at 00:00" or "Run every hour on weekdays between business hours".

## Data Format

### Schedule Structure

The schedule is stored in the `schedule_cron` field as a JSON string:

```json
{
  "type": "custom_daily",
  "timezone": "America/New_York",
  "schedule": {
    "0": {...},  // Sunday
    "1": {...},  // Monday
    "2": {...},  // Tuesday
    "3": {...},  // Wednesday
    "4": {...},  // Thursday
    "5": {...},  // Friday
    "6": {...}   // Saturday
  }
}
```

### Run Once Format (Original)

Execute at a single time on selected days:

```json
{
  "type": "custom_daily",
  "timezone": "America/New_York",
  "schedule": {
    "0": "09:00",
    "1": "14:30"
  }
}
```

**Result:** Runs once on Sunday at 09:00 and once on Monday at 14:30.

### Run Every Format (New)

Execute multiple times at regular intervals:

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

**Result:** Runs every 15 minutes on Sunday (96 times total).

### Mixed Format (Run Once + Run Every)

You can mix both formats in the same schedule:

```json
{
  "type": "custom_daily",
  "timezone": "America/New_York",
  "schedule": {
    "0": {
      "start_time": "00:00",
      "interval_minutes": 15
    },
    "1": "12:00",
    "6": {
      "start_time": "08:00",
      "interval_minutes": 60
    }
  }
}
```

**Result:** 
- Sunday: Every 15 minutes starting at 00:00 (96 times)
- Monday: Once at 12:00
- Saturday: Every hour starting at 08:00 (16 times)

### With End Time (Optional)

Limit the interval execution to specific hours:

```json
{
  "type": "custom_daily",
  "timezone": "America/New_York",
  "schedule": {
    "1": {
      "start_time": "08:00",
      "end_time": "18:00",
      "interval_minutes": 30
    }
  }
}
```

**Result:** Runs every 30 minutes on Monday from 08:00 to 18:00 (21 executions).

## Interval Options

Available intervals:
- **15 minutes** - 96 executions/day (00:00, 00:15, 00:30, ..., 23:45)
- **30 minutes** - 48 executions/day
- **60 minutes (1 hour)** - 24 executions/day
- **180 minutes (3 hours)** - 8 executions/day
- **360 minutes (6 hours)** - 4 executions/day
- **720 minutes (12 hours)** - 2 executions/day

## Use Cases

### Sunday Stop Loss (SSL) Rule

Run every 15 minutes only on Sunday:

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

### Business Hours Monitoring

Run every 30 minutes during business hours on weekdays:

```json
{
  "type": "custom_daily",
  "timezone": "America/New_York",
  "schedule": {
    "1": {
      "start_time": "08:00",
      "end_time": "18:00",
      "interval_minutes": 30
    },
    "2": {
      "start_time": "08:00",
      "end_time": "18:00",
      "interval_minutes": 30
    },
    "3": {
      "start_time": "08:00",
      "end_time": "18:00",
      "interval_minutes": 30
    },
    "4": {
      "start_time": "08:00",
      "end_time": "18:00",
      "interval_minutes": 30
    },
    "5": {
      "start_time": "08:00",
      "end_time": "18:00",
      "interval_minutes": 30
    }
  }
}
```

### Late Attribution Reactivator

Run every 15 minutes, 24/7:

```json
{
  "type": "custom_daily",
  "timezone": "America/New_York",
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

### Different Schedules Per Day

Heavy monitoring on weekends, light on weekdays:

```json
{
  "type": "custom_daily",
  "timezone": "America/New_York",
  "schedule": {
    "0": {
      "start_time": "00:00",
      "interval_minutes": 15
    },
    "1": {
      "start_time": "00:00",
      "interval_minutes": 180
    },
    "2": {
      "start_time": "00:00",
      "interval_minutes": 180
    },
    "3": {
      "start_time": "00:00",
      "interval_minutes": 180
    },
    "4": {
      "start_time": "00:00",
      "interval_minutes": 180
    },
    "5": {
      "start_time": "00:00",
      "interval_minutes": 180
    },
    "6": {
      "start_time": "00:00",
      "interval_minutes": 15
    }
  }
}
```

## Export/Import Compatibility

The interval format is **fully compatible** with folder export/import:

### Exporting

```bash
GET /api/meta-campaigns/folders/{folder_id}/export
```

Response includes all rules with their schedules:

```json
{
  "folder": {
    "name": "Sunday Stop Loss Rules"
  },
  "rules": [
    {
      "name": "SSL - ROAS Based",
      "description": "Pauses underperforming ad sets on Sunday",
      "enabled": true,
      "position": 0,
      "schedule_cron": "{\"type\":\"custom_daily\",\"timezone\":\"America/New_York\",\"schedule\":{\"0\":{\"start_time\":\"00:00\",\"interval_minutes\":15}}}",
      "conditions": {...},
      "actions": {...}
    }
  ],
  "export_timestamp": "2026-02-17T12:00:00",
  "version": "1.0",
  "rules_count": 1
}
```

### Importing

```bash
POST /api/meta-campaigns/folders/import
{
  "ad_account_id": 123,
  "folder_json": { ... }
}
```

The imported rule will automatically schedule with the correct interval pattern.

## Implementation Details

### Scheduling Behavior

- Each execution time is scheduled as a separate job
- Jobs repeat weekly (7 days = 604800 seconds)
- Job IDs follow pattern: `rule_{rule_id}_day_{day}_time_{HH_MM}`
- Example: `rule_42_day_0_time_00_00`, `rule_42_day_0_time_00_15`, etc.

### Execution Counts

Examples of total weekly executions:
- Every 15 min, 7 days: 96 × 7 = **672 executions/week**
- Every 15 min, Sunday only: **96 executions/week**
- Every hour, weekdays: 24 × 5 = **120 executions/week**
- Every 3 hours, daily: 8 × 7 = **56 executions/week**

### Timezone Handling

- All schedules support timezone configuration
- Execution times calculated in specified timezone
- Stored in database as UTC
- Automatically handles DST transitions

## Migration Guide

### From Cron to Custom Daily with Intervals

**Old:** `*/15 * * * *` (every 15 minutes, always)

**New:**
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

**Old:** `*/15 * * * 0` (every 15 minutes, Sunday only)

**New:**
```json
{
  "type": "custom_daily",
  "timezone": "UTC",
  "schedule": {
    "0": {
      "start_time": "00:00",
      "interval_minutes": 15
    }
  }
}
```

## Frontend Implementation

### UI Structure

```
Period: [Daily at Custom Times ▼]

Select Days and Times:

☑ Sunday     Start at: [00:00]  [Run every ▼] → [15 minutes ▼]
☑ Monday     Start at: [12:00]  [Run once ▼]
☐ Tuesday    Start at: [HH:MM]  [Run once ▼]
☐ Wednesday  Start at: [HH:MM]  [Run once ▼]
☐ Thursday   Start at: [HH:MM]  [Run once ▼]
☐ Friday     Start at: [HH:MM]  [Run once ▼]
☑ Saturday   Start at: [08:00]  [Run every ▼] → [1 hour ▼]

Timezone: [America/New_York ▼]
```

### Dropdown Options

**When "Run once" is selected:**
- Simple execution at specified time

**When "Run every" is selected:**
- 15 minutes
- 30 minutes
- 1 hour
- 3 hours
- 6 hours
- 12 hours

### Execution Summary (Optional UI Enhancement)

```
Summary: This rule will execute:
- Sunday: 96 times (every 15 minutes starting at 00:00)
- Monday: Once at 12:00
- Saturday: 16 times (every 1 hour starting at 08:00)
Total: 113 executions per week
```

## Backward Compatibility

✅ **Fully backward compatible**

- Existing rules with string format continue to work
- No migration required
- New rules can use either format
- Export/import handles both formats automatically

## Technical Notes

### Database Storage

- Schedule stored in `campaign_rule.schedule_cron` column (TEXT)
- Format: JSON string (not parsed at database level)
- Validated when schedule is created/updated

### Job Management

- Uses RQ Scheduler with Redis backend
- Each execution time = separate scheduled job
- Jobs cleaned up on rule disable/delete
- Automatic rescheduling on server restart

### Error Handling

- Invalid time formats logged and skipped
- Invalid intervals default to "run once"
- Timezone errors fallback to UTC
- Failed job creation doesn't block other jobs

## API Examples

### Create Rule with Intervals

```bash
POST /api/meta-campaigns/rules
{
  "ad_account_id": 123,
  "name": "Sunday Stop Loss",
  "enabled": true,
  "schedule_cron": "{\"type\":\"custom_daily\",\"timezone\":\"America/New_York\",\"schedule\":{\"0\":{\"start_time\":\"00:00\",\"interval_minutes\":15}}}",
  "conditions": {...},
  "actions": {...}
}
```

### Update Rule Schedule

```bash
PUT /api/meta-campaigns/rules/{rule_id}
{
  "schedule_cron": "{\"type\":\"custom_daily\",\"timezone\":\"America/New_York\",\"schedule\":{\"0\":{\"start_time\":\"00:00\",\"interval_minutes\":30}}}"
}
```

## Best Practices

1. **Start with longer intervals** - Test with 1 hour before using 15 minutes
2. **Monitor API usage** - Frequent executions increase Meta API calls
3. **Use end_time for business hours** - Don't run overnight if not needed
4. **Different schedules per day** - Heavy monitoring when needed, light otherwise
5. **Export before major changes** - Always backup rules before modifying schedules
6. **Import as disabled** - Review imported rules before enabling

## Troubleshooting

### Rule not executing at expected interval

- Check logs: "Scheduled X jobs for custom daily rule {id}"
- Verify timezone is correct
- Confirm start_time format is HH:MM

### Too many executions

- Review interval_minutes value
- Check if end_time is set (defaults to 23:59)
- Verify which days are enabled

### Jobs not appearing in scheduler

- Check rule is enabled
- Verify schedule_cron is valid JSON
- Review server logs for scheduling errors

## Future Enhancements

Potential future additions:
- Custom interval input (any number of minutes)
- Multiple time windows per day
- Exclude time ranges (e.g., lunch break)
- Quick presets ("Business hours", "Weekends only")
- Execution count warnings for aggressive schedules
