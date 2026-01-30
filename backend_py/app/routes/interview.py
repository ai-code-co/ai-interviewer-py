from __future__ import annotations
from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, HTTPException, status, UploadFile, File, Form
from ..services.interview_service import (
    complete_interview_session,
    create_interview_session,
    get_next_question,
    save_interview_response,
    get_session_by_token,
   
)
from ..services.interview_grader_service import grade_interview_session,save_evaluation_to_db
from ..services.tts_service import generate_question_audio
from ..services.storage_service import upload_interview_media
from ..services.storage_service import upload_interview_media as upload_audio
import os
from ..services.transcription_service import transcribe_audio_chunk
from pathlib import Path
router = APIRouter(prefix="/api/interview", tags=["interview"])

@router.get("/validate/{token}")
async def validate_token(token: str):
    session = get_session_by_token(token)
    if not session:
        raise HTTPException(status_code=404, detail="Invalid interview link")
    if session["status"] == "COMPLETED":
        # Optional: Allow viewing completed session? For now block it.
        # raise HTTPException(status_code=400, detail="Interview already completed")
        pass 
    return session

@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_interview(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    candidate_id = payload.get("candidate_id")
    job_id = payload.get("job_id")
    if not candidate_id or not job_id:
        raise HTTPException(status_code=400, detail="Missing IDs")
    try:
        session = create_interview_session(candidate_id, job_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"session": session}

@router.post("/question", status_code=status.HTTP_200_OK)
async def get_question(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    job_id = payload.get("job_id")
    last_question_id: Optional[str] = payload.get("last_question_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    question = get_next_question(job_id, last_question_id)
    if not question:
        return {"question": None, "done": True}
    
    # Generate Audio
    audio_b64 = generate_question_audio(question["question_text"])
    return {"question": question, "audio_base64": audio_b64, "done": False}

@router.post("/answer", status_code=status.HTTP_201_CREATED)
async def submit_answer(
    session_id: str = Form(...),
    question_id: str = Form(...),
    # We now accept an AUDIO file specifically for transcription
    audio_chunk: UploadFile = File(...), 
) -> Dict[str, Any]:
    
    try:
        # 1. Read Audio
        file_bytes = await audio_chunk.read()
    
        # 2. Transcribe (High Quality Whisper)
        print("⏳ Transcribing with Whisper...")
        print("73 file bytes",file_bytes)
        transcript_text = transcribe_audio_chunk(file_bytes)
        print(f"✅ Transcript: {transcript_text[:50]}...")

        # 3. Save to DB (We store the high-quality text)
        # We pass None for video_url here because the FULL video is uploaded at the end.
        # We only care about the TEXT for this specific question.
        save_interview_response(session_id, question_id, transcript_text, None, None)
    
        return {"success": True, "transcript": transcript_text}
    except  Exception as e:
        print(f"Error at answer route: {e}")

@router.post("/complete", status_code=status.HTTP_200_OK)
async def complete_interview(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Mark as completed in DB
    complete_interview_session(session_id, None)
    
    # Judging Agent
    
    current_file = Path(__file__).resolve()
    
    # the structure: backend_py/app/.../interview.py
    # want to get to: backend_py/local_uploads
    
    # Navigate up until we find the folder that contains 'local_uploads'
    # This loop looks at parents until it finds the root 'backend_py' folder
    backend_root = current_file.parent
    while backend_root.name != "backend_py" and backend_root.parent != backend_root:
        backend_root = backend_root.parent
        
    # path to uploads
    uploads_dir = backend_root / "local_uploads"
    
    print(f"Looking for uploads in: {uploads_dir}")

    target_file = None
    if uploads_dir.exists():
        # Iterate over 
        for file_path in uploads_dir.glob("*.pdf"):
            if session_id in file_path.name:
                target_file = file_path.name
                break
    
    if target_file:
        # Convert Path object back to string 
        pdf_path = str(uploads_dir / target_file)
    else:
        # Fallback for testing
        pdf_filename = "d0cda0a8-ec88-4900-8bd4-9b0555ce3fc4_TRANSCRIPT_802bbce0-1026-47ef-93b5-924a532cb488.pdf"
        pdf_path = str(uploads_dir / pdf_filename)

    print(f"Final PDF Path: {pdf_path}")

    try:
        grading_result = await grade_interview_session(session_id, pdf_path=pdf_path)

        if "error" not in grading_result:
            save_success = save_evaluation_to_db(session_id, grading_result)
            if not save_success:
                print("Warning: Failed to save to database, but AI generation worked.")

        # 3. RETURN RESPONSE
        return {"success": True, "grade": grading_result}
    except Exception as e:
         return {"success": False, "grading_error": str(e)}
   
    
@router.post("/upload-full-video", status_code=status.HTTP_201_CREATED)
async def upload_full_video(
    session_id: str = Form(...),
    video: UploadFile = File(...)
) -> Dict[str, Any]:
    try:
        file_bytes = await video.read()
        # We pass "full_session" as the question_id to identify it
        url = await upload_audio(file_bytes, session_id, "FULL_SESSION_RECORDING", media_type="video")
        
        # Optionally: Update the session with this URL
        from ..config import get_supabase_client
        supabase = get_supabase_client()
        # We store this url in the 'duration' field or a new column for simplicity
        supabase.table("interview_sessions").update({"duration": url}).eq("id", session_id).execute()
        
        return {"success": True, "url": url}
    except Exception as e:
        print(f"Full video upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload full video")
    
@router.post("/upload-transcript", status_code=status.HTTP_201_CREATED)
async def upload_transcript(
    session_id: str = Form(...),
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    try:
        file_bytes = await file.read()
        # Save locally using the existing storage logic, treating it as a 'file'
        # We assume 'video' logic works fine for any file saving in local setup
        url = await upload_audio(file_bytes, session_id, "TRANSCRIPT", media_type="pdf")
        return {"success": True, "url": url}
    except Exception as e:
        print(f"Transcript upload error: {e}")
        # Don't crash the whole flow if PDF fails
        return {"success": False, "error": str(e)}