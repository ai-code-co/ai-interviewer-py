from __future__ import annotations

import json
import os
from typing import Any, Dict

import PyPDF2
from openai import OpenAI

from ..config import get_settings
from ..db import execute, to_json_db
from .interview_service import fetch_interview_transcript, get_job_description_by_sessionid


def save_evaluation_to_db(session_id: str, grading_result: dict) -> bool:
    try:
        execute(
            """
            INSERT INTO ai_interview_evaluations (
                id, session_id, score, recommendation, summary,
                matched_skills, missing_skills, strengths, areas_for_improvement, created_at
            )
            VALUES (
                UUID(), :session_id, :score, :recommendation, :summary,
                :matched_skills, :missing_skills, :strengths, :areas_for_improvement, NOW()
            )
            ON DUPLICATE KEY UPDATE
                score = VALUES(score),
                recommendation = VALUES(recommendation),
                summary = VALUES(summary),
                matched_skills = VALUES(matched_skills),
                missing_skills = VALUES(missing_skills),
                strengths = VALUES(strengths),
                areas_for_improvement = VALUES(areas_for_improvement)
            """,
            {
                "session_id": session_id,
                "score": grading_result.get("score"),
                "recommendation": grading_result.get("recommendation"),
                "summary": grading_result.get("summary"),
                "matched_skills": to_json_db(grading_result.get("matched_skills", [])),
                "missing_skills": to_json_db(grading_result.get("missing_skills", [])),
                "strengths": to_json_db(grading_result.get("strengths", [])),
                "areas_for_improvement": to_json_db(grading_result.get("areas_for_improvement", [])),
            },
        )
        print(f"Successfully saved evaluation for session {session_id}")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"Error saving evaluation to DB: {exc}")
        return False


def read_transcript_from_pdf(pdf_path: str) -> str:
    try:
        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except Exception as exc:  # noqa: BLE001
        print(f"Error reading PDF: {exc}")
        return ""


def parse_transcript_text(text: str) -> list:
    print(f"DEBUG: Starting parse. Text length: {len(text)}")
    transcript_data = []

    lines = text.split("\n")
    current_item = None
    current_speaker = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("AI Interviewer:"):
            if current_item and "question" in current_item:
                transcript_data.append(current_item)

            content = line.replace("AI Interviewer:", "").strip()
            current_item = {"question": content, "answer": "", "keywords": ""}
            current_speaker = "interviewer"
        elif line.startswith("Candidate:"):
            if current_item:
                content = line.replace("Candidate:", "").strip()
                current_item["answer"] = content
                current_speaker = "candidate"
        else:
            if current_item:
                if current_speaker == "interviewer":
                    current_item["question"] += " " + line
                elif current_speaker == "candidate":
                    current_item["answer"] += " " + line

    if current_item and current_item.get("question"):
        transcript_data.append(current_item)

    print(f"DEBUG: Parsing complete. Found {len(transcript_data)} items.")
    return transcript_data


async def grade_interview_session(session_id: str, pdf_path: str = None) -> Dict[str, Any]:
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    job_context = get_job_description_by_sessionid(session_id)
    if not job_context:
        print("Warning: Job description not found, AI grading might be less accurate.")
        job_context = "General Software Engineering Role"

    transcript_data = []
    if pdf_path and os.path.exists(pdf_path):
        pdf_text = read_transcript_from_pdf(pdf_path)
        transcript_data = parse_transcript_text(pdf_text)
    else:
        transcript_data = fetch_interview_transcript(session_id) or []

    system_prompt = (
        "You are an expert technical interviewer and hiring manager. "
        "Analyze the provided interview transcript to evaluate the candidate. "
        "You must output a valid JSON object matching the exact structure below.\n\n"
        "Output Structure:\n"
        "{\n"
        '  "score": (integer 0-100),\n'
        '  "recommendation": "STRONG_MATCH" | "POTENTIAL_MATCH" | "WEAK_MATCH",\n'
        '  "summary": "A professional paragraph summarizing the candidate\'s fit (approx 3-4 sentences).",\n'
        '  "matched_skills": [\n'
        '       { "skill": "Skill Name", "reason": "Evidence from transcript" }\n'
        "   ],\n"
        '  "missing_skills": [\n'
        '       { "skill": "Skill Name", "reason": "Why it is considered missing or weak" }\n'
        "   ],\n"
        '  "strengths": [\n'
        '       { "header": "Short Title", "detail": "Detailed explanation" }\n'
        "   ],\n"
        '  "areas_for_improvement": [\n'
        '       { "header": "Short Title", "detail": "Detailed explanation" }\n'
        "   ]\n"
        "}\n\n"
        "Guidelines:\n"
        "1. Score: < 60 is No Match, 60-80 is Potential Match, > 80 is Strong Match.\n"
        "2. Matched Skills: Identify technical skills (e.g., React, Node.js) the candidate demonstrated proficiency in based on their answers.\n"
        "3. Missing Skills: Identify skills asked about in the questions where the candidate struggled, or standard skills implied by the role that were not mentioned.\n"
        "4. Strengths: Focus on broad attributes (e.g., 'Project Experience', 'Communication', 'Technical Depth').\n"
        "5. Areas for Improvement: Focus on red flags or weak spots (e.g., 'Limited Professional Experience', 'Theoretical Knowledge only')."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"JOB CONTEXT:\n{job_context}\n\nINTERVIEW TRANSCRIPT:\n{transcript_data}",
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except Exception as exc:  # noqa: BLE001
        print(f"Error parsing AI response: {exc}")
        return {"error": "Failed to parse AI grading", "raw_response": content}
