## backend_py/app/services/ai_question_service.py
from __future__ import annotations
import json
from ..config import get_settings, get_supabase_client
from openai import OpenAI

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
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "")
        
        questions = json.loads(content)
        
        supabase = get_supabase_client()
        data_to_insert = []
        
        for idx, q_text in enumerate(questions):
            data_to_insert.append({
                "job_id": job_id,
                "question_text": q_text,
                "question_order": idx + 1
            })

        if data_to_insert:
            supabase.table("interview_questions").insert(data_to_insert).execute()
            return True
            
    except Exception as e:
        print(f"Error generating questions: {e}")
        return False
    
    return False