from rq_scheduler import Scheduler
from datetime import datetime
from croniter import croniter
from app.core.config import settings
from app.jobs.queues import redis_conn
from app.features.meta_campaigns import models, worker
from app.core.db import SessionLocal
import logging
import json

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
        # Check if it's a custom daily schedule (JSON format)
        try:
            schedule_data = json.loads(rule.schedule_cron)
            if schedule_data.get("type") == "custom_daily" and schedule_data.get("schedule"):
                return schedule_custom_daily_rule(rule, schedule_data["schedule"])
        except (json.JSONDecodeError, KeyError, TypeError):
            # Not JSON, continue with regular cron parsing
            pass

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


def schedule_custom_daily_rule(rule: models.CampaignRule, schedule: dict):
    """
    Schedule a rule with custom daily times.
    schedule is a dict like: {"0": "09:00", "1": "14:30", ...} where keys are day numbers (0=Sunday, 6=Saturday)
    """
    # First, unschedule any existing jobs for this rule
    unschedule_rule(rule.id)

    if not schedule:
        logger.warning(f"No schedule entries for custom daily rule {rule.id}")
        return None

    job_ids = []
    next_runs = []

    # Schedule a job for each day/time combination
    for day_str, time_str in schedule.items():
        try:
            day = int(day_str)
            hour, minute = map(int, time_str.split(":"))

            # Create a cron expression for this specific day and time
            # Cron format: minute hour * * dayOfWeek
            cron_expr = f"{minute} {hour} * * {day}"

            # Calculate next run time
            cron = croniter(cron_expr, datetime.now())
            next_run = cron.get_next(datetime)

            # Calculate interval (7 days = 604800 seconds)
            interval_seconds = 7 * 24 * 60 * 60  # Weekly interval

            # Create unique job ID for this day/time combination
            job_id = f"rule_{rule.id}_day_{day}_time_{time_str.replace(':', '_')}"

            logger.info(f"Scheduling rule {rule.id} ({rule.name}) for {['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][day]} at {time_str}: next run at {next_run}")

            # Schedule the job
            job = scheduler.schedule(
                scheduled_time=next_run,
                func=worker.check_campaign_rule,
                args=[rule.id],
                interval=interval_seconds,
                repeat=None,  # Repeat indefinitely
                id=job_id
            )

            job_ids.append(job.id)
            next_runs.append(next_run)

        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing day/time for rule {rule.id}: day={day_str}, time={time_str}, error={str(e)}")
            continue

    if not job_ids:
        logger.error(f"No valid schedules created for rule {rule.id}")
        return None

    # Update rule with the earliest next run time
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

