## backend_py/flush_redis.py
import sys
import os
sys.path.append(os.getcwd())

from app.queue import redis_conn

print("Flushing all jobs from Redis...")
redis_conn.flushall()
print("Done! Redis is clean.")