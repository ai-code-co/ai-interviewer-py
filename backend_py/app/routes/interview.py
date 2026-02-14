from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, File, Form, HTTPException, UploadFile, status

from ..db import execute
from ..services.interview_grader_service import grade_interview_session, save_evaluation_to_db
from ..services.interview_service import (
    complete_interview_session,
    create_interview_session,
    get_next_question,
    get_session_by_token,
    save_interview_response,
)
from ..services.storage_service import upload_interview_media
from ..services.transcription_service import transcribe_audio_chunk
from ..services.tts_service import generate_question_audio


router = APIRouter(prefix="/api/interview", tags=["interview"])


@router.get("/validate/{token}")
async def validate_token(token: str):
    session = get_session_by_token(token)
    if not session:
        raise HTTPException(status_code=404, detail="Invalid interview link")
    return session


@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_interview(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    candidate_id = payload.get("candidate_id")
    job_id = payload.get("job_id")
    if not candidate_id or not job_id:
        raise HTTPException(status_code=400, detail="Missing IDs")
    try:
        session = create_interview_session(candidate_id, job_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
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

    audio_b64 = generate_question_audio(question["question_text"])
    return {"question": question, "audio_base64": audio_b64, "done": False}


@router.post("/answer", status_code=status.HTTP_201_CREATED)
async def submit_answer(
    session_id: str = Form(...),
    question_id: str = Form(...),
    audio_chunk: UploadFile = File(...),
) -> Dict[str, Any]:
    try:
        file_bytes = await audio_chunk.read()
        transcript_text = transcribe_audio_chunk(file_bytes)
        save_interview_response(session_id, question_id, transcript_text, None, None)
        return {"success": True, "transcript": transcript_text}
    except Exception as exc:  # noqa: BLE001
        print(f"Error at answer route: {exc}")
        raise HTTPException(status_code=500, detail="Failed to save answer") from exc


@router.post("/complete", status_code=status.HTTP_200_OK)
async def complete_interview(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    complete_interview_session(session_id, None)
    try:
        grading_result = await grade_interview_session(session_id=session_id, pdf_path=None)
        if "error" not in grading_result:
            save_success = save_evaluation_to_db(session_id, grading_result)
            if not save_success:
                print("Warning: Failed to save to database, but AI generation worked.")
        return {"success": True, "grade": grading_result}
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "grading_error": str(exc)}


@router.post("/upload-full-video", status_code=status.HTTP_201_CREATED)
async def upload_full_video(session_id: str = Form(...), video: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        file_bytes = await video.read()
        url = await upload_interview_media(file_bytes, session_id, "FULL_SESSION_RECORDING", media_type="video")
        execute(
            "UPDATE interview_sessions SET duration = :url WHERE id = :session_id",
            {"url": url, "session_id": session_id},
        )
        return {"success": True, "url": url}
    except Exception as exc:  # noqa: BLE001
        print(f"Full video upload error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to upload full video") from exc


@router.post("/upload-transcript", status_code=status.HTTP_201_CREATED)
async def upload_transcript(session_id: str = Form(...), file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        file_bytes = await file.read()
        url = await upload_interview_media(file_bytes, session_id, "TRANSCRIPT", media_type="pdf")
        try:
            execute(
                "UPDATE interview_sessions SET transcript_url = :url WHERE id = :session_id",
                {"url": url, "session_id": session_id},
            )
        except Exception:
            pass
        return {"success": True, "url": url}
    except Exception as exc:  # noqa: BLE001
        print(f"Transcript upload error: {exc}")
        return {"success": False, "error": str(exc)}
