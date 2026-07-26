from datetime import datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional


def generate_interval_times(start_time: str, interval_minutes: int, end_time: str = "23:59") -> List[str]:
    """Generate HH:MM execution slots from start through end, inclusive."""
    start_hour, start_minute = map(int, start_time.split(":"))
    end_hour, end_minute = map(int, end_time.split(":"))
    if interval_minutes <= 0:
        raise ValueError("interval_minutes must be greater than zero")

    current_minutes = start_hour * 60 + start_minute
    end_minutes = end_hour * 60 + end_minute
    times = []
    while current_minutes <= end_minutes:
        hour = current_minutes // 60
        minute = current_minutes % 60
        times.append(f"{hour:02d}:{minute:02d}")
        current_minutes += interval_minutes
    return times


def _localize(local_naive: datetime, tz: Any) -> datetime:
    if hasattr(tz, "localize"):
        return tz.localize(local_naive)
    return local_naive.replace(tzinfo=tz)


def calculate_next_custom_daily_run(
    schedule: Dict[str, Any],
    tz: Any,
    now_tz: Optional[datetime] = None,
) -> Optional[datetime]:
    """Return the next custom-daily slot in UTC.

    Day keys use the application's convention: 0=Sunday through 6=Saturday.
    Interval configurations contribute every generated slot, not just start_time.
    """
    now_tz = now_tz or datetime.now(tz)
    if now_tz.tzinfo is None:
        now_tz = _localize(now_tz, tz)

    candidates = []
    for day_offset in range(8):
        candidate_date = now_tz.date() + timedelta(days=day_offset)
        app_weekday = candidate_date.isoweekday() % 7

        for day_str, time_config in schedule.items():
            if int(day_str) != app_weekday:
                continue

            if isinstance(time_config, str):
                execution_times = [time_config]
            elif isinstance(time_config, dict):
                start_time = time_config.get("start_time", "00:00")
                interval_minutes = time_config.get("interval_minutes")
                end_time = time_config.get("end_time", "23:59")
                execution_times = (
                    generate_interval_times(start_time, int(interval_minutes), end_time)
                    if interval_minutes
                    else [start_time]
                )
            else:
                continue

            for execution_time in execution_times:
                hour, minute = map(int, execution_time.split(":"))
                local_naive = datetime.combine(candidate_date, time(hour, minute))
                candidate = _localize(local_naive, tz)
                if candidate > now_tz:
                    candidates.append(candidate)

    if not candidates:
        return None

    next_local = min(candidates)
    return next_local.astimezone(timezone.utc)
