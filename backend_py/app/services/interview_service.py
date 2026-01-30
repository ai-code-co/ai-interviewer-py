## backend_py/app/services/interview_service.py
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional,List
from ..config import get_supabase_client
from .ai_question_service import generate_interview_questions

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create_interview_session(candidate_id: str, job_id: str) -> Dict[str, Any]:
    supabase = get_supabase_client()
    
    # 1. Generate Questions if needed
    try:
        q_check = supabase.table("interview_questions").select("id").eq("job_id", job_id).execute()
        if not q_check.data:
            job_res = supabase.table("jobs").select("title, description").eq("id", job_id).single().execute()
            if job_res.data:
                print(f"Generating questions for Job {job_id}...")
                generate_interview_questions(job_id, job_res.data["title"], job_res.data["description"] or "")
    except Exception as e:
        print(f"Warning: Question generation check failed: {e}")

    # 2. Check Existing
    try:
        existing = supabase.table("interview_sessions").select("*").eq("candidate_id", candidate_id).eq("job_id", job_id).execute()
        if existing.data:
            session = existing.data[0]
            if not session.get("access_token"):
                new_token = str(uuid.uuid4())
                supabase.table("interview_sessions").update({"access_token": new_token}).eq("id", session["id"]).execute()
                session["access_token"] = new_token
            return session
    except Exception as e:
        print(f"Error checking session: {e}")

    # 3. Create New
    try:
        token = str(uuid.uuid4())
        res = supabase.table("interview_sessions").insert({
            "candidate_id": candidate_id,
            "job_id": job_id,
            "status": "PENDING",
            "access_token": token
        }).execute()
        
        if not res.data: raise RuntimeError("No data returned")
        return res.data[0]
    except Exception as e:
        raise RuntimeError(f"Failed to create session: {e}")

def get_session_by_token(token: str) -> Dict[str, Any]:
    supabase = get_supabase_client()
    try:
        # Return the session AND the last_question_id
        res = supabase.table("interview_sessions").select("*").eq("access_token", token).single().execute()
        return res.data
    except:
        return None

def get_next_question(job_id: str, last_question_id: Optional[str]) -> Optional[Dict[str, Any]]:
    supabase = get_supabase_client()
    try:
        if last_question_id:
            last_res = supabase.table("interview_questions").select("question_order").eq("id", last_question_id).single().execute()
            if not last_res.data: 
                # Fallback if ID is invalid (e.g. manual tampering), start from beginning
                return get_next_question(job_id, None)
                
            last_order = last_res.data["question_order"]
            
            res = supabase.table("interview_questions").select("*").eq("job_id", job_id).gt("question_order", last_order).order("question_order", desc=False).limit(1).execute()
        else:
            res = supabase.table("interview_questions").select("*").eq("job_id", job_id).order("question_order", desc=False).limit(1).execute()
            
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"Error getting question: {e}")
        return None

def save_interview_response(session_id: str, question_id: str, answer_text: str, answer_audio_url: Optional[str], answer_video_url: Optional[str]) -> Dict[str, Any]:
    supabase = get_supabase_client()
    try:
        # 1. Save Response
        res = supabase.table("interview_responses").insert({
            "session_id": session_id,
            "question_id": question_id,
            "answer_text": answer_text,
            "answer_audio_url": answer_audio_url,
            "answer_video_url": answer_video_url,
        }).execute()

        # 2. Update Progress (Anti-Cheating / Resume capability)
        supabase.table("interview_sessions").update({
            "last_question_id": question_id,
            "status": "IN_PROGRESS"
        }).eq("id", session_id).execute()

        return res.data[0]
    except Exception as e:
        raise RuntimeError(f"Failed to save response: {e}")

def fetch_interview_transcript(session_id: str) -> Optional[List[Dict[str, Any]]]:
    supabase = get_supabase_client()

    try:
        # fetch responses joined with the question details
        res = (
            supabase
            .table("interview_responses")
            .select("answer_text, interview_questions(question_text, expected_keywords)")
            .eq("session_id", session_id)
            .execute()
        )

       
        graded_input = []
        for r in (res.data or []):
            question_data = r.get("interview_questions") or {}
            graded_input.append({
                "question": question_data.get("question_text", "Unknown Question"),
                "keywords": question_data.get("expected_keywords", []), 
                "answer": r.get("answer_text", "[No Answer]")
            })
            
        return graded_input

    except Exception as e:
        print(f"Error fetching transcript for {session_id}: {e}")
        return None


def complete_interview_session(session_id: str, duration_seconds: Optional[int]) -> None:
    supabase = get_supabase_client()
    payload = {"status": "COMPLETED", "completed_at": _now_iso()}
    if duration_seconds is not None: payload["duration"] = f"{duration_seconds} seconds"
    try:
        supabase.table("interview_sessions").update(payload).eq("id", session_id).execute()
    except Exception as e:
        raise RuntimeError(f"Failed to complete session: {e}")
    
    
def get_job_description_by_sessionid(session_id: str) -> str:
    supabase = get_supabase_client()
    try:
       
        
        response = (
            supabase
            .table("interview_sessions")
            .select("jobs(title, description)") 
            .eq("id", session_id)
            .single() #  .single() returns a dict, not a list
            .execute()
        )
        
        
        # response.data looks like: { "jobs": { "title": "...", "description": "..." } }
        if response.data and response.data.get("jobs"):
            job_data = response.data.get("jobs")
            # Return a combined string or just the description
            return f"Role: {job_data.get('title')}\n\nDescription: {job_data.get('description')}"
            
        return ""

    except Exception as e:
        print(f"Error fetching job description for {session_id}: {e}")
        return ""
    
 