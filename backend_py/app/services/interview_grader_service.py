from .interview_service import fetch_interview_transcript,get_job_description_by_sessionid
from ..config import get_settings, get_supabase_client 
from openai import OpenAI
import json
from typing import Dict, Any
import PyPDF2
import os



def save_evaluation_to_db(session_id: str, grading_result: dict):
    """
    Save the AI grading result to Supabase.
    """
    supabase = get_supabase_client()
    try:
        data_to_insert = {
            "session_id": session_id,
            "score": grading_result.get("score"),
            "recommendation": grading_result.get("recommendation"),
            "summary": grading_result.get("summary"),
            "matched_skills": grading_result.get("matched_skills"),
            "missing_skills": grading_result.get("missing_skills"),
            "strengths": grading_result.get("strengths"),
            "areas_for_improvement": grading_result.get("areas_for_improvement")
        }

        
        supabase.table("ai_interview_evaluations").upsert(
            data_to_insert, on_conflict="session_id"
        ).execute()
        
        print(f"Successfully saved evaluation for session {session_id}")
        return True
    except Exception as e:
        print(f"Error saving evaluation to DB: {e}")
        return False   

def read_transcript_from_pdf(pdf_path: str) -> str:
    """
    Read text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text from the PDF
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""


def parse_transcript_text(text: str) -> list:
    """
    Parse the transcript text based on 'AI Interviewer:' and 'Candidate:' labels.
    """
    print(f"DEBUG: Starting parse. Text length: {len(text)}")
    transcript_data = []
    
    lines = text.split('\n')
    current_item = None
    current_speaker = None

    for line in lines:
        line = line.strip()
        if not line: continue  # Skip empty lines

        # Check if the line starts with the Interviewer label
        if line.startswith('AI Interviewer:'):
            # If we already have a previous pair, save it
            if current_item and 'question' in current_item:
                transcript_data.append(current_item)
            
            # Start a new question object
            content = line.replace('AI Interviewer:', '').strip()
            current_item = {'question': content, 'answer': '', 'keywords': ''}
            current_speaker = 'interviewer'
            
        # Check if the line starts with the Candidate label
        elif line.startswith('Candidate:'):
            if current_item:
                content = line.replace('Candidate:', '').strip()
                current_item['answer'] = content
                current_speaker = 'candidate'
        
        # Handle multi-line text (text that doesn't start with a label)
        else:
            if current_item:
                if current_speaker == 'interviewer':
                    current_item['question'] += " " + line
                elif current_speaker == 'candidate':
                    current_item['answer'] += " " + line

    # Append the last item
    if current_item and current_item.get('question'):
        transcript_data.append(current_item)
    
    print(f"DEBUG: Parsing complete. Found {len(transcript_data)} items.")
    return transcript_data

async def grade_interview_session(session_id:str,pdf_path: str = None) -> Dict[str,Any]:
    
    """
    Grade an interview session based on transcript data.
    
    Args:
        session_id: ID of the interview session
        pdf_path: Optional path to PDF transcript file
        
    Returns:
        Dictionary containing grading results
    """
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    
    
    job_context = get_job_description_by_sessionid(session_id)
    if not job_context:
        print("Warning: Job description not found, AI grading might be less accurate.")
        job_context = "General Software Engineering Role"
    
    # Read transcript from PDF if path is provided
    if pdf_path and os.path.exists(pdf_path):
        pdf_text = read_transcript_from_pdf(pdf_path)
        transcript_data = parse_transcript_text(pdf_text)
        print("85 transdata",transcript_data)
    else:
        print("87 error")

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
        '   ],\n'
        '  "missing_skills": [\n'
        '       { "skill": "Skill Name", "reason": "Why it is considered missing or weak" }\n'
        '   ],\n'
        '  "strengths": [\n'
        '       { "header": "Short Title", "detail": "Detailed explanation" }\n'
        '   ],\n'
        '  "areas_for_improvement": [\n'
        '       { "header": "Short Title", "detail": "Detailed explanation" }\n'
        '   ]\n'
        "}\n\n"
        
        "Guidelines:\n"
        "1. Score: < 60 is No Match, 60-80 is Potential Match, > 80 is Strong Match.\n"
        "2. Matched Skills: Identify technical skills (e.g., React, Node.js) the candidate demonstrated proficiency in based on their answers.\n"
        "3. Missing Skills: Identify skills asked about in the questions where the candidate struggled, or standard skills implied by the role that were not mentioned.\n"
        "4. Strengths: Focus on broad attributes (e.g., 'Project Experience', 'Communication', 'Technical Depth').\n"
        "5. Areas for Improvement: Focus on red flags or weak spots (e.g., 'Limited Professional Experience', 'Theoretical Knowledge only')."
    )

    # call OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": (
                    f"JOB CONTEXT:\n{job_context}\n\n"
                    f"INTERVIEW TRANSCRIPT:\n{transcript_data}"
                )}
        ],
        response_format={"type": "json_object"},
        temperature=0.2
    )

    try:
        content = response.choices[0].message.content
        result = json.loads(content)
        return result
    except Exception as e:
        print(f"Error parsing AI response: {e}")
        return {"error": "Failed to parse AI grading", "raw_response": content}
    