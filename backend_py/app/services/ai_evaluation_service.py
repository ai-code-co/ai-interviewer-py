from __future__ import annotations

from typing import Any, Dict, List, Literal, TypedDict, Union

from openai import OpenAI

from ..config import get_settings
from ..db import execute, fetch_one, from_json_db, to_json_db


Recommendation = Literal["STRONG_MATCH", "POTENTIAL_MATCH", "WEAK_MATCH"]


class AIEvaluationResult(TypedDict):
    score: int
    recommendation: Recommendation
    matched_skills: Union[Dict[str, str], List[str]]
    missing_skills: Union[Dict[str, str], List[str]]
    strengths: Union[Dict[str, str], List[str]]
    weaknesses: Union[Dict[str, str], List[str]]
    summary: str


class JobDetails(TypedDict):
    id: str
    title: str
    description: str | None


def _get_openai_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(api_key=settings.openai_api_key)


async def get_job_details(job_id: str) -> JobDetails:
    row = fetch_one(
        """
        SELECT id, title, description
        FROM jobs
        WHERE id = :job_id
        LIMIT 1
        """,
        {"job_id": job_id},
    )
    if not row:
        raise RuntimeError("Failed to fetch job details: Job not found")
    return JobDetails(id=str(row["id"]), title=row["title"], description=row.get("description"))


def _normalize_field(field: Any) -> Union[Dict[str, str], List[str]]:
    if not field:
        return {}
    if isinstance(field, dict):
        normalized: Dict[str, str] = {}
        for key, value in field.items():
            if key and value:
                normalized[str(key).strip()] = str(value).strip()
        return normalized
    if isinstance(field, list):
        if field and isinstance(field[0], dict):
            normalized = {}
            for item in field:
                if isinstance(item, dict):
                    for key, value in item.items():
                        if key and value:
                            normalized[str(key).strip()] = str(value).strip()
            return normalized
        return [str(s).strip() for s in field if str(s).strip()]
    return {}


async def evaluate_candidate(resume_text: str, job_details: JobDetails) -> AIEvaluationResult:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    system_prompt = (
        "You are an AI recruitment assistant.\n"
        "Evaluate candidates objectively based only on provided resume and job description.\n"
        "Do not speculate or invent skills that are not explicitly mentioned.\n"
        "Respond ONLY in valid JSON format.\n"
        "Never recommend hiring or rejecting - only provide objective evaluation."
    )

    user_prompt = f"""JOB DESCRIPTION:

Title: {job_details['title']}
{f"Description: {job_details['description']}" if job_details.get('description') else "No description provided."}

CANDIDATE RESUME:

{resume_text}

TASK:

Evaluate how suitable this candidate is for the job based ONLY on the information provided.

Return a JSON object with the following structure:
{{
  "score": <number between 0-100>,
  "recommendation": "<STRONG_MATCH | POTENTIAL_MATCH | WEAK_MATCH>",
  "matched_skills": {{"skill": "description", ...}},
  "missing_skills": {{"skill": "description", ...}},
  "strengths": {{"strength": "description", ...}},
  "weaknesses": {{"weakness": "description", ...}},
  "summary": "<short paragraph summarizing the evaluation>"
}}

IMPORTANT:
- Only include skills explicitly mentioned in the resume or job description
- Do not invent or assume skills
- Be objective and fair
- Recommendation should be based on score: 80-100 = STRONG_MATCH, 50-79 = POTENTIAL_MATCH, 0-49 = WEAK_MATCH
"""
    client = _get_openai_client()
    completion = client.chat.completions.create(
        model=settings.openai_model or "gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=2000,
    )
    content = completion.choices[0].message.content
    if not content:
        raise RuntimeError("OpenAI returned empty response")

    try:
        import json

        parsed = json.loads(content)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("AI returned invalid JSON format") from exc

    raw_score = parsed.get("score")
    score = int(raw_score) if isinstance(raw_score, (int, float, str)) and str(raw_score).isdigit() else None
    if score is None or score < 0 or score > 100:
        raise RuntimeError("Invalid score: must be between 0 and 100")
    score = max(0, min(100, round(score)))

    valid_recommendations: list[str] = ["STRONG_MATCH", "POTENTIAL_MATCH", "WEAK_MATCH"]
    recommendation: str = parsed.get("recommendation") or ""
    if recommendation not in valid_recommendations:
        if score >= 80:
            recommendation = "STRONG_MATCH"
        elif score >= 50:
            recommendation = "POTENTIAL_MATCH"
        else:
            recommendation = "WEAK_MATCH"

    matched_skills = _normalize_field(parsed.get("matched_skills"))
    missing_skills = _normalize_field(parsed.get("missing_skills"))
    strengths = _normalize_field(parsed.get("strengths"))
    weaknesses = _normalize_field(parsed.get("weaknesses"))

    summary_raw = parsed.get("summary")
    summary = summary_raw.strip() if isinstance(summary_raw, str) and summary_raw.strip() else "Evaluation completed."

    return AIEvaluationResult(
        score=score,
        recommendation=recommendation,  # type: ignore[assignment]
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        strengths=strengths,
        weaknesses=weaknesses,
        summary=summary,
    )


async def save_evaluation(candidate_id: str, result: AIEvaluationResult) -> None:
    execute(
        """
        INSERT INTO ai_evaluations (
            id, candidate_id, score, recommendation, matched_skills, missing_skills,
            strengths, weaknesses, summary, status, created_at, updated_at
        )
        VALUES (
            UUID(), :candidate_id, :score, :recommendation, :matched_skills, :missing_skills,
            :strengths, :weaknesses, :summary, 'COMPLETED', NOW(), NOW()
        )
        ON DUPLICATE KEY UPDATE
            score = VALUES(score),
            recommendation = VALUES(recommendation),
            matched_skills = VALUES(matched_skills),
            missing_skills = VALUES(missing_skills),
            strengths = VALUES(strengths),
            weaknesses = VALUES(weaknesses),
            summary = VALUES(summary),
            status = 'COMPLETED',
            error_message = NULL,
            updated_at = NOW()
        """,
        {
            "candidate_id": candidate_id,
            "score": result["score"],
            "recommendation": result["recommendation"],
            "matched_skills": to_json_db(result["matched_skills"]),
            "missing_skills": to_json_db(result["missing_skills"]),
            "strengths": to_json_db(result["strengths"]),
            "weaknesses": to_json_db(result["weaknesses"]),
            "summary": result["summary"],
        },
    )


async def mark_evaluation_failed(candidate_id: str, error_message: str) -> None:
    try:
        execute(
            """
            INSERT INTO ai_evaluations (
                id, candidate_id, score, recommendation, matched_skills, missing_skills,
                strengths, weaknesses, summary, status, error_message, created_at, updated_at
            )
            VALUES (
                UUID(), :candidate_id, 0, 'POTENTIAL_MATCH', :matched_skills, :missing_skills,
                :strengths, :weaknesses, 'Evaluation failed', 'FAILED', :error_message, NOW(), NOW()
            )
            ON DUPLICATE KEY UPDATE
                status = 'FAILED',
                error_message = VALUES(error_message),
                matched_skills = VALUES(matched_skills),
                missing_skills = VALUES(missing_skills),
                strengths = VALUES(strengths),
                weaknesses = VALUES(weaknesses),
                summary = VALUES(summary),
                updated_at = NOW()
            """,
            {
                "candidate_id": candidate_id,
                "error_message": (error_message or "")[:1000],
                "matched_skills": to_json_db([]),
                "missing_skills": to_json_db([]),
                "strengths": to_json_db([]),
                "weaknesses": to_json_db([]),
            },
        )
    except Exception as exc:  # noqa: BLE001
        print("Failed to mark evaluation as failed:", exc)


async def create_pending_evaluation(candidate_id: str) -> None:
    try:
        execute(
            """
            INSERT INTO ai_evaluations (
                id, candidate_id, score, recommendation, matched_skills, missing_skills,
                strengths, weaknesses, summary, status, created_at, updated_at
            )
            VALUES (
                UUID(), :candidate_id, 0, 'POTENTIAL_MATCH', :matched_skills, :missing_skills,
                :strengths, :weaknesses, 'Evaluation queued...', 'PENDING', NOW(), NOW()
            )
            ON DUPLICATE KEY UPDATE
                status = 'PENDING',
                summary = 'Evaluation queued...',
                updated_at = NOW()
            """,
            {
                "candidate_id": candidate_id,
                "matched_skills": to_json_db([]),
                "missing_skills": to_json_db([]),
                "strengths": to_json_db([]),
                "weaknesses": to_json_db([]),
            },
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Exception creating pending evaluation row: {exc}")


def normalize_ai_evaluation_row(row: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not row:
        return None
    row["matched_skills"] = from_json_db(row.get("matched_skills"), [])
    row["missing_skills"] = from_json_db(row.get("missing_skills"), [])
    row["strengths"] = from_json_db(row.get("strengths"), [])
    row["weaknesses"] = from_json_db(row.get("weaknesses"), [])
    return row
