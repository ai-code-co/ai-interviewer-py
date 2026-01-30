## backend_py/app/workers/ai_evaluation_worker.py
from __future__ import annotations

import asyncio
import nest_asyncio
import os
from ..config import get_supabase_admin_client, get_supabase_client
from ..services.ai_evaluation_service import (
    evaluate_candidate,
    get_job_details,
    mark_evaluation_failed,
    save_evaluation,
)
from ..services.resume_parser_service import extract_resume_text

# Apply nest_asyncio
nest_asyncio.apply()

# Define Local Upload Directory (Must match storage_service.py)
UPLOAD_DIR = os.path.join(os.getcwd(), "local_uploads")

# --- HELPER: Fetch Job ID if missing ---
def _fetch_job_id_from_candidate(candidate_id: str) -> str:
    print(f"⚠️ [Worker Warning] job_id missing in arguments. Fetching from DB...")
    supabase = get_supabase_client()
    res = supabase.table("candidates").select("job_id").eq("id", candidate_id).single().execute()
    if res.data and res.data.get("job_id"):
        return res.data["job_id"]
    raise RuntimeError(f"Could not find job_id for candidate {candidate_id}")

# --- MAIN WORKER FUNCTION ---
def process_evaluation_job(candidate_id: str, resume_path: str, storage_bucket: str, job_id: str = None) -> dict:
    
    print(f"\n{'='*60}")
    print(f"🚀 [START] WORKER JOB STARTED")
    print(f"👤 Candidate ID: {candidate_id}")
    
    if not job_id:
        try:
            job_id = _fetch_job_id_from_candidate(candidate_id)
            print(f"🔧 [Worker Fix] Retrieved Job ID from DB: {job_id}")
        except Exception as e:
            print(f"❌ [Fatal] Could not retrieve Job ID: {e}")
            return {"success": False, "error": str(e)}
    else:
        print(f"💼 Job ID:       {job_id}")

    print(f"{'='*60}")

    try:
        # --- STEP 1: READ LOCAL RESUME ---
        print(f"\n📥 [STEP 1] Reading Local Resume...")
        # Construct full local path
        local_file_path = os.path.join(UPLOAD_DIR, resume_path)
        print(f"   Path: {local_file_path}")
        
        if not os.path.exists(local_file_path):
            raise RuntimeError(f"File not found on local disk: {local_file_path}")

        with open(local_file_path, "rb") as f:
            file_bytes = f.read()

        if not file_bytes: raise RuntimeError("Empty file.")
        print(f"✅ [STEP 1] Read Complete. Size: {len(file_bytes)} bytes")

        # --- STEP 2: PARSE TEXT ---
        print(f"\n📄 [STEP 2] Extracting Text...")
        filename = resume_path # The path is just the filename in our local setup
        parsed = extract_resume_text(file_bytes, filename)
        resume_text = parsed.text
        
        if not resume_text or len(resume_text.strip()) < 50:
            raise RuntimeError("Resume text too short.")
        print(f"✅ [STEP 2] Extraction Complete.")

        # --- STEP 3: FETCH JOB DETAILS ---
        print(f"\n💼 [STEP 3] Fetching Job Description...")
        job_details = _run_sync(get_job_details(job_id))
        print(f"✅ [STEP 3] Job Found: '{job_details.get('title')}'")

        # --- STEP 4: CALL OPENAI ---
        print(f"\n🤖 [STEP 4] Sending to OpenAI...")
        evaluation = _run_sync(evaluate_candidate(resume_text, job_details))
        print(f"✅ [STEP 4] AI Response Received! Score: {evaluation['score']}")

        # --- STEP 5: SAVE TO DB ---
        print(f"\n💾 [STEP 5] Saving Results...")
        _run_sync(save_evaluation(candidate_id, evaluation))
        print(f"✅ [STEP 5] Saved.")
        print(f"\n{'='*60}\n🎉 [SUCCESS] DONE\n{'='*60}\n")
        
        return {"success": True, "score": evaluation["score"]}

    except Exception as exc:
        print(f"\n❌ [JOB FAILED] {exc}\n")
        try:
            _run_sync(mark_evaluation_failed(candidate_id, str(exc)))
        except: pass
        raise exc

def _run_sync(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        return loop.run_until_complete(coro)
    return loop.run_until_complete(coro)