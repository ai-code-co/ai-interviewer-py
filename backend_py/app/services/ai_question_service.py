from __future__ import annotations

import json
from uuid import uuid4

from openai import OpenAI

from ..config import get_settings
from ..db import execute


def generate_interview_questions(job_id: str, job_title: str, job_description: str) -> bool:
    """
    Generates 3-5 interview questions based on the job description
    and saves them to the interview_questions table.
    """
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    prompt = f"""
    You are an expert technical recruiter. Generate 4 interview questions for the role of "{job_title}".

    Job Description:
    {job_description}

    Requirements:
    1. The first question must be an introduction (e.g., "Tell us about yourself").
    2. The next 3 questions should be specific to the skills in the description.
    3. Keep questions concise (under 30 words) so they are easy to listen to via TTS.
    4. Return ONLY a raw JSON array of strings. Example: ["Question 1", "Question 2"]
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        content = (response.choices[0].message.content or "").strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "")

        questions = json.loads(content)
        if not isinstance(questions, list):
            return False

        for idx, q_text in enumerate(questions):
            if not str(q_text).strip():
                continue
            execute(
                """
                INSERT INTO interview_questions (id, job_id, question_text, question_order)
                VALUES (:id, :job_id, :question_text, :question_order)
                """,
                {
                    "id": str(uuid4()),
                    "job_id": job_id,
                    "question_text": str(q_text).strip(),
                    "question_order": idx + 1,
                },
            )
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"Error generating questions: {exc}")
        return False
