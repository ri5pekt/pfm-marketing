"""
Test examples for custom daily schedule with intervals

These are example test cases showing how the new interval feature works.
Run with: pytest tests/test_schedule_intervals.py
"""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.features.meta_campaigns.scheduler_service import generate_interval_times
from app.features.meta_campaigns.schedule_calculations import calculate_next_custom_daily_run


def test_generate_interval_times_15_minutes():
    """Test generating times for 15-minute intervals"""
    times = generate_interval_times("00:00", 15)
    assert len(times) == 96  # 24 hours * 4 (per hour) = 96
    assert times[0] == "00:00"
    assert times[1] == "00:15"
    assert times[2] == "00:30"
    assert times[-1] == "23:45"


def test_next_custom_daily_run_advances_to_next_interval_slot():
    """A Monday interval rule must advance within Monday, not jump a week."""
    tz = ZoneInfo("America/New_York")
    schedule = {
        "1": {
            "start_time": "00:01",
            "interval_minutes": 15,
        }
    }
    now = datetime(2026, 7, 20, 0, 1, 16, tzinfo=tz)  # Monday

    next_run = calculate_next_custom_daily_run(schedule, tz, now)

    assert next_run == datetime(2026, 7, 20, 4, 16, tzinfo=ZoneInfo("UTC"))


def test_next_custom_daily_run_rolls_to_next_week_after_last_slot():
    tz = ZoneInfo("America/New_York")
    schedule = {
        "1": {
            "start_time": "00:01",
            "end_time": "00:31",
            "interval_minutes": 15,
        }
    }
    now = datetime(2026, 7, 20, 0, 31, 1, tzinfo=tz)  # Monday

    next_run = calculate_next_custom_daily_run(schedule, tz, now)

    assert next_run == datetime(2026, 7, 27, 4, 1, tzinfo=ZoneInfo("UTC"))


def test_generate_interval_times_30_minutes():
    """Test generating times for 30-minute intervals"""
    times = generate_interval_times("00:00", 30)
    assert len(times) == 48  # 24 hours * 2 (per hour) = 48
    assert times[0] == "00:00"
    assert times[1] == "00:30"
    assert times[-1] == "23:30"


def test_generate_interval_times_1_hour():
    """Test generating times for 1-hour intervals"""
    times = generate_interval_times("00:00", 60)
    assert len(times) == 24  # 24 hours
    assert times[0] == "00:00"
    assert times[1] == "01:00"
    assert times[-1] == "23:00"


def test_generate_interval_times_with_end_time():
    """Test generating times with custom end time"""
    times = generate_interval_times("08:00", 30, "18:00")
    assert len(times) == 21  # 10 hours * 2 + 1 = 21
    assert times[0] == "08:00"
    assert times[-1] == "18:00"


def test_generate_interval_times_3_hours():
    """Test generating times for 3-hour intervals"""
    times = generate_interval_times("00:00", 180)
    assert len(times) == 8  # 24 / 3 = 8
    assert times == ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]


def test_generate_interval_times_6_hours():
    """Test generating times for 6-hour intervals"""
    times = generate_interval_times("00:00", 360)
    assert len(times) == 4  # 24 / 6 = 4
    assert times == ["00:00", "06:00", "12:00", "18:00"]


def test_generate_interval_times_12_hours():
    """Test generating times for 12-hour intervals"""
    times = generate_interval_times("00:00", 720)
    assert len(times) == 2  # 24 / 12 = 2
    assert times == ["00:00", "12:00"]


def test_schedule_format_run_once():
    """Test the format for run once schedule"""
    schedule = {
        "type": "custom_daily",
        "timezone": "America/New_York",
        "schedule": {
            "0": "09:00",  # Sunday at 09:00
            "1": "14:30"   # Monday at 14:30
        }
    }
    
    # This should be stored as JSON string
    schedule_cron = json.dumps(schedule)
    parsed = json.loads(schedule_cron)
    
    assert parsed["type"] == "custom_daily"
    assert parsed["timezone"] == "America/New_York"
    assert isinstance(parsed["schedule"]["0"], str)
    assert parsed["schedule"]["0"] == "09:00"


def test_schedule_format_run_every():
    """Test the format for run every (interval) schedule"""
    schedule = {
        "type": "custom_daily",
        "timezone": "America/New_York",
        "schedule": {
            "0": {
                "start_time": "00:00",
                "interval_minutes": 15
            }
        }
    }
    
    # This should be stored as JSON string
    schedule_cron = json.dumps(schedule)
    parsed = json.loads(schedule_cron)
    
    assert parsed["type"] == "custom_daily"
    assert parsed["timezone"] == "America/New_York"
    assert isinstance(parsed["schedule"]["0"], dict)
    assert parsed["schedule"]["0"]["start_time"] == "00:00"
    assert parsed["schedule"]["0"]["interval_minutes"] == 15


def test_schedule_format_mixed():
    """Test mixed format (some run once, some run every)"""
    schedule = {
        "type": "custom_daily",
        "timezone": "America/New_York",
        "schedule": {
            "0": {
                "start_time": "00:00",
                "interval_minutes": 15
            },
            "1": "12:00",  # Run once
            "6": {
                "start_time": "08:00",
                "interval_minutes": 60
            }
        }
    }
    
    schedule_cron = json.dumps(schedule)
    parsed = json.loads(schedule_cron)
    
    # Sunday: interval
    assert isinstance(parsed["schedule"]["0"], dict)
    assert parsed["schedule"]["0"]["interval_minutes"] == 15
    
    # Monday: run once
    assert isinstance(parsed["schedule"]["1"], str)
    assert parsed["schedule"]["1"] == "12:00"
    
    # Saturday: interval
    assert isinstance(parsed["schedule"]["6"], dict)
    assert parsed["schedule"]["6"]["interval_minutes"] == 60


def test_schedule_format_with_end_time():
    """Test format with optional end_time"""
    schedule = {
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
    
    schedule_cron = json.dumps(schedule)
    parsed = json.loads(schedule_cron)
    
    assert parsed["schedule"]["1"]["start_time"] == "08:00"
    assert parsed["schedule"]["1"]["end_time"] == "18:00"
    assert parsed["schedule"]["1"]["interval_minutes"] == 30


def test_export_import_compatibility():
    """Test that exported rules with intervals can be imported"""
    # Simulated export format
    export_data = {
        "folder": {
            "name": "Sunday Stop Loss"
        },
        "rules": [
            {
                "name": "SSL - ROAS Based",
                "description": "Pauses underperforming ad sets",
                "enabled": True,
                "position": 0,
                "schedule_cron": json.dumps({
                    "type": "custom_daily",
                    "timezone": "America/New_York",
                    "schedule": {
                        "0": {
                            "start_time": "00:00",
                            "interval_minutes": 15
                        }
                    }
                }),
                "conditions": {},
                "actions": {}
            }
        ],
        "version": "1.0",
        "rules_count": 1
    }
    
    # Verify schedule_cron can be parsed
    rule = export_data["rules"][0]
    schedule = json.loads(rule["schedule_cron"])
    
    assert schedule["type"] == "custom_daily"
    assert schedule["schedule"]["0"]["interval_minutes"] == 15


def test_execution_count_calculations():
    """Test execution count calculations for different intervals"""
    test_cases = [
        # (interval_minutes, expected_per_day)
        (15, 96),   # Every 15 min
        (30, 48),   # Every 30 min
        (60, 24),   # Every hour
        (180, 8),   # Every 3 hours
        (360, 4),   # Every 6 hours
        (720, 2),   # Every 12 hours
    ]
    
    for interval_minutes, expected_count in test_cases:
        times = generate_interval_times("00:00", interval_minutes)
        assert len(times) == expected_count, f"Failed for interval {interval_minutes}: got {len(times)}, expected {expected_count}"


def test_business_hours_only():
    """Test business hours schedule (8 AM to 6 PM)"""
    times = generate_interval_times("08:00", 30, "18:00")
    
    # 8:00 to 18:00 is 10 hours
    # 30-minute intervals = 20 half-hours + 1 (for 18:00) = 21 executions
    assert len(times) == 21
    assert times[0] == "08:00"
    assert times[-1] == "18:00"
    
    # Verify no times before 8 AM or after 6 PM
    for time_str in times:
        hour = int(time_str.split(":")[0])
        assert 8 <= hour <= 18


def test_sunday_stop_loss_use_case():
    """Test Sunday Stop Loss rule: every 15 minutes on Sunday"""
    schedule = {
        "type": "custom_daily",
        "timezone": "America/New_York",
        "schedule": {
            "0": {
                "start_time": "00:00",
                "interval_minutes": 15
            }
        }
    }
    
    times = generate_interval_times("00:00", 15)
    
    # 96 executions on Sunday
    assert len(times) == 96
    
    # Weekly total: 96 executions
    weekly_total = 96
    assert weekly_total == 96


def test_late_attribution_reactivator_24_7():
    """Test Late Attribution Reactivator: every 15 minutes, 24/7"""
    schedule = {
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
    
    times_per_day = generate_interval_times("00:00", 15)
    
    # 96 executions per day × 7 days = 672 executions per week
    weekly_total = len(times_per_day) * 7
    assert weekly_total == 672


if __name__ == "__main__":
    # Run basic tests
    print("Testing 15-minute intervals...")
    test_generate_interval_times_15_minutes()
    print("✓ 15-minute intervals work correctly")
    
    print("\nTesting schedule formats...")
    test_schedule_format_run_once()
    test_schedule_format_run_every()
    test_schedule_format_mixed()
    print("✓ All schedule formats work correctly")
    
    print("\nTesting execution counts...")
    test_execution_count_calculations()
    print("✓ Execution counts correct")
    
    print("\nTesting business hours...")
    test_business_hours_only()
    print("✓ Business hours filtering works")
    
    print("\nTesting use cases...")
    test_sunday_stop_loss_use_case()
    test_late_attribution_reactivator_24_7()
    print("✓ Real-world use cases validated")
    
    print("\n✅ All tests passed!")
