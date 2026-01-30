## backend_py/app/queue.py
from rq import Queue

from .config import get_redis_connection


redis_conn = get_redis_connection()

# AI Evaluation Queue (equivalent to BullMQ "ai-evaluation" queue)
ai_queue = Queue("ai-evaluation", connection=redis_conn)

