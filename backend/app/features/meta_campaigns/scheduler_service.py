from rq_scheduler import Scheduler
from datetime import datetime
from croniter import croniter
from app.core.config import settings
from app.jobs.queues import redis_conn
from app.features.meta_campaigns import models, worker
from app.features.meta_campaigns.schedule_calculations import generate_interval_times
from app.core.db import SessionLocal
import logging
import json

# Try to use zoneinfo (Python 3.9+), fallback to pytz
try:
    from zoneinfo import ZoneInfo
except ImportError:
    try:
        from backports.zoneinfo import ZoneInfo
    except ImportError:
        import pytz
        def ZoneInfo(tz_name):
            return pytz.timezone(tz_name)

logger = logging.getLogger(__name__)

scheduler = Scheduler(connection=redis_conn)


def cron_to_interval_seconds(cron_expr: str) -> int:
    """Convert cron expression to interval in seconds for rq-scheduler"""
    # Parse cron: minute hour day month weekday
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {cron_expr}")

    minute, hour, day, month, weekday = parts

    # Calculate interval based on cron pattern
    # If minute is */X, interval is X minutes
    if minute.startswith('*/'):
        try:
            minutes = int(minute[2:])
            return minutes * 60
        except ValueError:
            pass

    # If minute is specific and hour is *, interval is 60 minutes (1 hour)
    if minute != '*' and hour == '*':
        return 60 * 60

    # If hour is */X, interval is X hours
    if hour.startswith('*/'):
        try:
            hours = int(hour[2:])
            return hours * 3600
        except ValueError:
            pass

    # If day is */X, interval is X days
    if day.startswith('*/'):
        try:
            days = int(day[2:])
            return days * 86400
        except ValueError:
            pass

    # Default: if it's a specific time (not */pattern), calculate from next two runs
    try:
        cron = croniter(cron_expr, datetime.now())
        first_run = cron.get_next(datetime)
        second_run = cron.get_next(datetime)
        interval = (second_run - first_run).total_seconds()
        return int(interval)
    except Exception:
        # Fallback: assume 1 minute if we can't parse
        logger.warning(f"Could not parse cron expression {cron_expr}, defaulting to 60 seconds")
        return 60


def schedule_rule(rule: models.CampaignRule):
    """Schedule a rule to run based on its cron expression or custom daily schedule"""
    if not rule.enabled:
        return None

    # If no schedule_cron, unschedule the rule (manual-only rule)
    if not rule.schedule_cron:
        unschedule_rule(rule.id)
        # Clear next_run_at
        db = SessionLocal()
        try:
            rule_obj = db.query(models.CampaignRule).filter(models.CampaignRule.id == rule.id).first()
            if rule_obj:
                rule_obj.next_run_at = None
                db.commit()
        finally:
            db.close()
        return None

    try:
        # Check if it's a JSON-wrapped schedule (all schedule types now support timezone)
        schedule_cron_str = rule.schedule_cron
        timezone = "UTC"
        cron_expr = None

        try:
            schedule_data = json.loads(rule.schedule_cron)

            # Handle custom daily schedule
            if schedule_data.get("type") == "custom_daily" and schedule_data.get("schedule"):
                timezone = schedule_data.get("timezone", "UTC")
                return schedule_custom_daily_rule(rule, schedule_data["schedule"], timezone)

            # Handle other schedule types wrapped in JSON (with timezone support)
            if schedule_data.get("type") and schedule_data.get("cron"):
                cron_expr = schedule_data.get("cron")
                timezone = schedule_data.get("timezone", "UTC")
        except (json.JSONDecodeError, KeyError, TypeError):
            # Not JSON, use as-is (legacy format, defaults to UTC)
            cron_expr = rule.schedule_cron

        # Use extracted cron expression or original if not JSON
        if cron_expr is None:
            cron_expr = rule.schedule_cron

        # Get timezone object
        try:
            tz = ZoneInfo(timezone)
        except Exception as e:
            logger.warning(f"Invalid timezone {timezone}, using UTC: {str(e)}")
            tz = ZoneInfo("UTC")
            timezone = "UTC"

        # Parse cron expression in the specified timezone
        # Get current time in the schedule's timezone
        now_tz = datetime.now(tz)
        now_naive = now_tz.replace(tzinfo=None)

        # croniter works with naive datetime
        cron = croniter(cron_expr, now_naive)
        next_run_naive = cron.get_next(datetime)

        # Localize to the schedule's timezone, then convert to UTC for storage
        if hasattr(tz, 'localize'):
            # pytz timezone
            next_run_tz = tz.localize(next_run_naive)
        else:
            # zoneinfo timezone
            next_run_tz = next_run_naive.replace(tzinfo=tz)

        # Convert to UTC for storage and scheduling
        utc_tz = ZoneInfo("UTC")
        next_run_utc = next_run_tz.astimezone(utc_tz)

        # Calculate interval in seconds from cron expression
        interval_seconds = cron_to_interval_seconds(cron_expr)

        logger.info(f"Scheduling rule {rule.id} ({rule.name}): next run at {next_run_utc} UTC (timezone: {timezone}), interval {interval_seconds}s")

        # Schedule the job with interval (rq-scheduler expects naive UTC datetime)
        job = scheduler.schedule(
            scheduled_time=next_run_utc.replace(tzinfo=None),
            func=worker.check_campaign_rule,
            args=[rule.id],
            interval=interval_seconds,
            repeat=None,  # Repeat indefinitely
            id=f"rule_{rule.id}",
            result_ttl=0,
        )

        # Update rule with next run time (stored in UTC)
        db = SessionLocal()
        try:
            rule_obj = db.query(models.CampaignRule).filter(models.CampaignRule.id == rule.id).first()
            if rule_obj:
                rule_obj.next_run_at = next_run_utc
                db.commit()
        finally:
            db.close()

        return job.id
    except Exception as e:
        logger.error(f"Error scheduling rule {rule.id}: {str(e)}", exc_info=True)
        return None


def schedule_custom_daily_rule(rule: models.CampaignRule, schedule: dict, timezone: str = "UTC"):
    """
    Schedule a rule with custom daily times.
    
    Supports two formats:
    1. Run once per day: {"0": "09:00", "1": "14:30", ...}
    2. Run with intervals: {"0": {"start_time": "00:00", "interval_minutes": 15}, ...}
    
    Args:
        rule: The campaign rule to schedule
        schedule: Dict where keys are day numbers (0=Sunday, 6=Saturday)
        timezone: Timezone string (e.g., "UTC", "America/New_York", "Asia/Jerusalem")
    """
    # First, unschedule any existing jobs for this rule
    unschedule_rule(rule.id)

    if not schedule:
        logger.warning(f"No schedule entries for custom daily rule {rule.id}")
        return None

    # Get timezone object
    try:
        tz = ZoneInfo(timezone)
    except Exception as e:
        logger.warning(f"Invalid timezone {timezone}, using UTC: {str(e)}")
        tz = ZoneInfo("UTC")

    job_ids = []
    next_runs = []

    # Get current time in the schedule's timezone
    now_tz = datetime.now(tz)
    now_naive = now_tz.replace(tzinfo=None)

    # Schedule jobs for each day/time combination
    for day_str, time_config in schedule.items():
        try:
            day = int(day_str)
            day_name = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][day]
            
            # Determine if this is a simple time string or interval config
            if isinstance(time_config, str):
                # Format 1: Simple string "HH:MM" - run once
                execution_times = [time_config]
                interval_info = f"once at {time_config}"
            elif isinstance(time_config, dict):
                # Format 2: Interval config with start_time and interval_minutes
                start_time = time_config.get("start_time", "00:00")
                interval_minutes = time_config.get("interval_minutes")
                end_time = time_config.get("end_time", "23:59")
                
                if interval_minutes:
                    # Generate all execution times for this interval
                    execution_times = generate_interval_times(start_time, interval_minutes, end_time)
                    interval_info = f"every {interval_minutes} minutes from {start_time} to {end_time} ({len(execution_times)} times)"
                else:
                    # No interval specified, treat as run once
                    execution_times = [start_time]
                    interval_info = f"once at {start_time}"
            else:
                logger.error(f"Invalid time_config format for rule {rule.id}, day {day}: {time_config}")
                continue

            logger.info(f"Scheduling rule {rule.id} ({rule.name}) for {day_name}: {interval_info} ({timezone})")

            # Schedule a job for each execution time
            for execution_time in execution_times:
                hour, minute = map(int, execution_time.split(":"))
                
                # Create a cron expression for this specific day and time
                # Cron format: minute hour * * dayOfWeek
                cron_expr = f"{minute} {hour} * * {day}"

                # Calculate next run time in the schedule's timezone
                cron = croniter(cron_expr, now_naive)
                next_run_naive = cron.get_next(datetime)

                # Localize to the schedule's timezone, then convert to UTC for storage
                if hasattr(tz, 'localize'):
                    # pytz timezone
                    next_run_tz = tz.localize(next_run_naive)
                else:
                    # zoneinfo timezone
                    next_run_tz = next_run_naive.replace(tzinfo=tz)

                # Convert to UTC for storage
                utc_tz = ZoneInfo("UTC")
                next_run_utc = next_run_tz.astimezone(utc_tz)

                # Calculate interval (7 days = 604800 seconds for weekly repeat)
                interval_seconds = 7 * 24 * 60 * 60

                # Create unique job ID for this day/time combination
                job_id = f"rule_{rule.id}_day_{day}_time_{execution_time.replace(':', '_')}"

                # Schedule the job (rq-scheduler expects UTC datetime)
                job = scheduler.schedule(
                    scheduled_time=next_run_utc.replace(tzinfo=None),  # rq-scheduler expects naive UTC
                    func=worker.check_campaign_rule,
                    args=[rule.id],
                    interval=interval_seconds,
                    repeat=None,  # Repeat indefinitely
                    id=job_id,
                    result_ttl=0,
                )

                job_ids.append(job.id)
                next_runs.append(next_run_utc)

        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Error parsing day/time for rule {rule.id}: day={day_str}, time_config={time_config}, error={str(e)}", exc_info=True)
            continue

    if not job_ids:
        logger.error(f"No valid schedules created for rule {rule.id}")
        return None

    # Update rule with the earliest next run time (stored in UTC)
    db = SessionLocal()
    try:
        rule_obj = db.query(models.CampaignRule).filter(models.CampaignRule.id == rule.id).first()
        if rule_obj and next_runs:
            rule_obj.next_run_at = min(next_runs)
            db.commit()
    finally:
        db.close()

    logger.info(f"Scheduled {len(job_ids)} jobs for custom daily rule {rule.id}")
    return job_ids[0]  # Return first job ID for compatibility


def unschedule_rule(rule_id: int):
    """Remove a scheduled rule (including all custom daily schedule jobs)"""
    try:
        # Cancel the main rule job
        try:
            scheduler.cancel(f"rule_{rule_id}")
        except:
            pass

        # Cancel all custom daily schedule jobs (they have pattern: rule_{rule_id}_day_*_time_*)
        # We need to get all scheduled jobs and filter by pattern
        try:
            scheduled_jobs = scheduler.get_jobs()
            for job in scheduled_jobs:
                if job.id and job.id.startswith(f"rule_{rule_id}_day_"):
                    try:
                        scheduler.cancel(job.id)
                        logger.debug(f"Cancelled custom daily job: {job.id}")
                    except Exception as e:
                        logger.warning(f"Error cancelling job {job.id}: {str(e)}")
        except Exception as e:
            logger.warning(f"Error getting scheduled jobs for rule {rule_id}: {str(e)}")

        return True
    except Exception as e:
        logger.error(f"Error unscheduling rule {rule_id}: {str(e)}")
        return False


def reschedule_all_rules():
    """Load all enabled rules from database and schedule them.

    Clears the entire rq-scheduler job registry first so that duplicate jobs
    are never created when this is called after a Redis restart or scheduler
    process restart.
    """
    # Wipe any surviving scheduled jobs before re-seeding to prevent duplicates
    try:
        existing_jobs = scheduler.get_jobs()
        for job in existing_jobs:
            try:
                scheduler.cancel(job.id)
            except Exception:
                pass
        if existing_jobs:
            logger.info(f"Cleared {len(existing_jobs)} existing scheduled jobs before reseed")
    except Exception as e:
        logger.warning(f"Could not clear existing scheduled jobs (Redis may be empty): {e}")

    db = SessionLocal()
    try:
        rules = db.query(models.CampaignRule).filter(
            models.CampaignRule.enabled == True,
            models.CampaignRule.schedule_cron.isnot(None)
        ).all()
        for rule in rules:
            schedule_rule(rule)
        logger.info(f"Scheduled {len(rules)} rules")
    finally:
        db.close()

