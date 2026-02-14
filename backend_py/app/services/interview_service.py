from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..db import execute, fetch_all, fetch_one, from_json_db
from .ai_question_service import generate_interview_questions


def _now_db() -> datetime:
    return datetime.utcnow()


def create_interview_session(candidate_id: str, job_id: str) -> Dict[str, Any]:
    try:
        q_check = fetch_one(
            "SELECT COUNT(*) AS total FROM interview_questions WHERE job_id = :job_id",
            {"job_id": job_id},
        )
        total = int(q_check["total"]) if q_check else 0
        if total == 0:
            job_res = fetch_one(
                "SELECT title, description FROM jobs WHERE id = :job_id LIMIT 1",
                {"job_id": job_id},
            )
            if job_res:
                print(f"Generating questions for Job {job_id}...")
                generate_interview_questions(job_id, job_res["title"], job_res.get("description") or "")
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: Question generation check failed: {exc}")

    try:
        existing = fetch_one(
            """
            SELECT *
            FROM interview_sessions
            WHERE candidate_id = :candidate_id AND job_id = :job_id
            ORDER BY created_at DESC
            LIMIT 1
            """,
            {"candidate_id": candidate_id, "job_id": job_id},
        )
        if existing:
            if not existing.get("access_token"):
                new_token = str(uuid4())
                execute(
                    "UPDATE interview_sessions SET access_token = :token WHERE id = :id",
                    {"token": new_token, "id": existing["id"]},
                )
                existing["access_token"] = new_token
            return existing
    except Exception as exc:  # noqa: BLE001
        print(f"Error checking session: {exc}")

    try:
        token = str(uuid4())
        session_id = str(uuid4())
        execute(
            """
            INSERT INTO interview_sessions (id, candidate_id, job_id, status, access_token, created_at)
            VALUES (:id, :candidate_id, :job_id, 'PENDING', :access_token, :created_at)
            """,
            {
                "id": session_id,
                "candidate_id": candidate_id,
                "job_id": job_id,
                "access_token": token,
                "created_at": _now_db(),
            },
        )
        row = fetch_one("SELECT * FROM interview_sessions WHERE id = :id LIMIT 1", {"id": session_id})
        if not row:
            raise RuntimeError("No data returned")
        return row
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to create session: {exc}") from exc


def get_session_by_token(token: str) -> Dict[str, Any] | None:
    try:
        return fetch_one(
            "SELECT * FROM interview_sessions WHERE access_token = :token LIMIT 1",
            {"token": token},
        )
    except Exception:
        return None


def get_next_question(job_id: str, last_question_id: Optional[str]) -> Optional[Dict[str, Any]]:
    try:
        if last_question_id:
            last_res = fetch_one(
                "SELECT question_order FROM interview_questions WHERE id = :id LIMIT 1",
                {"id": last_question_id},
            )
            if not last_res:
                return get_next_question(job_id, None)

            last_order = int(last_res["question_order"])
            rows = fetch_all(
                """
                SELECT *
                FROM interview_questions
                WHERE job_id = :job_id AND question_order > :last_order
                ORDER BY question_order ASC
                LIMIT 1
                """,
                {"job_id": job_id, "last_order": last_order},
            )
        else:
            rows = fetch_all(
                """
                SELECT *
                FROM interview_questions
                WHERE job_id = :job_id
                ORDER BY question_order ASC
                LIMIT 1
                """,
                {"job_id": job_id},
            )
        return rows[0] if rows else None
    except Exception as exc:  # noqa: BLE001
        print(f"Error getting question: {exc}")
        return None


def save_interview_response(
    session_id: str,
    question_id: str,
    answer_text: str,
    answer_audio_url: Optional[str],
    answer_video_url: Optional[str],
) -> Dict[str, Any]:
    try:
        response_id = str(uuid4())
        execute(
            """
            INSERT INTO interview_responses (
                id, session_id, question_id, answer_text, answer_audio_url, answer_video_url, created_at
            )
            VALUES (
                :id, :session_id, :question_id, :answer_text, :answer_audio_url, :answer_video_url, :created_at
            )
            """,
            {
                "id": response_id,
                "session_id": session_id,
                "question_id": question_id,
                "answer_text": answer_text,
                "answer_audio_url": answer_audio_url,
                "answer_video_url": answer_video_url,
                "created_at": _now_db(),
            },
        )
        execute(
            """
            UPDATE interview_sessions
            SET last_question_id = :question_id, status = 'IN_PROGRESS'
            WHERE id = :session_id
            """,
            {"question_id": question_id, "session_id": session_id},
        )
        saved = fetch_one("SELECT * FROM interview_responses WHERE id = :id LIMIT 1", {"id": response_id})
        return saved or {}
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to save response: {exc}") from exc


def fetch_interview_transcript(session_id: str) -> Optional[List[Dict[str, Any]]]:
    try:
        rows = fetch_all(
            """
            SELECT r.answer_text, q.question_text, q.expected_keywords
            FROM interview_responses r
            LEFT JOIN interview_questions q ON q.id = r.question_id
            WHERE r.session_id = :session_id
            ORDER BY r.created_at ASC
            """,
            {"session_id": session_id},
        )
        graded_input = []
        for row in rows:
            graded_input.append(
                {
                    "question": row.get("question_text", "Unknown Question"),
                    "keywords": from_json_db(row.get("expected_keywords"), []),
                    "answer": row.get("answer_text", "[No Answer]"),
                }
            )
        return graded_input
    except Exception as exc:  # noqa: BLE001
        print(f"Error fetching transcript for {session_id}: {exc}")
        return None


def complete_interview_session(session_id: str, duration_seconds: Optional[int]) -> None:
    payload: Dict[str, Any] = {"session_id": session_id, "completed_at": _now_db()}
    try:
        if duration_seconds is not None:
            execute(
                """
                UPDATE interview_sessions
                SET status = 'COMPLETED', completed_at = :completed_at, duration = :duration
                WHERE id = :session_id
                """,
                {
                    **payload,
                    "duration": f"{duration_seconds} seconds",
                },
            )
        else:
            execute(
                """
                UPDATE interview_sessions
                SET status = 'COMPLETED', completed_at = :completed_at
                WHERE id = :session_id
                """,
                payload,
            )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to complete session: {exc}") from exc


def get_job_description_by_sessionid(session_id: str) -> str:
    try:
        row = fetch_one(
            """
            SELECT j.title, j.description
            FROM interview_sessions s
            LEFT JOIN jobs j ON j.id = s.job_id
            WHERE s.id = :session_id
            LIMIT 1
            """,
            {"session_id": session_id},
        )
        if row:
            return f"Role: {row.get('title')}\n\nDescription: {row.get('description')}"
        return ""
    except Exception as exc:  # noqa: BLE001
        print(f"Error fetching job description for {session_id}: {exc}")
        return ""
