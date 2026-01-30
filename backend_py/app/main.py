## backend_py/app/main.py
from __future__ import annotations
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles # <--- IMPORT THIS

from .config import get_settings
from .routes import apply, candidates, invites, jobs, interview


settings = get_settings()

app = FastAPI(title="AI Interviewer Python Backend", version="1.0.0")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Make errors compatible with the existing frontend, which expects { error: ... }
    detail = exc.detail
    if isinstance(detail, str):
        payload = {"error": detail}
    elif isinstance(detail, dict) and "error" in detail:
        payload = detail
    else:
        payload = {"error": str(detail)}
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Avoid leaking internals to the client, but keep it debuggable via server logs
    print("[unhandled]", repr(exc))
    return JSONResponse(status_code=500, content={"error": "Internal server error"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MOUNT LOCAL UPLOADS FOLDER
upload_dir = os.path.join(os.getcwd(), "local_uploads")
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

@app.get("/health")
async def health():
    from datetime import datetime, timezone
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

app.include_router(jobs.router)
app.include_router(invites.router)
app.include_router(candidates.router)
app.include_router(apply.router)
app.include_router(interview.router)