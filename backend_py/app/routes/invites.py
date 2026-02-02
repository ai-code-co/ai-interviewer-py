## backend_py/app/routes/invites.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
import re
from secrets import token_urlsafe

from fastapi import APIRouter, HTTPException, Query, status, UploadFile, File

from ..config import get_settings, get_supabase_client
from ..services.email_service import send_invite_email, should_soft_fail_mailgun


router = APIRouter(prefix="/api/invites", tags=["invites"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def send_invite(payload: Dict[str, Any]) -> Dict[str, Any]:
    email = payload.get("email")
    issued_by = payload.get("issued_by")

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required")
    if not issued_by:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="issued_by (user ID) is required")

    email_regex = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    if not email_regex.match(email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")

    token = token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=48)
    settings = get_settings()
    
    # Generate the link for the candidate to Upload Resume
    invite_url = f"{settings.app_url.rstrip('/')}/{token}"

    # Send email
    try:
        send_invite_email(email, invite_url)
    except Exception as exc:
        msg = str(exc)
        if should_soft_fail_mailgun(msg):
            print(f"[mailgun] soft-fail, proceeding without send: {msg}")
        else:
            print("Error sending email:", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send invitation email. Please check Mailgun config.",
            ) from exc

    # Create application token record
    supabase = get_supabase_client()
    
    try:
        res = (
            supabase.table("application_tokens")
            .insert(
                {
                    "token": token,
                    "email": email,
                    "issued_by": issued_by,
                    "status": "PENDING",
                    "expires_at": expires_at.isoformat(),
                }
            )
            .execute()
        )
        
        # In new Supabase SDK, if execute() returns without raising exception, it is successful.
        # We just need to check if data is returned.
        if not res.data:
             raise RuntimeError("Database insertion returned no data")
             
    except Exception as exc:
        print(f"Error creating application token: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invitation email sent, but failed to save record in database.",
        )

    data = res.data[0] if isinstance(res.data, list) and res.data else res.data
    return {"success": True, "data": data}


@router.get("/")
async def get_invited_candidates(issued_by: str = Query(..., description="User ID who issued invites")) -> List[Dict]:
    supabase = get_supabase_client()
    try:
        res = (
            supabase.table("application_tokens")
            .select("*")
            .eq("issued_by", issued_by)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as exc:
        print(f"Error fetching tokens: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch invited candidates",
        )
        
    tokens = res.data or []
    now = datetime.now(timezone.utc)
    result: List[Dict[str, Any]] = []
    
    for token in tokens:
        expires_at = datetime.fromisoformat(token["expires_at"])
        is_expired = expires_at <= now
        final_status = token["status"]
        if token["status"] == "PENDING" and is_expired:
            final_status = "EXPIRED"
        
        has_applied = token["status"] == "USED"
        result.append(
            {
                "id": token["id"],
                "email": token["email"],
                "status": final_status,
                "created_at": token["created_at"],
                "expires_at": token["expires_at"],
                "used_at": token.get("used_at"),
                "has_applied": has_applied,
            }
        )
    return result


@router.get("/public/jobs")
async def get_public_jobs() -> List[Dict[str, Any]]:
    supabase = get_supabase_client()
    try:
        res = (
            supabase.table("jobs")
            .select("id, title, description")
            .eq("status", "open")
            .order("created_at", desc=True)
            .execute()
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch jobs")
        
    return res.data or []

@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def send_bulk_invites(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Accepts: { "emails": ["a@b.com", "c@d.com"], "issued_by": "uuid" }
    """
    emails = payload.get("emails", [])
    issued_by = payload.get("issued_by")
    
    if not emails or not issued_by:
        raise HTTPException(status_code=400, detail="Emails list and issued_by are required")

    settings = get_settings()
    supabase = get_supabase_client()
    results = {"success": 0, "failed": 0, "errors": []}

    for email in emails:
        # Simple validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            results["failed"] += 1
            continue

        try:
            token = token_urlsafe(32)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=48)
            invite_url = f"{settings.app_url.rstrip('/')}/apply?token={token}"

            # 1. Send Email
            send_invite_email(email, invite_url)

            # 2. Save to DB
            supabase.table("application_tokens").insert({
                "token": token,
                "email": email,
                "issued_by": issued_by,
                "status": "PENDING",
                "expires_at": expires_at.isoformat(),
            }).execute()
            
            results["success"] += 1
        except Exception as e:
            print(f"Failed to invite {email}: {e}")
            results["failed"] += 1
            results["errors"].append(f"{email}: {str(e)}")

    return results