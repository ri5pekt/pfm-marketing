from app.features.meta_campaigns import service
from app.core.db import SessionLocal
from app.jobs.queues import get_queue
from datetime import datetime
from croniter import croniter
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


def check_campaign_rule(rule_id: int):
    """
    Worker function to check and execute a campaign rule.
    This will be called by RQ scheduler.
    """
    db = SessionLocal()
    try:
        rule = service.get_rule(db, rule_id)
        if not rule or not rule.enabled:
            logger.info(f"Rule {rule_id} is disabled or not found")
            return

        logger.info(f"Checking rule {rule_id}: {rule.name}")

        # Use the test_rule function which has the full implementation
        # This will fetch data, evaluate conditions, and log results
        result = service.test_rule(db, rule_id)

        # TODO: Execute actions if conditions are met
        # For now, test_rule just evaluates and logs

        logger.info(f"Rule {rule_id} check completed: {result.get('decision', 'unknown')}")

        # Update last_run_at and calculate next_run_at
        now = datetime.now()
        rule.last_run_at = now

        # Calculate next run time from cron expression or custom daily schedule
        if rule.schedule_cron:
            try:
                is_custom_daily = False
                schedule_cron_str = rule.schedule_cron
                timezone = "UTC"
                cron_expr = None

                # Check if it's a JSON-wrapped schedule (all schedule types now support timezone)
                try:
                    schedule_data = json.loads(rule.schedule_cron)

                    # Handle custom daily schedule
                    if schedule_data.get("type") == "custom_daily" and schedule_data.get("schedule"):
                        is_custom_daily = True
                        # Calculate next run time for custom daily schedule
                        schedule = schedule_data["schedule"]
                        timezone = schedule_data.get("timezone", "UTC")

                        # Get timezone object
                        try:
                            tz = ZoneInfo(timezone)
                        except Exception as e:
                            logger.warning(f"Invalid timezone {timezone}, using UTC: {str(e)}")
                            tz = ZoneInfo("UTC")

                        # Get current time in the schedule's timezone
                        now_tz = datetime.now(tz)
                        next_runs = []

                        for day_str, time_str in schedule.items():
                            try:
                                day = int(day_str)
                                hour, minute = map(int, time_str.split(":"))

                                # Create a cron expression for this specific day and time
                                # Cron format: minute hour * * dayOfWeek
                                cron_expr = f"{minute} {hour} * * {day}"

                                # Calculate next run time in the schedule's timezone
                                # croniter works with naive datetime, so we convert to naive first
                                now_naive = now_tz.replace(tzinfo=None)
                                cron = croniter(cron_expr, now_naive)
                                next_run_naive = cron.get_next(datetime)

                                # Localize to the schedule's timezone, then convert to UTC for storage
                                # pytz uses localize(), zoneinfo uses replace()
                                if hasattr(tz, 'localize'):
                                    # pytz timezone
                                    next_run_tz = tz.localize(next_run_naive)
                                else:
                                    # zoneinfo timezone
                                    next_run_tz = next_run_naive.replace(tzinfo=tz)

                                # Convert to UTC for storage
                                utc_tz = ZoneInfo("UTC")
                                next_run_utc = next_run_tz.astimezone(utc_tz)

                                next_runs.append(next_run_utc)
                            except (ValueError, KeyError) as e:
                                logger.warning(f"Error parsing day/time for next run calculation: day={day_str}, time={time_str}, error={str(e)}")
                                continue

                        if next_runs:
                            rule.next_run_at = min(next_runs)
                            logger.info(f"Rule {rule_id} next run scheduled for {rule.next_run_at} UTC (custom daily, timezone: {timezone})")
                        else:
                            logger.warning(f"Could not calculate next run time for custom daily rule {rule_id}")
                    else:
                        # Handle other schedule types wrapped in JSON (with timezone support)
                        if schedule_data.get("type") and schedule_data.get("cron"):
                            cron_expr = schedule_data.get("cron")
                            timezone = schedule_data.get("timezone", "UTC")
                except (json.JSONDecodeError, KeyError, TypeError):
                    # Not JSON, use as-is (legacy format, defaults to UTC)
                    cron_expr = rule.schedule_cron

                # If not custom_daily, calculate next run time for regular cron expression
                if not is_custom_daily and rule.next_run_at is None:
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

                    # Convert to UTC for storage
                    utc_tz = ZoneInfo("UTC")
                    next_run_utc = next_run_tz.astimezone(utc_tz)

                    rule.next_run_at = next_run_utc
                    logger.info(f"Rule {rule_id} next run scheduled for {next_run_utc} UTC (timezone: {timezone})")
            except Exception as e:
                logger.error(f"Error calculating next run time for rule {rule_id}: {str(e)}")

        db.commit()

    except Exception as e:
        logger.error(f"Error checking rule {rule_id}: {str(e)}", exc_info=True)
        service.create_rule_log(
            db,
            rule_id,
            "error",
            f"Error: {str(e)}",
            {"error": str(e)}
        )
    finally:
        db.close()


def enqueue_rule_check(rule_id: int):
    """Enqueue a rule check job"""
    queue = get_queue()
    job = queue.enqueue(check_campaign_rule, rule_id)
    return job.id

