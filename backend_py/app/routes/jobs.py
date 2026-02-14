from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from ..db import db_connection, execute, fetch_all, fetch_one


router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _now_db() -> datetime:
    return datetime.utcnow()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_jobs() -> List[Dict[str, Any]]:
    try:
        return fetch_all("SELECT * FROM jobs ORDER BY created_at DESC")
    except Exception as exc:  # noqa: BLE001
        print("Error fetching jobs:", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch jobs") from exc


@router.get("/{job_id}")
async def get_job_by_id(job_id: str) -> Dict[str, Any]:
    try:
        row = fetch_one("SELECT * FROM jobs WHERE id = :job_id LIMIT 1", {"job_id": job_id})
    except Exception as exc:  # noqa: BLE001
        print("Error fetching job:", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch job") from exc
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return row


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    title = payload.get("title")
    description = payload.get("description")
    status_value = payload.get("status")

    if not title or not status_value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title and status are required")
    if status_value not in ("open", "closed"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be 'open' or 'closed'")

    job_id = str(uuid4())
    created_at = _now_db()
    try:
        with db_connection(transactional=True) as conn:
            execute(
                """
                INSERT INTO jobs (id, title, description, status, created_at)
                VALUES (:id, :title, :description, :status, :created_at)
                """,
                {
                    "id": job_id,
                    "title": title,
                    "description": description or None,
                    "status": status_value,
                    "created_at": created_at,
                },
                conn=conn,
            )
            row = fetch_one("SELECT * FROM jobs WHERE id = :job_id LIMIT 1", {"job_id": job_id}, conn=conn)
    except Exception as exc:  # noqa: BLE001
        print("Error creating job:", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create job") from exc
    if not row:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create job")
    return row


@router.put("/{job_id}")
async def update_job(job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    title = payload.get("title")
    description = payload.get("description")
    status_value = payload.get("status")

    if not title or not status_value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title and status are required")
    if status_value not in ("open", "closed"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be 'open' or 'closed'")

    try:
        with db_connection(transactional=True) as conn:
            result = execute(
                """
                UPDATE jobs
                SET title = :title, description = :description, status = :status
                WHERE id = :job_id
                """,
                {
                    "title": title,
                    "description": description or None,
                    "status": status_value,
                    "job_id": job_id,
                },
                conn=conn,
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
            row = fetch_one("SELECT * FROM jobs WHERE id = :job_id LIMIT 1", {"job_id": job_id}, conn=conn)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        print("Error updating job:", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update job") from exc
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return row


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: str) -> None:
    try:
        with db_connection(transactional=True) as conn:
            execute("DELETE FROM jobs WHERE id = :job_id", {"job_id": job_id}, conn=conn)
    except Exception as exc:  # noqa: BLE001
        print("Error deleting job:", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete job") from exc
    return None
