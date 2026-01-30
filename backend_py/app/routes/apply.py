## backend_py/app/routes/apply.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import (
    APIRouter,
    File,
    Form,
    Header,
    HTTPException,
    UploadFile,
    status,
)

from postgrest.exceptions import APIError

from ..config import get_supabase_admin_client, get_supabase_client
from ..queue import ai_queue
from ..services.storage_service import upload_resume
from ..services.ai_evaluation_service import create_pending_evaluation


router = APIRouter(prefix="/api/apply", tags=["apply"])


@router.get("/validate")
async def validate_token(token: str | None = None) -> Dict[str, Any]:
    if not token:
        return {"valid": False, "error": "Token is required"}

    supabase = get_supabase_client()
    try:
        res = (
            supabase.table("application_tokens")
            .select("email, status, expires_at")
            .eq("token", token)
            .single()
            .execute()
        )
        err = getattr(res, "error", None)
        if err or not res.data or (getattr(res, "status_code", 200) >= 400):
            return {"valid": False, "error": "Token is invalid"}

        data = res.data
    except APIError as exc:
        # Handle case where token doesn't exist (PGRST116 = no rows found)
        if isinstance(exc.args[0], dict) and exc.args[0].get("code") == "PGRST116":
            return {"valid": False, "error": "Token is invalid"}
        # Log other API errors but still return invalid
        print(f"Error validating token: {exc}")
        return {"valid": False, "error": "Token is invalid"}
        
    except Exception as exc:
        print(f"Unexpected error validating token: {exc}")
        return {"valid": False, "error": "Token is invalid"}

    if data["status"] != "PENDING":
        return {"valid": False, "error": "Token has already been used or expired"}

    expires_at = datetime.fromisoformat(data["expires_at"])
    now = datetime.now(timezone.utc)
    if expires_at <= now:
        supabase.table("application_tokens").update({"status": "EXPIRED"}).eq("token", token).execute()
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

    supabase = get_supabase_client()

    # Step 1: validate token
    try:
        token_res = (
            supabase.table("application_tokens")
            .select("email, status, expires_at")
            .eq("token", token)
            .single()
            .execute()
        )
        token_err = getattr(token_res, "error", None)
        if token_err or not token_res.data or (getattr(token_res, "status_code", 200) >= 400):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid application token")
        token_data = token_res.data
    except APIError as exc:
        # Handle case where token doesn't exist (PGRST116 = no rows found)
        if isinstance(exc.args[0], dict) and exc.args[0].get("code") == "PGRST116":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid application token") from exc
        # Re-raise other API errors
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {exc}") from exc

    if token_data["status"] != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has already been used or expired",
        )

    expires_at = datetime.fromisoformat(token_data["expires_at"])
    now = datetime.now(timezone.utc)
    if expires_at <= now:
        supabase.table("application_tokens").update({"status": "EXPIRED"}).eq("token", token).execute()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation has expired")

    # Step 2: parse form data
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 5MB",
        )

    # Step 3: create candidate (Robust Error Handling)
    candidate = None
    try:
        candidate_res = (
            supabase.table("candidates")
            .insert(
                {
                    "job_id": job_id,
                    "name": name.strip(),
                    "email": token_data["email"],
                    "phone": phone.strip() if phone else None,
                }
            )
            .execute()
        )
        
        # Check for errors returned in the response object (not raised as exceptions)
        cand_err = getattr(candidate_res, "error", None)
        if cand_err:
            # Convert error to string to check for duplicate key (23505)
            err_str = str(cand_err).lower()
            err_code = ""
            if isinstance(cand_err, dict):
                err_code = str(cand_err.get("code", ""))
            elif hasattr(cand_err, "code"):
                err_code = str(cand_err.code)

            if "23505" in err_str or "23505" in err_code or "duplicate key" in err_str:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You have already applied for this position. We have your previous application on file.",
                )
            
            # Generic DB error
            print(f"Database Error (Response): {cand_err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create application record.",
            )

        if not candidate_res.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database returned no data.",
            )
            
        candidate = candidate_res.data[0]

    except HTTPException:
        raise # Re-raise HTTP exceptions defined above
    except Exception as exc:
        # Catch Exceptions raised by the client (APIError, etc.)
        error_str = str(exc).lower()
        
        # Check for Postgres unique violation code 23505
        if "23505" in error_str or "duplicate key" in error_str:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already applied for this position. We have your previous application on file.",
            )
        
        # Log unexpected errors
        print(f"Database Exception: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create application record. Internal Error.",
        )

    # Step 4: upload resume
    try:
        upload_result = await upload_resume(
            file_bytes=file_bytes,
            file_name=resume.filename or "resume.pdf",
            file_type=resume.content_type or "application/octet-stream",
            candidate_id=str(candidate["id"]),
        )
    except Exception as exc:  # noqa: BLE001
        print("Error uploading resume:", repr(exc))
        # Cleanup candidate if resume upload fails
        supabase.table("candidates").delete().eq("id", candidate["id"]).execute()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload resume: {exc}",
        ) from exc

    # Step 5: candidate_documents record
    doc_res = (
        supabase.table("candidate_documents")
        .insert(
            {
                "candidate_id": candidate["id"],
                "storage_bucket": "resumes",
                "storage_path": upload_result["path"],
                "file_hash": upload_result["hash"],
            }
        )
        .execute()
    )
    doc_err = getattr(doc_res, "error", None)
    if doc_err or (getattr(doc_res, "status_code", 200) >= 400):
        print("Error creating document record:", doc_err)
        # Cleanup
        supabase.table("candidates").delete().eq("id", candidate["id"]).execute()
        supabase_admin = get_supabase_admin_client()
        if supabase_admin:
            supabase_admin.storage.from_("resumes").remove([upload_result["path"]])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document information",
        )

    # Step 6: mark token as USED
    supabase.table("application_tokens").update(
        {
            "status": "USED",
            "used_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("token", token).execute()

    # Step 7a: create pending AI evaluation row so UI can immediately reflect queued status
    try:
        await create_pending_evaluation(str(candidate["id"]))
    except Exception as exc:  # noqa: BLE001
        # Non-fatal; worker can still create row later
        print("Failed to create pending evaluation row:", repr(exc))

    # Step 7b: enqueue AI evaluation job
    try:
        ai_queue.enqueue(
            "app.workers.ai_evaluation_worker.process_evaluation_job",
            candidate_id=str(candidate["id"]),
            job_id=str(job_id),
            resume_path=upload_result["path"],
            storage_bucket="resumes",
            job_timeout=600,
        )
        print(f"[API] Enqueued AI evaluation job for candidate {candidate['id']}")
    except Exception as exc:  # noqa: BLE001
        print("Failed to enqueue AI evaluation job:", exc)

    return {"success": True, "message": "Application submitted successfully"}