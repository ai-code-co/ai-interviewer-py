## backend_py/app/services/ai_evaluation_service.py
from __future__ import annotations

from typing import Any, Dict, List, Literal, TypedDict, Union

from openai import OpenAI

from ..config import get_settings, get_supabase_client


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
    supabase = get_supabase_client()
    res = supabase.table("jobs").select("id, title, description").eq("id", job_id).single().execute()
    err = getattr(res, "error", None)
    if err or not res.data or (getattr(res, "status_code", 200) >= 400):
        message = err.message if err and hasattr(err, "message") else "Job not found"
        raise RuntimeError(f"Failed to fetch job details: {message}")
    data = res.data
    return JobDetails(id=str(data["id"]), title=data["title"], description=data.get("description"))


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

    # Validate / normalize
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
    supabase = get_supabase_client()
    payload = {
        "candidate_id": candidate_id,
        "score": result["score"],
        "recommendation": result["recommendation"],
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
        "strengths": result["strengths"],
        "weaknesses": result["weaknesses"],
        "summary": result["summary"],
        "status": "COMPLETED",
    }
    res = (
        supabase.table("ai_evaluations")
        .upsert(payload, on_conflict="candidate_id")
        .execute()
    )
    err = getattr(res, "error", None)
    if err or (getattr(res, "status_code", 200) >= 400):
        msg = err.message if err and hasattr(err, "message") else "Unknown error"
        raise RuntimeError(f"Failed to save evaluation: {msg}")


async def mark_evaluation_failed(candidate_id: str, error_message: str) -> None:
    supabase = get_supabase_client()
    payload = {
        "candidate_id": candidate_id,
        "status": "FAILED",
        "error_message": (error_message or "")[:1000],
        "matched_skills": [],
        "missing_skills": [],
        "strengths": [],
        "weaknesses": [],
        "summary": "Evaluation failed",
    }
    res = (
        supabase.table("ai_evaluations")
        .upsert(payload, on_conflict="candidate_id")
        .execute()
    )
    err = getattr(res, "error", None)
    if err or (getattr(res, "status_code", 200) >= 400):
        # Log-like behavior only; don't raise to avoid loops
        msg = err.message if err and hasattr(err, "message") else "Unknown error"
        print("Failed to mark evaluation as failed:", msg)


async def create_pending_evaluation(candidate_id: str) -> None:
    """
    Create or update an ai_evaluations row in PENDING state so the frontend
    can immediately show that an evaluation is queued.
    """
    supabase = get_supabase_client()
    payload = {
        "candidate_id": candidate_id,
        "status": "PENDING",
        "summary": "Evaluation queued...",
        "matched_skills": [],
        "missing_skills": [],
        "strengths": [],
        "weaknesses": [],
        # FIX: Add these placeholder values to satisfy Database Constraints
        "score": 0, 
        "recommendation": "POTENTIAL_MATCH" 
    }
    try:
        res = (
            supabase.table("ai_evaluations")
            .upsert(payload, on_conflict="candidate_id")
            .execute()
        )
        err = getattr(res, "error", None)
        if err:
            err_msg = getattr(err, "message", str(err))
            print(f"Failed to create pending evaluation row: {err_msg}")
    except Exception as exc:  # noqa: BLE001
        print(f"Exception creating pending evaluation row: {exc}")
