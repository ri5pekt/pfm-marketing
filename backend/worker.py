import redis
from rq import Worker, Queue, Connection
from app.core.config import settings
from app.jobs.queues import redis_conn

if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker(["default"])
        worker.work()

