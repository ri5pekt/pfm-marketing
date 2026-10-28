from app.features.meta_campaigns import service
from app.core.db import SessionLocal
from app.jobs.queues import get_queue
from app.features.meta_campaigns.schedule_calculations import calculate_next_custom_daily_run
from datetime import datetime, timedelta, timezone as dt_timezone
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

FAILURE_RETRY_MINUTES = 15


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

        rule.last_run_at = datetime.now()
        next_run_utc = _compute_next_run(rule)
        if next_run_utc:
            rule.next_run_at = next_run_utc
            logger.info(f"Rule {rule_id} next run scheduled for {next_run_utc} UTC")

        db.commit()

    except Exception as e:
        logger.error(f"Error checking rule {rule_id}: {str(e)}", exc_info=True)
        db.rollback()
        service.create_rule_log(
            db,
            rule_id,
            "error",
            f"Error: {str(e)}",
            {"error": str(e)}
        )
        _schedule_retry_after_failure(db, rule_id)
    finally:
        db.close()


def _schedule_retry_after_failure(db, rule_id: int):
    """Push next_run_at forward after a failed run so the scheduler doesn't re-run it every poll."""
    try:
        rule = service.get_rule(db, rule_id)
        if not rule or not rule.enabled:
            return
        retry_at = datetime.now(dt_timezone.utc) + timedelta(minutes=FAILURE_RETRY_MINUTES)
        next_slot = _compute_next_run(rule)
        rule.next_run_at = min(next_slot, retry_at) if next_slot else retry_at
        db.commit()
        logger.info(f"Rule {rule_id} failed; next attempt at {rule.next_run_at} UTC")
    except Exception as e:
        db.rollback()
        logger.error(f"Error rescheduling rule {rule_id} after failure: {str(e)}")


def _compute_next_run(rule):
    """Return the next scheduled run (UTC) from the rule's cron or custom daily schedule, or None."""
    if not rule.schedule_cron:
        return None
    rule_id = rule.id
    try:
        timezone = "UTC"
        cron_expr = None

        # Check if it's a JSON-wrapped schedule (all schedule types now support timezone)
        try:
            schedule_data = json.loads(rule.schedule_cron)

            if schedule_data.get("type") == "custom_daily" and schedule_data.get("schedule"):
                timezone = schedule_data.get("timezone", "UTC")
                try:
                    tz = ZoneInfo(timezone)
                except Exception as e:
                    logger.warning(f"Invalid timezone {timezone}, using UTC: {str(e)}")
                    tz = ZoneInfo("UTC")

                next_run_utc = calculate_next_custom_daily_run(
                    schedule_data["schedule"],
                    tz,
                    datetime.now(tz),
                )
                if not next_run_utc:
                    logger.warning(f"Could not calculate next run time for custom daily rule {rule_id}")
                return next_run_utc

            if schedule_data.get("type") and schedule_data.get("cron"):
                cron_expr = schedule_data.get("cron")
                timezone = schedule_data.get("timezone", "UTC")
        except (json.JSONDecodeError, KeyError, TypeError):
            # Not JSON, use as-is (legacy format, defaults to UTC)
            cron_expr = rule.schedule_cron

        if cron_expr is None:
            cron_expr = rule.schedule_cron

        try:
            tz = ZoneInfo(timezone)
        except Exception as e:
            logger.warning(f"Invalid timezone {timezone}, using UTC: {str(e)}")
            tz = ZoneInfo("UTC")

        # croniter works with naive datetime in the schedule's timezone
        now_naive = datetime.now(tz).replace(tzinfo=None)
        next_run_naive = croniter(cron_expr, now_naive).get_next(datetime)

        if hasattr(tz, 'localize'):
            # pytz timezone
            next_run_tz = tz.localize(next_run_naive)
        else:
            next_run_tz = next_run_naive.replace(tzinfo=tz)

        return next_run_tz.astimezone(ZoneInfo("UTC"))
    except Exception as e:
        logger.error(f"Error calculating next run time for rule {rule_id}: {str(e)}")
        return None


def enqueue_rule_check(rule_id: int):
    """Enqueue a rule check job"""
    queue = get_queue()
    job = queue.enqueue(check_campaign_rule, rule_id)
    return job.id

