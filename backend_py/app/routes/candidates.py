from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Body, HTTPException, Path

from ..config import get_settings
from ..db import fetch_all, fetch_one, from_json_db, execute
from ..services.ai_evaluation_service import normalize_ai_evaluation_row
from ..services.email_service import send_approval_email, send_offer_email, send_rejection_email
from ..services.interview_service import create_interview_session
from ..services.storage_service import get_resume_url


router = APIRouter(prefix="/api/candidates", tags=["candidates"])


@router.get("/")
async def get_candidates() -> List[Dict[str, Any]]:
    try:
        rows = fetch_all(
            """
            SELECT
                c.id, c.name, c.email, c.phone, c.created_at,
                j.id AS job_id, j.title AS job_title, j.description AS job_description
            FROM candidates c
            LEFT JOIN jobs j ON j.id = c.job_id
            ORDER BY c.created_at DESC
            """
        )
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "phone": row.get("phone"),
                "created_at": row["created_at"],
                "job": {
                    "id": row.get("job_id"),
                    "title": row.get("job_title"),
                    "description": row.get("job_description"),
                },
            }
            for row in rows
        ]
    except Exception as exc:  # noqa: BLE001
        print(f"Error fetching candidates: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{candidate_id}")
async def get_candidate_by_id(candidate_id: str = Path(...)) -> Dict[str, Any]:
    candidate = fetch_one(
        """
        SELECT
            c.*,
            j.id AS job_id_ref,
            j.title AS job_title,
            j.description AS job_description,
            j.status AS job_status,
            j.created_at AS job_created_at
        FROM candidates c
        LEFT JOIN jobs j ON j.id = c.job_id
        WHERE c.id = :candidate_id
        LIMIT 1
        """,
        {"candidate_id": candidate_id},
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    docs = []
    try:
        docs_res = fetch_all(
            "SELECT * FROM candidate_documents WHERE candidate_id = :candidate_id ORDER BY uploaded_at DESC",
            {"candidate_id": candidate_id},
        )
        for doc in docs_res:
            url = await get_resume_url(doc["storage_path"], doc["storage_bucket"])
            docs.append({**doc, "url": url})
    except Exception:
        pass

    evaluation_data = None
    try:
        eval_row = fetch_one(
            "SELECT * FROM ai_evaluations WHERE candidate_id = :candidate_id LIMIT 1",
            {"candidate_id": candidate_id},
        )
        evaluation_data = normalize_ai_evaluation_row(eval_row)
    except Exception:
        pass

    interview_data = None
    ai_interview_report = None
    try:
        session = fetch_one(
            """
            SELECT *
            FROM interview_sessions
            WHERE candidate_id = :candidate_id
            ORDER BY created_at DESC
            LIMIT 1
            """,
            {"candidate_id": candidate_id},
        )
        if session:
            ai_eval_res = fetch_one(
                "SELECT * FROM ai_interview_evaluations WHERE session_id = :session_id LIMIT 1",
                {"session_id": session["id"]},
            )
            if ai_eval_res:
                ai_interview_report = {
                    **ai_eval_res,
                    "matched_skills": from_json_db(ai_eval_res.get("matched_skills"), []),
                    "missing_skills": from_json_db(ai_eval_res.get("missing_skills"), []),
                    "strengths": from_json_db(ai_eval_res.get("strengths"), []),
                    "areas_for_improvement": from_json_db(ai_eval_res.get("areas_for_improvement"), []),
                }

            duration_value = session.get("duration")
            video_url = duration_value if isinstance(duration_value, str) and duration_value.startswith("http") else None
            transcript_url = session.get("transcript_url") if isinstance(session.get("transcript_url"), str) else None
            interview_data = {**session, "video_url": video_url, "transcript_url": transcript_url}
    except Exception as exc:  # noqa: BLE001
        print(f"Error fetching interview data: {exc}")

    job_payload = {
        "id": candidate.get("job_id_ref"),
        "title": candidate.get("job_title"),
        "description": candidate.get("job_description"),
        "status": candidate.get("job_status"),
        "created_at": candidate.get("job_created_at"),
    }

    return {
        **candidate,
        "job": job_payload,
        "documents": docs,
        "evaluation": evaluation_data,
        "interview": interview_data,
        "ai_interview_report": ai_interview_report,
    }


@router.put("/{candidate_id}/status")
async def update_candidate_status(candidate_id: str, body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    status_value = body.get("status")
    custom_message = body.get("customMessage") or ""

    if status_value not in ("APPROVED", "REJECTED", "PENDING"):
        raise HTTPException(status_code=400, detail="Invalid status")

    try:
        execute(
            """
            UPDATE candidates
            SET status = :status, status_updated_at = :updated_at
            WHERE id = :candidate_id
            """,
            {
                "status": status_value,
                "updated_at": datetime.utcnow(),
                "candidate_id": candidate_id,
            },
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Error updating status: {exc}")
        raise HTTPException(status_code=500, detail="Failed to update status") from exc

    candidate = None
    job_title = "Position"
    is_interview_done = False

    try:
        candidate = fetch_one(
            """
            SELECT
                c.*,
                j.id AS job_id_ref,
                j.title AS job_title
            FROM candidates c
            LEFT JOIN jobs j ON j.id = c.job_id
            WHERE c.id = :candidate_id
            LIMIT 1
            """,
            {"candidate_id": candidate_id},
        )
        if not candidate:
            raise RuntimeError("Candidate not found after status update")
        job_title = candidate.get("job_title") or "Position"

        rows = fetch_all(
            "SELECT status FROM interview_sessions WHERE candidate_id = :candidate_id",
            {"candidate_id": candidate_id},
        )
        is_interview_done = any(row.get("status") == "COMPLETED" for row in rows)
    except Exception as exc:  # noqa: BLE001
        return {"message": f"Status updated to {status_value}, but email failed.", "error": str(exc)}

    interview_link = ""
    try:
        if status_value == "APPROVED":
            if is_interview_done:
                send_offer_email(candidate["email"], job_title, custom_message)
            else:
                session = create_interview_session(candidate_id, candidate["job_id"])
                settings = get_settings()
                interview_link = f"{settings.app_url}/interview/{session['access_token']}"
                send_approval_email(candidate["email"], job_title, custom_message, interview_link)
        elif status_value == "REJECTED":
            send_rejection_email(candidate["email"], job_title, custom_message)
    except Exception as exc:  # noqa: BLE001
        print(f"Email sending error: {exc}")

    return {"message": f"Status updated to {status_value}", "interview_link": interview_link}
