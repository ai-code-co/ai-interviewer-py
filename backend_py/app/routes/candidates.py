## backend_py/app/routes/candidates.py
from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime, timezone
import os
from fastapi import APIRouter, Body, HTTPException, Path, status
from ..config import get_supabase_client, get_settings
from ..services.email_service import send_approval_email, send_rejection_email, send_offer_email
from ..services.storage_service import get_resume_url
from ..services.interview_service import create_interview_session

router = APIRouter(prefix="/api/candidates", tags=["candidates"])

@router.get("/")
async def get_candidates() -> List[Dict[str, Any]]:
    supabase = get_supabase_client()
    try:
        res = supabase.table("candidates").select("id, name, email, phone, created_at, jobs (id, title, description)").order("created_at", desc=True).execute()
        return [{
            "id": c["id"],
            "name": c["name"],
            "email": c["email"],
            "phone": c.get("phone"),
            "created_at": c["created_at"],
            "job": c.get("jobs", {})
        } for c in (res.data or [])]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{candidate_id}")
async def get_candidate_by_id(candidate_id: str = Path(...)) -> Dict[str, Any]:
    supabase = get_supabase_client()
    settings = get_settings()
    
    # 1. Fetch Candidate
    try:
        res = supabase.table("candidates").select("*, jobs(*)").eq("id", candidate_id).single().execute()
    except: raise HTTPException(status_code=404, detail="Candidate not found")
    candidate = res.data

    # 2. Fetch Documents (Cloud)
    docs = []
    try:
        docs_res = supabase.table("candidate_documents").select("*").eq("candidate_id", candidate_id).execute()
        for d in (docs_res.data or []):
            url = await get_resume_url(d["storage_path"], d["storage_bucket"])
            docs.append({**d, "url": url})
    except: pass

    # 3. Fetch Resume Evaluation
    evaluation_data = None
    try:
        eval_res = supabase.table("ai_evaluations").select("*").eq("candidate_id", candidate_id).maybe_single().execute()
        evaluation_data = eval_res.data
    except: pass

    # 4. Fetch Interview Data (Hybrid + Your AI Report Logic)
    interview_data = None
    ai_interview_report = None 

    try:
        sess_res = supabase.table("interview_sessions").select("*").eq("candidate_id", candidate_id).maybe_single().execute()
        if sess_res.data:
            session = sess_res.data
            session_id = session["id"]
            
            # --- YOUR CUSTOM AI REPORT LOGIC ---
            try:
                ai_eval_res = supabase.table("ai_interview_evaluations")\
                    .select("*")\
                    .eq("session_id", session_id)\
                    .maybe_single()\
                    .execute()
                ai_interview_report = ai_eval_res.data
            except Exception as eval_err:
                print(f"Error fetching AI interview analysis: {eval_err}")
            # -----------------------------------

            video_url = None
            pdf_url = None
            
            # A. FIND VIDEO (Local Disk)
            upload_dir = os.path.join(os.getcwd(), "local_uploads")
            if os.path.exists(upload_dir):
                for filename in os.listdir(upload_dir):
                    if filename.startswith(session_id) and (filename.endswith(".webm") or filename.endswith(".mp4")):
                        video_url = f"{settings.app_url}/uploads/{filename}"
                        break
            
            # B. FIND PDF (Supabase Cloud - Bucket: interview-transcripts)
            try:
                # We list files in the bucket folder {session_id}/
                # Because we saved it as: session_id/question_id.pdf
                # Or specifically "transcript.pdf" from frontend upload
                p_list = supabase.storage.from_("interview-transcripts").list(session_id)
                if p_list:
                    for f in p_list:
                        if f['name'].endswith('.pdf'):
                            pdf_url = supabase.storage.from_("interview-transcripts").get_public_url(f"{session_id}/{f['name']}")
                            break
            except Exception as e:
                print(f"Error checking cloud transcripts: {e}")

            interview_data = {
                **session,
                "video_url": video_url,
                "transcript_url": pdf_url,
                "ai_report": ai_interview_report # Including your report here
            }
    except Exception as e:
        print(f"Error fetching interview data: {e}")

    return {
        **candidate,
        "job": candidate.get("jobs", {}),
        "documents": docs,
        "evaluation": evaluation_data,
        "interview": interview_data
    }

# ... (Keep update_candidate_status exactly as is) ...
@router.put("/{candidate_id}/status")
async def update_candidate_status(candidate_id: str, body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    status_value = body.get("status")
    custom_message = body.get("customMessage") or ""
    
    if status_value not in ("APPROVED", "REJECTED", "PENDING"):
        raise HTTPException(status_code=400, detail="Invalid status")

    supabase = get_supabase_client()
    try:
        supabase.table("candidates").update({
            "status": status_value,
            "status_updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", candidate_id).execute()
    except:
        raise HTTPException(status_code=500, detail="Failed to update status")

    candidate = None
    job_title = "Position"
    is_interview_done = False

    try:
        res = supabase.table("candidates").select("*, jobs(*)").eq("id", candidate_id).single().execute()
        candidate = res.data
        job_title = candidate.get("jobs", {}).get("title", "Position")
        try:
            int_res = supabase.table("interview_sessions").select("status").eq("candidate_id", candidate_id).execute()
            if int_res.data:
                for session in int_res.data:
                    if session.get("status") == "COMPLETED":
                        is_interview_done = True
                        break
        except: is_interview_done = False
    except:
        return {"message": "Status updated, email failed."}
    
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
    except Exception as e:
        print(f"Email error: {e}")

    return {"message": f"Status updated to {status_value}", "interview_link": interview_link}