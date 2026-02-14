from __future__ import annotations

import asyncio
import os

import nest_asyncio
import requests

from ..db import fetch_one
from ..services.ai_evaluation_service import (
    evaluate_candidate,
    get_job_details,
    mark_evaluation_failed,
    save_evaluation,
)
from ..services.resume_parser_service import extract_resume_text
from ..services.storage_service import get_signed_download_url


nest_asyncio.apply()

UPLOAD_DIR = os.path.join(os.getcwd(), "local_uploads")


def _fetch_job_id_from_candidate(candidate_id: str) -> str:
    print("[Worker Warning] job_id missing in arguments. Fetching from DB...")
    row = fetch_one("SELECT job_id FROM candidates WHERE id = :id LIMIT 1", {"id": candidate_id})
    if row and row.get("job_id"):
        return str(row["job_id"])
    raise RuntimeError(f"Could not find job_id for candidate {candidate_id}")


def _load_resume_bytes(
    resume_path: str,
    resume_public_id: str | None = None,
    resume_resource_type: str = "raw",
) -> bytes:
    if resume_path.startswith("http://") or resume_path.startswith("https://"):
        response = requests.get(resume_path, timeout=30)
        if response.status_code == 401:
            signed_url = get_signed_download_url(
                resume_path=resume_path,
                public_id=resume_public_id,
                resource_type=resume_resource_type,
            )
            if signed_url:
                signed_resp = requests.get(signed_url, timeout=30)
                signed_resp.raise_for_status()
                return signed_resp.content
        response.raise_for_status()
        return response.content

    local_file_path = os.path.join(UPLOAD_DIR, resume_path)
    if not os.path.exists(local_file_path):
        raise RuntimeError(f"File not found on local disk: {local_file_path}")
    with open(local_file_path, "rb") as file:
        return file.read()


def process_evaluation_job(
    candidate_id: str,
    resume_path: str,
    storage_bucket: str,
    job_id: str = None,
    resume_public_id: str | None = None,
    resume_resource_type: str = "raw",
    resume_text: str | None = None,
) -> dict:
    _ = storage_bucket

    if not job_id:
        job_id = _fetch_job_id_from_candidate(candidate_id)

    try:
        final_resume_text = (resume_text or "").strip()
        if not final_resume_text:
            file_bytes = _load_resume_bytes(
                resume_path,
                resume_public_id=resume_public_id,
                resume_resource_type=resume_resource_type,
            )
            if not file_bytes:
                raise RuntimeError("Empty file.")

            filename = resume_path.split("/")[-1]
            parsed = extract_resume_text(file_bytes, filename)
            final_resume_text = parsed.text

        if not final_resume_text or len(final_resume_text.strip()) < 50:
            raise RuntimeError("Resume text too short.")

        job_details = _run_sync(get_job_details(job_id))
        evaluation = _run_sync(evaluate_candidate(final_resume_text, job_details))
        _run_sync(save_evaluation(candidate_id, evaluation))
        return {"success": True, "score": evaluation["score"]}

    except Exception as exc:  # noqa: BLE001
        try:
            _run_sync(mark_evaluation_failed(candidate_id, str(exc)))
        except Exception:
            pass
        raise exc


def _run_sync(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        nest_asyncio.apply()
        return loop.run_until_complete(coro)
    return loop.run_until_complete(coro)
