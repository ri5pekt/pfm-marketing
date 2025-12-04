from app.features.meta_campaigns import service
from app.core.db import SessionLocal
from app.jobs.queues import get_queue
from datetime import datetime
from croniter import croniter
import logging

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

        # Calculate next run time from cron expression
        if rule.schedule_cron:
            try:
                cron = croniter(rule.schedule_cron, now)
                next_run = cron.get_next(datetime)
                rule.next_run_at = next_run
                logger.info(f"Rule {rule_id} next run scheduled for {next_run}")
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

