from __future__ import annotations
import os
from ..config import get_settings
from openai import OpenAI

def transcribe_audio_chunk(file_bytes: bytes) -> str:
    """
    Uses OpenAI Whisper (API) to transcribe audio with high accuracy.
    Handles accents, fillers, and background noise.
    """
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    
    # Save to temp file because OpenAI API needs a file path/object with name
    temp_filename = f"temp_chunk_{os.urandom(4).hex()}.webm"
    
    try:
        with open(temp_filename, "wb") as f:
            f.write(file_bytes)
            
        with open(temp_filename, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                language="en", # Force English for consistency
                prompt="This is a technical job interview answer." # Context helps accuracy
            )
            
        return transcript.text
    
    except Exception as e:
        print(f"Whisper Error: {e}")
        return "" # Return empty string on failure
    
    finally:
        # Cleanup temp file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)