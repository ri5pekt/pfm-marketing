#!/usr/bin/env python3
"""
Rule scheduler — polls the database every POLL_INTERVAL seconds for rules
that are due to run and enqueues them via RQ.

This replaces the rq-scheduler interval mechanism which has compatibility
issues with rq >= 1.11 (jobs run once and are never re-queued).

Flow:
  1. Rule created/updated via API → schedule_rule() sets next_run_at in DB
  2. This loop finds rules where next_run_at <= now and enqueues them
  3. Worker executes the rule and updates next_run_at to the next occurrence
  4. Repeat
"""

import rq
import rq.utils

# Patch for rq-scheduler compatibility (kept for scheduler_service imports)
class ColorizingStreamHandler:
    pass
rq.utils.ColorizingStreamHandler = ColorizingStreamHandler

from app.core.db import SessionLocal
from app.features.meta_campaigns import models, worker
from app.jobs.queues import redis_conn, get_queue
import redis as redis_lib
from datetime import datetime, timezone
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

POLL_INTERVAL = 10  # seconds between DB polls


def wait_for_redis(interval: int = 5):
    """Block until Redis responds to PING."""
    while True:
        try:
            redis_conn.ping()
            return
        except redis_lib.exceptions.ConnectionError:
            logger.warning(f"Redis not reachable, retrying in {interval}s...")
            time.sleep(interval)


def enqueue_due_rules():
    """Query the DB for rules that are due and enqueue them via RQ."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        due_rules = db.query(models.CampaignRule).filter(
            models.CampaignRule.enabled == True,
            models.CampaignRule.schedule_cron.isnot(None),
            models.CampaignRule.next_run_at.isnot(None),
            models.CampaignRule.next_run_at <= now,
        ).all()

        if not due_rules:
            return

        queue = get_queue()
        enqueued = 0
        for rule in due_rules:
            scheduled_ts = int(rule.next_run_at.timestamp())
            job_id = f"rule_{rule.id}_at_{scheduled_ts}"

            # Use Redis SETNX as a distributed lock for this scheduled slot.
            # TTL of 120s covers execution time + next poll cycle.
            # If the key already exists, this slot was already enqueued — skip it.
            lock_key = f"rule_lock:{job_id}"
            acquired = redis_conn.set(lock_key, "1", nx=True, ex=120)
            if not acquired:
                logger.debug(f"Rule {rule.id} slot {scheduled_ts} already locked — skipping")
                continue

            try:
                queue.enqueue(
                    worker.check_campaign_rule,
                    rule.id,
                    job_id=job_id,
                    result_ttl=0,
                )
                logger.info(f"Enqueued rule {rule.id} ({rule.name}) — scheduled {rule.next_run_at}")
                enqueued += 1
            except Exception as e:
                logger.error(f"Failed to enqueue rule {rule.id}: {e}")
                # Release the lock so it can be retried on next poll
                redis_conn.delete(lock_key)

        if enqueued:
            logger.info(f"Enqueued {enqueued} due rules")

    except Exception as e:
        logger.error(f"Error in enqueue_due_rules: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == '__main__':
    logger.info("Starting rule scheduler (poll mode, interval=%ds)...", POLL_INTERVAL)

    while True:
        try:
            wait_for_redis()
            enqueue_due_rules()
            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except redis_lib.exceptions.ConnectionError as e:
            logger.error(f"Redis connection lost: {e} — will retry in 10s")
            time.sleep(10)
        except Exception as e:
            logger.error(f"Scheduler loop error: {e}", exc_info=True)
            time.sleep(5)
