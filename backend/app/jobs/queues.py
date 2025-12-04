from redis import Redis
from rq import Queue
from app.core.config import settings

redis_conn = Redis.from_url(settings.REDIS_URL)

def get_queue(name="default"):
    return Queue(name, connection=redis_conn)

