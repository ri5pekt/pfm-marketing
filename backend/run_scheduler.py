#!/usr/bin/env python3
"""
Custom scheduler runner that patches rq-scheduler compatibility issues
"""
# Patch for rq-scheduler compatibility with newer rq versions
# Must be done before importing rq_scheduler
import rq
import rq.utils

# Create a dummy class if it doesn't exist
class ColorizingStreamHandler:
    pass

# Patch it before any rq_scheduler imports
rq.utils.ColorizingStreamHandler = ColorizingStreamHandler

# Now we can safely import rq_scheduler
from rq_scheduler import Scheduler
from app.core.config import settings
from app.jobs.queues import redis_conn
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Starting RQ Scheduler daemon...")
    scheduler = Scheduler(connection=redis_conn)
    
    # Run the scheduler loop manually
    while True:
        try:
            scheduler.run(burst=False)
            time.sleep(1)  # Check every second
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
            time.sleep(5)  # Wait before retrying

