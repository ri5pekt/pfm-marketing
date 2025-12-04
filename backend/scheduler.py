# Patch for rq-scheduler compatibility with newer rq versions
# Must be done before importing rq_scheduler
import rq.utils
if not hasattr(rq.utils, 'ColorizingStreamHandler'):
    # Create a dummy class if it doesn't exist
    class ColorizingStreamHandler:
        pass
    rq.utils.ColorizingStreamHandler = ColorizingStreamHandler

from app.features.meta_campaigns.scheduler_service import reschedule_all_rules
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Initializing scheduled rules...")
    reschedule_all_rules()
    logger.info("Scheduled rules initialized")

