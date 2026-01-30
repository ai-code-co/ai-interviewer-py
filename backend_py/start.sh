#!/bin/bash
pip install rq

# 1. Start the Worker in the background
python run_worker.py &

# 2. Start the API in the foreground
uvicorn app.main:app --host 0.0.0.0 --port $PORT