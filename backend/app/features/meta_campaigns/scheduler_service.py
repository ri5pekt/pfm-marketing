from rq_scheduler import Scheduler
from datetime import datetime
from croniter import croniter
from app.core.config import settings
from app.jobs.queues import redis_conn
from app.features.meta_campaigns import models, worker
from app.core.db import SessionLocal
import logging

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
    """Schedule a rule to run based on its cron expression"""
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
        # Parse cron expression and get next run time
        cron = croniter(rule.schedule_cron, datetime.now())
        next_run = cron.get_next(datetime)

        # Calculate interval in seconds from cron expression
        interval_seconds = cron_to_interval_seconds(rule.schedule_cron)

        logger.info(f"Scheduling rule {rule.id} ({rule.name}): next run at {next_run}, interval {interval_seconds}s")

        # Schedule the job with interval (like the working project)
        job = scheduler.schedule(
            scheduled_time=next_run,
            func=worker.check_campaign_rule,
            args=[rule.id],
            interval=interval_seconds,
            repeat=None,  # Repeat indefinitely
            id=f"rule_{rule.id}"
        )

        # Update rule with next run time
        db = SessionLocal()
        try:
            rule_obj = db.query(models.CampaignRule).filter(models.CampaignRule.id == rule.id).first()
            if rule_obj:
                rule_obj.next_run_at = next_run
                db.commit()
        finally:
            db.close()

        return job.id
    except Exception as e:
        logger.error(f"Error scheduling rule {rule.id}: {str(e)}", exc_info=True)
        return None


def unschedule_rule(rule_id: int):
    """Remove a scheduled rule"""
    try:
        scheduler.cancel(f"rule_{rule_id}")
        return True
    except Exception as e:
        logger.error(f"Error unscheduling rule {rule_id}: {str(e)}")
        return False


def reschedule_all_rules():
    """Load all enabled rules from database and schedule them"""
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

