from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError

from ..db import db_connection, execute, fetch_one
from ..queue import ai_queue
from ..services.ai_evaluation_service import create_pending_evaluation
from ..services.resume_parser_service import extract_resume_text
from ..services.storage_service import delete_media, upload_resume


router = APIRouter(prefix="/api/apply", tags=["apply"])


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    normalized = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


@router.get("/validate")
async def validate_token(token: str | None = None) -> Dict[str, Any]:
    if not token:
        return {"valid": False, "error": "Token is required"}

    try:
        data = fetch_one(
            """
            SELECT email, status, expires_at
            FROM application_tokens
            WHERE token = :token
            LIMIT 1
            """,
            {"token": token},
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error validating token: {exc}")
        return {"valid": False, "error": "Token is invalid"}

    if not data:
        return {"valid": False, "error": "Token is invalid"}
    if data["status"] != "PENDING":
        return {"valid": False, "error": "Token has already been used or expired"}

    expires_at = _parse_datetime(str(data["expires_at"]))
    now = datetime.now(timezone.utc)
    if expires_at <= now:
        execute("UPDATE application_tokens SET status = 'EXPIRED' WHERE token = :token", {"token": token})
        return {"valid": False, "error": "Token has expired"}

    return {"valid": True, "email": data["email"]}


@router.post("/submit", status_code=status.HTTP_201_CREATED)
async def submit_application(
    name: str = Form(...),
    email: str = Form(...),
    job_id: str = Form(...),
    phone: str | None = Form(None),
    resume: UploadFile = File(...),
    token_form: str | None = Form(None),
    x_application_token: str | None = Header(None),
) -> Dict[str, Any]:
    token = x_application_token or token_form
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Application token is required")

    token_data = fetch_one(
        """
        SELECT email, status, expires_at
        FROM application_tokens
        WHERE token = :token
        LIMIT 1
        """,
        {"token": token},
    )
    if not token_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid application token")

    if token_data["status"] != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has already been used or expired",
        )

    expires_at = _parse_datetime(str(token_data["expires_at"]))
    now = datetime.now(timezone.utc)
    if expires_at <= now:
        execute("UPDATE application_tokens SET status = 'EXPIRED' WHERE token = :token", {"token": token})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation has expired")

    if email != token_data["email"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email mismatch. Please use the email from your invitation.",
        )
    if not name or not job_id or resume is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name, job selection, and resume are required",
        )

    allowed_types = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    if resume.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload PDF or Word document.",
        )
    max_size = 5 * 1024 * 1024
    file_bytes = await resume.read()
    if len(file_bytes) > max_size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size must be less than 5MB")

    parsed_resume_text: str | None = None
    try:
        parsed_resume_text = extract_resume_text(
            file_bytes,
            resume.filename or "resume.pdf",
        ).text
    except Exception as exc:  # noqa: BLE001
        # Non-fatal: worker can still try URL-based fallback
        print("Resume text pre-parse failed, worker will fallback to file fetch:", repr(exc))

    candidate_id = str(uuid4())
    candidate = None
    try:
        with db_connection(transactional=True) as conn:
            execute(
                """
                INSERT INTO candidates (
                    id, job_id, name, email, phone, created_at, status
                ) VALUES (
                    :id, :job_id, :name, :email, :phone, :created_at, 'PENDING'
                )
                """,
                {
                    "id": candidate_id,
                    "job_id": job_id,
                    "name": name.strip(),
                    "email": token_data["email"],
                    "phone": phone.strip() if phone else None,
                    "created_at": datetime.utcnow(),
                },
                conn=conn,
            )
            candidate = fetch_one("SELECT * FROM candidates WHERE id = :id LIMIT 1", {"id": candidate_id}, conn=conn)
    except IntegrityError as exc:
        err = str(exc).lower()
        if "1062" in err or "duplicate" in err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already applied for this position. We have your previous application on file.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create application record.",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create application record. Internal Error.",
        ) from exc

    if not candidate:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database returned no data.")

    upload_result: Dict[str, Any] = {}
    try:
        upload_result = await upload_resume(
            file_bytes=file_bytes,
            file_name=resume.filename or "resume.pdf",
            file_type=resume.content_type or "application/octet-stream",
            candidate_id=str(candidate["id"]),
        )
    except Exception as exc:  # noqa: BLE001
        print("Error uploading resume:", repr(exc))
        execute("DELETE FROM candidates WHERE id = :id", {"id": candidate["id"]})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload resume: {exc}",
        ) from exc

    try:
        execute(
            """
            INSERT INTO candidate_documents (
                id, candidate_id, storage_bucket, storage_path, file_hash, uploaded_at
            ) VALUES (
                :id, :candidate_id, :storage_bucket, :storage_path, :file_hash, :uploaded_at
            )
            """,
            {
                "id": str(uuid4()),
                "candidate_id": candidate["id"],
                "storage_bucket": "cloudinary",
                "storage_path": upload_result["path"],
                "file_hash": upload_result["hash"],
                "uploaded_at": datetime.utcnow(),
            },
        )
    except Exception as exc:  # noqa: BLE001
        print("Error creating document record:", exc)
        execute("DELETE FROM candidates WHERE id = :id", {"id": candidate["id"]})
        public_id = upload_result.get("public_id")
        if public_id:
            try:
                await delete_media(public_id, upload_result.get("resource_type", "raw"))
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document information",
        ) from exc

    execute(
        """
        UPDATE application_tokens
        SET status = 'USED', used_at = :used_at
        WHERE token = :token
        """,
        {
            "used_at": datetime.utcnow(),
            "token": token,
        },
    )

    try:
        await create_pending_evaluation(str(candidate["id"]))
    except Exception as exc:  # noqa: BLE001
        print("Failed to create pending evaluation row:", repr(exc))

    try:
        ai_queue.enqueue(
            "app.workers.ai_evaluation_worker.process_evaluation_job",
            candidate_id=str(candidate["id"]),
            job_id=str(job_id),
            resume_path=upload_result["path"],
            storage_bucket="cloudinary",
            resume_public_id=upload_result.get("public_id"),
            resume_resource_type=upload_result.get("resource_type", "raw"),
            resume_text=parsed_resume_text,
            job_timeout=600,
        )
        print(f"[API] Enqueued AI evaluation job for candidate {candidate['id']}")
    except Exception as exc:  # noqa: BLE001
        print("Failed to enqueue AI evaluation job:", exc)

    return {"success": True, "message": "Application submitted successfully"}
