from __future__ import annotations
import base64
from ..config import get_settings
from openai import Client

def generate_question_audio(text: str) -> str:
    """
    Generates audio from text using OpenAI TTS.
    Returns base64 encoded audio string to play immediately on frontend.
    """
    settings = get_settings()
    client = Client(api_key=settings.openai_api_key)

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy", 
            input=text,
            response_format="mp3"
        )
        # Convert binary audio to base64 for easy JSON transport
        audio_b64 = base64.b64encode(response.content).decode('utf-8')
        return f"data:audio/mp3;base64,{audio_b64}"
    except Exception as e:
        print(f"TTS Generation Error: {e}")
        return None