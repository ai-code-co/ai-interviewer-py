## backend_py/app/services/storage_service.py
from __future__ import annotations
import os
from hashlib import sha256
from uuid import uuid4
import requests
from ..config import get_settings

# Local Upload Directory (For Videos)
UPLOAD_DIR = os.path.join(os.getcwd(), "local_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- HELPER: Upload to Supabase (Cloud) ---
async def _upload_to_supabase(bucket: str, path: str, file_bytes: bytes, content_type: str) -> str:
    settings = get_settings()
    url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{path}"
    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
        "Content-Type": content_type,
        "x-upsert": "true",
    }
    resp = requests.put(url, headers=headers, data=file_bytes, timeout=60)
    if resp.status_code >= 400:
        raise RuntimeError(f"Supabase Upload Failed: {resp.status_code} {resp.text}")
    
    return f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public/{bucket}/{path}"

# --- HELPER: Save to Local Disk (Server) ---
def _save_to_local(filename: str, file_bytes: bytes) -> str:
    settings = get_settings()
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    print(f"✅ Saved locally: {file_path}")
    return f"{settings.app_url}/uploads/{filename}"


# ---------------------------------------------------------
# 1. RESUME UPLOAD (Cloud)
# ---------------------------------------------------------
async def upload_resume(file_bytes: bytes, file_name: str, file_type: str, candidate_id: str) -> dict:
    try:
        file_hash = sha256(file_bytes).hexdigest()
        sanitized_name = "".join(ch if ch.isalnum() or ch in (".", "-") else "_" for ch in file_name)
        from time import time
        path = f"{candidate_id}/{int(time()*1000)}-{sanitized_name}"

        await _upload_to_supabase("resumes", path, file_bytes, file_type)
        return {"path": path, "hash": file_hash}
    except Exception as e:
        raise RuntimeError(f"Failed to upload resume: {e}")


# ---------------------------------------------------------
# 2. INTERVIEW MEDIA (Hybrid: Video=Local, PDF=Cloud)
# ---------------------------------------------------------
async def upload_interview_media(file_bytes: bytes, session_id: str, question_id: str = "full_session", media_type: str = "video") -> str:
    filename_base = f"{session_id}_{question_id}_{uuid4()}"

    try:
        if media_type == "video":
            # HEAVY FILE -> LOCAL DISK
            filename = f"{filename_base}.webm"
            return _save_to_local(filename, file_bytes)
            
        elif media_type == "pdf":
            # LIGHT FILE -> SUPABASE CLOUD (Safe storage)
            path = f"{session_id}/{question_id}.pdf"
            return await _upload_to_supabase("interview-transcripts", path, file_bytes, "application/pdf")
            
        elif media_type == "audio":
            # WHISPER CHUNK -> SUPABASE CLOUD (Better access for workers)
            path = f"{session_id}/{filename_base}.webm"
            return await _upload_to_supabase("interview-audio", path, file_bytes, "audio/webm")
            
        else:
            return _save_to_local(f"{filename_base}.dat", file_bytes)

    except Exception as e:
        raise RuntimeError(f"Failed to save {media_type}: {e}")

# Alias
upload_audio = upload_interview_media

# ---------------------------------------------------------
# 3. GET RESUME URL (Cloud)
# ---------------------------------------------------------
async def get_resume_url(storage_path: str, bucket: str) -> str:
    settings = get_settings()
    return f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public/{bucket}/{storage_path}"