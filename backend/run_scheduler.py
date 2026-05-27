#!/usr/bin/env python3
"""
Custom scheduler runner that patches rq-scheduler compatibility issues
and automatically reseeds scheduled jobs from the database after any
Redis restart or connection loss.
"""
# Patch for rq-scheduler compatibility with newer rq versions
# Must be done before importing rq_scheduler
import rq
import rq.utils

class ColorizingStreamHandler:
    pass

rq.utils.ColorizingStreamHandler = ColorizingStreamHandler

from rq_scheduler import Scheduler
from app.jobs.queues import redis_conn
from app.features.meta_campaigns.scheduler_service import reschedule_all_rules
import redis as redis_lib
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def wait_for_redis(interval: int = 5):
    """Block until Redis responds to PING."""
    while True:
        try:
            redis_conn.ping()
            return
        except redis_lib.exceptions.ConnectionError:
            logger.warning(f"Redis not reachable, retrying in {interval}s...")
            time.sleep(interval)


if __name__ == '__main__':
    logger.info("Starting RQ Scheduler daemon...")

    # scheduler.py already seeded Redis on first boot — skip reseed on first iteration
    first_start = True

    while True:
        try:
            wait_for_redis()

            scheduler = Scheduler(connection=redis_conn)

            if not first_start:
                # Redis restarted (empty) or scheduler crashed — rebuild job registry from Postgres
                logger.warning("Scheduler restarting after failure — reseeding all rules from database...")
                reschedule_all_rules()
                logger.info("Reseed complete")

            first_start = False

            # Blocking call — exits only on exception
            scheduler.run(burst=False)

        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except redis_lib.exceptions.ConnectionError as e:
            logger.error(f"Redis connection lost: {e} — will retry in 10s")
            time.sleep(10)
        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
            time.sleep(5)
