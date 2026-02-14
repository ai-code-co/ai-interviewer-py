from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
import os
import time
from urllib.parse import urlparse
from uuid import uuid4

import cloudinary
import cloudinary.uploader
import cloudinary.utils

from ..config import get_settings


@lru_cache()
def _configure_cloudinary() -> None:
    settings = get_settings()
    if settings.cloudinary_url:
        cloudinary.config(cloudinary_url=settings.cloudinary_url, secure=True)
    else:
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )


async def upload_interview_media(
    file_bytes: bytes,
    session_id: str,
    question_id: str = "full_session",
    media_type: str = "video",
) -> str:
    _configure_cloudinary()

    if media_type == "pdf":
        resource_type = "raw"
    elif media_type == "video":
        resource_type = "video"
    else:
        resource_type = "raw"

    try:
        upload_result = cloudinary.uploader.upload(
            file_bytes,
            resource_type=resource_type,
            folder=f"ai-interviewer/interviews/{session_id}",
            public_id=f"{question_id}_{uuid4().hex}",
            overwrite=False,
        )
        return upload_result["secure_url"]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to upload media to Cloudinary: {exc}") from exc


async def upload_resume(file_bytes: bytes, file_name: str, file_type: str, candidate_id: str) -> dict:
    _ = file_type
    _configure_cloudinary()
    try:
        file_hash = sha256(file_bytes).hexdigest()
        ext = os.path.splitext(file_name or "")[1].lower()
        if ext not in {".pdf", ".doc", ".docx"}:
            ext = ".pdf"
        public_id = f"{uuid4().hex}{ext}"
        upload_result = cloudinary.uploader.upload(
            file_bytes,
            resource_type="raw",
            type="upload",
            access_mode="public",
            folder=f"ai-interviewer/resumes/{candidate_id}",
            public_id=public_id,
            overwrite=False,
        )
        return {
            "path": upload_result["secure_url"],
            "hash": file_hash,
            "public_id": upload_result["public_id"],
            "resource_type": "raw",
        }
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to upload resume to Cloudinary: {exc}") from exc


async def get_resume_url(storage_path: str, bucket: str) -> str:
    _ = bucket
    return storage_path


async def delete_media(public_id: str, resource_type: str = "raw") -> None:
    _configure_cloudinary()
    cloudinary.uploader.destroy(public_id, resource_type=resource_type, invalidate=True)


def get_signed_download_url(
    resume_path: str,
    public_id: str | None = None,
    resource_type: str = "raw",
    expires_in_seconds: int = 900,
) -> str | None:
    _configure_cloudinary()
    resolved_public_id = public_id or _extract_public_id_from_cloudinary_url(resume_path, resource_type)
    if not resolved_public_id:
        return None

    normalized_public_id, fmt = _split_public_id_and_format(resolved_public_id)
    if fmt:
        return cloudinary.utils.private_download_url(
            normalized_public_id,
            fmt,
            resource_type=resource_type,
            type="upload",
            expires_at=int(time.time()) + expires_in_seconds,
            attachment=False,
        )

    signed_url, _ = cloudinary.utils.cloudinary_url(
        normalized_public_id,
        resource_type=resource_type,
        type="upload",
        sign_url=True,
        secure=True,
    )
    return signed_url


def _extract_public_id_from_cloudinary_url(url: str, resource_type: str) -> str | None:
    try:
        parsed = urlparse(url)
        marker = f"/{resource_type}/upload/"
        if marker not in parsed.path:
            return None
        tail = parsed.path.split(marker, 1)[1]
        if tail.startswith("v"):
            parts = tail.split("/", 1)
            if len(parts) == 2 and parts[0][1:].isdigit():
                tail = parts[1]
        return tail.lstrip("/") or None
    except Exception:
        return None


def _split_public_id_and_format(public_id: str) -> tuple[str, str | None]:
    filename = public_id.rsplit("/", 1)[-1]
    if "." not in filename:
        return public_id, None
    base, ext = filename.rsplit(".", 1)
    if not ext:
        return public_id, None
    normalized = public_id[: -(len(ext) + 1)]
    return normalized, ext.lower()
