## backend_py/app/routes/jobs.py
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status

from ..config import get_supabase_client


router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/", response_model=List[Dict[str, Any]])
async def get_jobs() -> List[Dict[str, Any]]:
    supabase = get_supabase_client()
    res = supabase.table("jobs").select("*").order("created_at", desc=True).execute()
    err = getattr(res, "error", None)
    if err or (getattr(res, "status_code", 200) >= 400):
        print("Error fetching jobs:", err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch jobs")
    return res.data or []


@router.get("/{job_id}")
async def get_job_by_id(job_id: str) -> Dict[str, Any]:
    supabase = get_supabase_client()
    res = supabase.table("jobs").select("*").eq("id", job_id).single().execute()
    err = getattr(res, "error", None)
    if err or not res.data or (getattr(res, "status_code", 200) >= 400):
        print("Error fetching job:", err)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return res.data


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    title = payload.get("title")
    description = payload.get("description")
    status_value = payload.get("status")

    if not title or not status_value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title and status are required")
    if status_value not in ("open", "closed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'open' or 'closed'",
        )

    supabase = get_supabase_client()
    res = (
        supabase.table("jobs")
        .insert(
            {
                "title": title,
                "description": description or None,
                "status": status_value,
            }
        )
        .execute()
    )
    err = getattr(res, "error", None)
    if err or (getattr(res, "status_code", 200) >= 400):
        print("Error creating job:", err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create job")
    data = res.data[0] if isinstance(res.data, list) and res.data else res.data
    return data


@router.put("/{job_id}")
async def update_job(job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    title = payload.get("title")
    description = payload.get("description")
    status_value = payload.get("status")

    if not title or not status_value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title and status are required")
    if status_value not in ("open", "closed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'open' or 'closed'",
        )

    supabase = get_supabase_client()
    res = (
        supabase.table("jobs")
        .update(
            {
                "title": title,
                "description": description or None,
                "status": status_value,
            }
        )
        .eq("id", job_id)
        .execute()
    )
    err = getattr(res, "error", None)
    if err or (getattr(res, "status_code", 200) >= 400):
        print("Error updating job:", err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update job")
    data = res.data[0] if isinstance(res.data, list) and res.data else res.data
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return data


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: str) -> None:
    supabase = get_supabase_client()
    res = supabase.table("jobs").delete().eq("id", job_id).execute()
    err = getattr(res, "error", None)
    if err or (getattr(res, "status_code", 200) >= 400):
        print("Error deleting job:", err)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete job")
    return None

