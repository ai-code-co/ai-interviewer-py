from __future__ import annotations
import os
from hashlib import sha256
from uuid import uuid4
from ..config import get_settings

# Ensure upload directory exists
UPLOAD_DIR = os.path.join(os.getcwd(), "local_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------------
# 1. VIDEO / AUDIO UPLOAD (For Interview)
# ---------------------------------------------------------
async def upload_interview_media(file_bytes: bytes, session_id: str, question_id: str = "full_session", media_type: str = "video") -> str:
    settings = get_settings()
    
    # UPDATE: Handle PDF extension
    if media_type == "pdf":
        ext = "pdf"
    elif media_type == "video":
        ext = "webm"
    else:
        ext = "webm"
    
    filename = f"{session_id}_{question_id}_{uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        
        print(f"✅ Saved {media_type} locally: {file_path}")
        return f"{settings.app_url}/uploads/{filename}"

    except Exception as e:
        raise RuntimeError(f"Failed to save local media: {e}")
# ---------------------------------------------------------
# 2. RESUME UPLOAD (For Apply Form)
# ---------------------------------------------------------
async def upload_resume(file_bytes: bytes, file_name: str, file_type: str, candidate_id: str) -> dict:
    """
    Saves the resume LOCALLY to 'local_uploads'.
    Matches the signature expected by apply.py
    """
    try:
        # Generate hash
        file_hash = sha256(file_bytes).hexdigest()
        
        # Generate safe filename
        sanitized_name = "".join(ch if ch.isalnum() or ch in (".", "-") else "_" for ch in file_name)
        final_name = f"resume_{candidate_id}_{uuid4()}_{sanitized_name}"
        file_path = os.path.join(UPLOAD_DIR, final_name)

        # Write file
        with open(file_path, "wb") as f:
            f.write(file_bytes)
            
        print(f"✅ Saved resume locally: {file_path}")

        # Return dict expected by apply.py (Step 4)
        return {
            "path": final_name,  # We store just the filename as the path
            "hash": file_hash
        }
    except Exception as e:
        raise RuntimeError(f"Failed to save local resume: {e}")


# ---------------------------------------------------------
# 3. GET URL HELPER
# ---------------------------------------------------------
async def get_resume_url(storage_path: str, bucket: str) -> str:
    """
    Returns the localhost URL for the file.
    Ignores 'bucket' since we are using one local folder.
    """
    settings = get_settings()
    return f"{settings.app_url}/uploads/{storage_path}"