## backend_py/run_worker.py
import os
import sys

# Ensure the current directory is in the python path
sys.path.append(os.getcwd())

# Import SimpleWorker instead of Worker
from rq import SimpleWorker, Queue
from app.queue import redis_conn
import nest_asyncio

# Apply nest_asyncio to allow async DB calls inside the worker
nest_asyncio.apply()

# Define the queues to listen to
listen = ['ai-evaluation']

if __name__ == '__main__':
    print(f"Worker listening on queues: {listen}")
    print("Running in SimpleWorker mode (Windows compatible)...")
    
    # Create Queue objects with the explicit Redis connection
    queues = [Queue(name, connection=redis_conn) for name in listen]
    
    # Use SimpleWorker for Windows support
    worker = SimpleWorker(queues, connection=redis_conn)
    
    # Start working
    worker.work()