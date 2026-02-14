from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from secrets import token_urlsafe
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status

from ..config import get_settings
from ..db import db_connection, execute, fetch_all, fetch_one
from ..services.email_service import send_invite_email, should_soft_fail_mailgun


router = APIRouter(prefix="/api/invites", tags=["invites"])


def _to_utc_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def send_invite(payload: Dict[str, Any]) -> Dict[str, Any]:
    email = payload.get("email")
    issued_by = payload.get("issued_by")

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required")

    email_regex = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    if not email_regex.match(email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")

    token = token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=48)
    settings = get_settings()
    invite_url = f"{settings.app_url.rstrip('/')}/apply?token={token}"

    token_id = str(uuid4())
    created_at = datetime.utcnow()
    try:
        with db_connection(transactional=True) as conn:
            execute(
                """
                INSERT INTO application_tokens (
                    id, token, email, issued_by, status, expires_at, created_at
                ) VALUES (
                    :id, :token, :email, :issued_by, 'PENDING', :expires_at, :created_at
                )
                """,
                {
                    "id": token_id,
                    "token": token,
                    "email": email,
                    "issued_by": issued_by,
                    "expires_at": expires_at,
                    "created_at": created_at,
                },
                conn=conn,
            )
            row = fetch_one(
                "SELECT * FROM application_tokens WHERE id = :id LIMIT 1",
                {"id": token_id},
                conn=conn,
            )
    except Exception as exc:  # noqa: BLE001
        print(f"Error creating application token: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save invitation record in database.",
        ) from exc

    try:
        send_invite_email(email, invite_url)
    except Exception as exc:  # noqa: BLE001
        msg = str(exc)
        if should_soft_fail_mailgun(msg):
            print(f"[mailgun] soft-fail, proceeding without send: {msg}")
        else:
            print("Error sending email:", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invitation saved, but failed to send email. Please check Mailgun config.",
            ) from exc

    return {"success": True, "data": row}


@router.get("/")
async def get_invited_candidates(issued_by: str = Query(..., description="User ID who issued invites")) -> List[Dict[str, Any]]:
    try:
        tokens = fetch_all(
            """
            SELECT *
            FROM application_tokens
            WHERE issued_by = :issued_by
            ORDER BY created_at DESC
            """,
            {"issued_by": issued_by},
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Error fetching tokens: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch invited candidates",
        ) from exc

    now = datetime.now(timezone.utc)
    result: List[Dict[str, Any]] = []

    for token in tokens:
        token_expires = token["expires_at"]
        expires_at = _to_utc_datetime(token_expires)
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
    try:
        return fetch_all(
            """
            SELECT id, title, description
            FROM jobs
            WHERE status = 'open'
            ORDER BY created_at DESC
            """
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Error fetching public jobs: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch jobs") from exc


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def send_bulk_invites(payload: Dict[str, Any]) -> Dict[str, Any]:
    emails = payload.get("emails", [])
    issued_by = payload.get("issued_by")

    if not emails or not issued_by:
        raise HTTPException(status_code=400, detail="Emails list and issued_by are required")

    settings = get_settings()
    results = {"success": 0, "failed": 0, "errors": []}

    for email in emails:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            results["failed"] += 1
            continue

        try:
            token = token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=48)
            invite_url = f"{settings.app_url.rstrip('/')}/apply?token={token}"
            execute(
                """
                INSERT INTO application_tokens (
                    id, token, email, issued_by, status, expires_at, created_at
                ) VALUES (
                    :id, :token, :email, :issued_by, 'PENDING', :expires_at, :created_at
                )
                """,
                {
                    "id": str(uuid4()),
                    "token": token,
                    "email": email,
                    "issued_by": issued_by,
                    "expires_at": expires_at,
                    "created_at": datetime.utcnow(),
                },
            )
            send_invite_email(email, invite_url)
            results["success"] += 1
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to invite {email}: {exc}")
            results["failed"] += 1
            results["errors"].append(f"{email}: {str(exc)}")

    return results
